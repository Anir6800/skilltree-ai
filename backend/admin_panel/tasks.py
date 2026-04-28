"""
Celery tasks for assessment evaluation.
Handles async evaluation and WebSocket broadcasting.
"""

import logging
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def evaluate_assessment_submission(self, submission_id: int):
    """
    Async task to evaluate an assessment submission.
    Broadcasts result via WebSocket when complete.
    
    Args:
        submission_id: ID of AssessmentSubmission to evaluate
    """
    from admin_panel.models import AssessmentSubmission
    from admin_panel.assessment_engine import assessment_engine
    
    try:
        # Fetch submission
        submission = AssessmentSubmission.objects.select_related('question', 'user').get(id=submission_id)
        
        # Update status to evaluating
        submission.status = 'evaluating'
        submission.save(update_fields=['status'])
        
        # Run evaluation
        result = assessment_engine.evaluate(submission)
        
        # Update submission with results
        submission.status = 'evaluated'
        submission.result = result.to_dict()
        submission.score = result.score
        submission.passed = result.passed
        submission.evaluated_at = timezone.now()
        submission.save(update_fields=['status', 'result', 'score', 'passed', 'evaluated_at'])
        
        # Broadcast result via WebSocket
        channel_layer = get_channel_layer()
        group_name = f'assessment_{submission_id}'
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'assessment_result',
                'submission_id': submission_id,
                'result': result.to_dict(),
                'score': result.score,
                'passed': result.passed,
                'status': 'evaluated'
            }
        )
        
        return {
            'submission_id': submission_id,
            'status': 'evaluated',
            'score': result.score,
            'passed': result.passed
        }
        
    except ObjectDoesNotExist:
        # Submission not found
        return {
            'submission_id': submission_id,
            'status': 'error',
            'error': 'Submission not found'
        }
        
    except Exception as e:
        logger.error(f"Assessment evaluation failed for submission {submission_id}: {e}", exc_info=True)
        # Update submission status to error
        try:
            submission = AssessmentSubmission.objects.get(id=submission_id)
            submission.status = 'error'
            submission.result = {
                'error': str(e),
                'feedback': f'Evaluation failed: {str(e)}'
            }
            submission.save(update_fields=['status', 'result'])
        except Exception as inner_exc:
            logger.error(f"Failed to update submission {submission_id} error state: {inner_exc}")
        
        # Retry task if retries remaining
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=5)
        
        return {
            'submission_id': submission_id,
            'status': 'error',
            'error': str(e)
        }
