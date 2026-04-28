"""
SkillTree AI - Adaptive Learning Signal Handlers
Django signals to trigger adaptation on quest submission completion.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from quests.models import QuestSubmission
from skills.adaptive_tasks import update_ability_score_on_submission, adapt_tree_for_user

logger = logging.getLogger(__name__)


@receiver(post_save, sender=QuestSubmission)
def on_quest_submission_complete(sender, instance: QuestSubmission, created: bool, **kwargs):
    """
    Signal handler: Triggered when a QuestSubmission is saved.
    Triggers ability score update and tree adaptation if submission is complete.
    """
    if not created:
        return

    # Only process completed submissions
    if instance.status not in ['passed', 'failed']:
        return

    try:
        # Update ability score asynchronously
        update_ability_score_on_submission.delay(instance.id)

        # Trigger tree adaptation asynchronously
        adapt_tree_for_user.delay(instance.user.id)

        logger.info(f"Triggered adaptive tasks for user {instance.user.id} on submission {instance.id}")
    except Exception as e:
        logger.error(f"Failed to trigger adaptive tasks for submission {instance.id}: {e}")


def ready():
    """
    Called when the app is ready.
    Registers signal handlers.
    """
    pass
