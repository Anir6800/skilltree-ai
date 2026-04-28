"""
SkillTree AI - Quote Generator Signal Handlers
Django signals to trigger quote generation on quest submission completion.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from quests.models import QuestSubmission
from ai_evaluation.quote_generator import quote_generator

logger = logging.getLogger(__name__)


@receiver(post_save, sender=QuestSubmission)
def on_quest_submission_complete(sender, instance: QuestSubmission, created: bool, **kwargs):
    """
    Signal handler: Triggered when a QuestSubmission is saved.
    Pre-generates quote for completed submissions to avoid latency on frontend.
    """
    if not created:
        return

    # Only process completed submissions
    if instance.status not in ['passed', 'failed', 'flagged']:
        return

    try:
        # Pre-generate quote asynchronously (non-blocking)
        # This ensures quote is cached and ready when frontend requests it
        quote = quote_generator.generate_result_quote(instance)
        logger.info(f"Pre-generated quote for submission {instance.id}: {quote[:50]}...")
    except Exception as e:
        logger.error(f"Failed to pre-generate quote for submission {instance.id}: {e}")
        # Don't raise - quote generation failure shouldn't block submission processing


def ready():
    """
    Called when the app is ready.
    Registers signal handlers.
    """
    pass
