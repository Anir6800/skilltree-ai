"""
SkillTree AI - Leaderboard Celery Tasks
Periodic tasks for snapshotting rankings and resetting weekly boards.
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='leaderboard.tasks.snapshot_leaderboard', bind=True, max_retries=3)
def snapshot_leaderboard(self):
    """
    Snapshot current Redis global rankings to LeaderboardSnapshot table.
    Scheduled every 5 minutes via Celery beat.
    """
    try:
        from leaderboard.services import snapshot_rankings
        count = snapshot_rankings()
        logger.info(f"snapshot_leaderboard: persisted {count} entries")
        return {'status': 'ok', 'count': count}
    except Exception as exc:
        logger.error(f"snapshot_leaderboard failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60)


@shared_task(name='leaderboard.tasks.reset_weekly', bind=True, max_retries=3)
def reset_weekly(self):
    """
    Reset the weekly leaderboard Redis key.
    Scheduled every Monday at 00:00 UTC via Celery beat.
    """
    try:
        from leaderboard.services import reset_weekly_leaderboard
        success = reset_weekly_leaderboard()
        logger.info(f"reset_weekly: success={success}")
        return {'status': 'ok', 'reset': success}
    except Exception as exc:
        logger.error(f"reset_weekly failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=120)


@shared_task(name='leaderboard.tasks.refresh_user_score', bind=True, max_retries=3)
def refresh_user_score(self, user_id):
    """
    Recompute and push a single user's leaderboard score to Redis.
    Called after quest submission, XP award, or streak update.
    """
    try:
        from leaderboard.services import update_leaderboard
        score = update_leaderboard(user_id)
        logger.debug(f"refresh_user_score: user={user_id} score={score}")
        return {'status': 'ok', 'user_id': user_id, 'score': score}
    except Exception as exc:
        logger.error(f"refresh_user_score failed for user {user_id}: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=30)
