"""
SkillTree AI - Quote Generator Signal Handlers
Django signals to trigger quote generation on quest submission completion.

FIX: Quote generation is now dispatched as a Celery task (fire-and-forget)
instead of running synchronously in the signal handler.  The previous
synchronous approach caused:
  - LM Studio to receive a burst of requests on every submission save
  - Django request threads to block waiting for LM Studio
  - Celery retries to pile up and re-trigger the signal, creating a loop
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from quests.models import QuestSubmission

logger = logging.getLogger(__name__)


@receiver(post_save, sender=QuestSubmission)
def on_quest_submission_complete(sender, instance: QuestSubmission, created: bool, **kwargs):
    """
    Signal handler: Triggered when a QuestSubmission is saved.

    Only fires for *newly created* submissions that are already in a terminal
    state (passed / failed / flagged).  Quote generation is dispatched as a
    Celery task so it never blocks the HTTP response or the Celery pipeline.
    """
    if not created:
        return

    # Only pre-generate for terminal statuses
    if instance.status not in ('passed', 'failed', 'flagged'):
        return

    try:
        from ai_evaluation.quote_tasks import pregenerate_quote_task
        pregenerate_quote_task.delay(instance.id)
    except Exception as e:
        # Never let signal failures surface to the caller
        logger.warning(
            "Could not dispatch quote pre-generation task for submission %s: %s",
            instance.id, e,
        )


def ready():
    """Called when the app is ready. Registers signal handlers."""
    pass
