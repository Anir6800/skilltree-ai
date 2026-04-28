"""
SkillTree AI - Adaptive Learning Celery Tasks
Periodic and event-driven skill tree adaptation.
"""

import logging
from celery import shared_task
from django.utils import timezone
from skills.adaptive_engine import AdaptiveTreeEngine
from quests.models import QuestSubmission

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def adapt_tree_for_user(self, user_id: int) -> dict:
    """
    Trigger adaptive tree adjustment for a user.
    Called after quest submission completion and every 24h via Celery Beat.
    """
    try:
        engine = AdaptiveTreeEngine(user_id)
        changes = engine.adapt_tree_for_user()
        logger.info(f"Adapted tree for user {user_id}: {changes}")
        return changes
    except Exception as exc:
        logger.error(f"Failed to adapt tree for user {user_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def update_ability_score_on_submission(self, submission_id: int) -> float:
    """
    Update user's ability score after quest submission.
    Called from quest submission completion signal.
    """
    try:
        submission = QuestSubmission.objects.get(id=submission_id)
        engine = AdaptiveTreeEngine(submission.user.id)

        # Determine outcome: 1.0 for fast first-pass, 0.0 for fail, 0.5 for normal pass
        if submission.status == 'passed':
            # Check if first attempt and fast
            earlier_attempts = QuestSubmission.objects.filter(
                user=submission.user,
                quest=submission.quest,
                created_at__lt=submission.created_at
            ).count()

            if earlier_attempts == 0:
                # First attempt - check speed
                execution_time = submission.execution_result.get('time_ms', 0)
                if execution_time < 5000:  # Less than 5 seconds
                    outcome = 1.0
                else:
                    outcome = 0.75
            else:
                outcome = 0.5
        else:
            outcome = 0.0

        new_score = engine.update_ability_score(outcome)
        engine.update_preferred_difficulty()

        logger.info(f"Updated ability score for user {submission.user.id}: outcome={outcome}, new_score={new_score:.3f}")
        return new_score
    except QuestSubmission.DoesNotExist:
        logger.error(f"Submission {submission_id} not found")
        return 0.0
    except Exception as exc:
        logger.error(f"Failed to update ability score for submission {submission_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def periodic_tree_adaptation():
    """
    Celery Beat task: Run every 24 hours to adapt trees for all active users.
    """
    from django.contrib.auth import get_user_model
    from datetime import timedelta

    User = get_user_model()
    cutoff_date = timezone.now() - timedelta(days=1)

    # Get users who were active in the last 24 hours
    active_users = User.objects.filter(
        last_login__gte=cutoff_date
    ).values_list('id', flat=True)

    for user_id in active_users:
        adapt_tree_for_user.delay(user_id)

    logger.info(f"Triggered periodic tree adaptation for {len(active_users)} users")
    return len(active_users)
