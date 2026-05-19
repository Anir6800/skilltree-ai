"""
SkillTree AI - Password Change Email Tasks
===========================================
Celery tasks for async password change email delivery with retry mechanism.
"""

import logging
import time
from celery import shared_task
from django.conf import settings
from django.core.cache import cache

from .password_change_email import EmailQueueEntry, password_change_email_service

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Email Delivery Tasks
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
)
def send_password_change_email_task(self, queue_entry_id: int) -> bool:
    """
    Send password change email with retry mechanism.
    
    Args:
        self: Task instance
        queue_entry_id: Email queue entry ID
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        queue_entry = EmailQueueEntry.objects.get(id=queue_entry_id)
    except EmailQueueEntry.DoesNotExist:
        logger.error(f"Email queue entry {queue_entry_id} not found")
        return False
    
    # Check if max retries exceeded
    if queue_entry.retry_count >= getattr(settings, 'EMAIL_MAX_RETRIES', 3):
        queue_entry.mark_max_retries_exceeded()
        logger.warning(
            f"Max retries exceeded for email queue entry {queue_entry_id}"
        )
        return False
    
    # Mark as sending
    queue_entry.mark_sending()
    
    try:
        # Build email payload
        payload = {
            'email': queue_entry.user.email,
            'username': queue_entry.user.username,
            'email_type': queue_entry.email_type,
            **queue_entry.metadata,
        }
        
        # Send to mail service
        import requests
        base_url = getattr(settings, "MAIL_SERVICE_URL", "http://127.0.0.1:4000").rstrip("/")
        
        response = requests.post(
            f"{base_url}/auth-mail/password-change",
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        
        # Mark as sent
        queue_entry.mark_sent()
        
        logger.info(
            f"Password change email sent successfully for user {queue_entry.user.id}"
        )
        return True
        
    except requests.RequestException as e:
        queue_entry.mark_failed(str(e))
        
        # Check if we should retry
        if queue_entry.retry_count < getattr(settings, 'EMAIL_MAX_RETRIES', 3):
            # Schedule retry with exponential backoff
            retry_delay = min(
                5 * (2 ** queue_entry.retry_count),
                300  # Max 5 minutes
            )
            
            logger.info(
                f"Scheduling retry {queue_entry.retry_count + 1} for email "
                f"queue entry {queue_entry_id} in {retry_delay} seconds"
            )
            
            # Schedule retry
            send_password_change_email_task.apply_async(
                args=[queue_entry_id],
                countdown=retry_delay,
            )
            
            return False
        else:
            queue_entry.mark_max_retries_exceeded()
            logger.error(
                f"Email delivery failed after max retries for queue entry {queue_entry_id}"
            )
            return False
    
    except Exception as e:
        queue_entry.mark_failed(str(e))
        logger.error(
            f"Unexpected error sending email for queue entry {queue_entry_id}: {e}"
        )
        return False


@shared_task
def process_email_queue() -> int:
    """
    Process pending emails in queue.
    
    Returns:
        Number of emails processed
    """
    return password_change_email_service.process_email_queue()


@shared_task
def cleanup_old_email_entries() -> int:
    """
    Clean up old email queue entries.
    Deletes entries older than 90 days.
    
    Returns:
        Number of entries deleted
    """
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff = timezone.now() - timedelta(days=90)
    
    # Delete old entries
    deleted_count, _ = EmailQueueEntry.objects.filter(
        created_at__lt=cutoff
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old email queue entries")
    return deleted_count


@shared_task
def cleanup_old_audit_logs() -> int:
    """
    Clean up old audit logs.
    Deletes entries older than 1 year.
    
    Returns:
        Number of entries deleted
    """
    from django.utils import timezone
    from datetime import timedelta
    from .password_change_email import PasswordChangeAuditLog
    
    cutoff = timezone.now() - timedelta(days=365)
    
    # Delete old audit logs
    deleted_count, _ = PasswordChangeAuditLog.objects.filter(
        created_at__lt=cutoff
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old audit log entries")
    return deleted_count


# ─────────────────────────────────────────────────────────────────────────────
# Rate Limit Cleanup Tasks
# ─────────────────────────────────────────────────────────────────────────────

@shared_task
def cleanup_rate_limit_cache() -> int:
    """
    Clean up expired rate limit cache entries.
    
    Returns:
        Number of cache entries cleared
    """
    # This is handled automatically by Django cache TTL
    # But we can add explicit cleanup if needed
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Email Delivery Status Tasks
# ─────────────────────────────────────────────────────────────────────────────

@shared_task
def check_email_delivery_status(queue_entry_id: int) -> Dict[str, Any]:
    """
    Check the delivery status of an email.
    
    Args:
        queue_entry_id: Email queue entry ID
        
    Returns:
        Dictionary with delivery status
    """
    try:
        queue_entry = EmailQueueEntry.objects.get(id=queue_entry_id)
        
        return {
            'status': queue_entry.status,
            'retry_count': queue_entry.retry_count,
            'last_error': queue_entry.last_error,
            'created_at': queue_entry.created_at.isoformat(),
            'sent_at': queue_entry.sent_at.isoformat() if queue_entry.sent_at else None,
        }
        
    except EmailQueueEntry.DoesNotExist:
        return {
            'error': 'Email queue entry not found',
            'status': 'not_found',
        }
