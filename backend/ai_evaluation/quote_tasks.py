"""
SkillTree AI - Quote Generator Celery Tasks
Async quote pre-generation so LM Studio is never called synchronously
from a Django signal or HTTP request thread.
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    name='ai_evaluation.quote_tasks.pregenerate_quote_task',
    bind=True,
    max_retries=1,          # Only one retry — LM Studio unavailability is transient
    default_retry_delay=60, # Wait 60 s before retrying (not immediately)
    ignore_result=True,     # We don't need the return value
)
def pregenerate_quote_task(self, submission_id: int) -> None:
    """
    Pre-generate and cache a motivational quote for a completed submission.

    Runs asynchronously via Celery so it never blocks the HTTP response.
    If LM Studio is unavailable the task silently succeeds (the frontend
    will receive a fallback quote on demand).
    """
    try:
        from quests.models import QuestSubmission
        from ai_evaluation.quote_generator import quote_generator
        from core.lm_client import lm_client

        # Skip entirely if LM Studio is not reachable — avoids queuing
        # a retry that would just fail again immediately.
        if not lm_client.is_available():
            logger.info(
                "LM Studio unavailable — skipping quote pre-generation for submission %s",
                submission_id,
            )
            return

        submission = QuestSubmission.objects.select_related('quest', 'user').get(
            id=submission_id
        )
        quote = quote_generator.generate_result_quote(submission)
        logger.info(
            "Pre-generated quote for submission %s: %.60s…",
            submission_id, quote,
        )

    except Exception as exc:
        logger.warning(
            "Quote pre-generation failed for submission %s: %s",
            submission_id, exc,
        )
        # Retry once after 60 s; if it fails again, give up silently
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.info(
                "Max retries exceeded for quote pre-generation of submission %s — giving up",
                submission_id,
            )
