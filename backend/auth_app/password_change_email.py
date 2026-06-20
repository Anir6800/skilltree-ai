"""
SkillTree AI - Secure Password Change Email Notification System
================================================================
Production-grade password change email system with:
- Immediate notification after password change
- Device/browser info tracking
- IP/location tracking (optional)
- Security warnings and recovery instructions
- Rate limiting and spam prevention
- Audit logging
- Async email queue with retry mechanism
- Never includes password in emails
"""

import logging
import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone as django_timezone
from django.db import transaction, models
from django.core.cache import cache
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from core.db_utils import generate_user_scoped_cache_key

logger = logging.getLogger(__name__)
User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# Rate Limiting Configuration
# ─────────────────────────────────────────────────────────────────────────────

RATE_LIMIT_CONFIG = {
    'per_user_per_hour': 5,      # Max 5 emails per user per hour
    'per_ip_per_hour': 20,       # Max 20 emails per IP per hour
    'global_per_minute': 100,    # Max 100 emails globally per minute
    'cooldown_seconds': 60,      # Cooldown between retries
    'max_retries': 3,            # Max retry attempts
    'retry_delay_seconds': [5, 15, 30],  # Exponential backoff
}


# ─────────────────────────────────────────────────────────────────────────────
# Audit Log Models
# ─────────────────────────────────────────────────────────────────────────────

class PasswordChangeAuditLog(models.Model):
    """
    Audit log for password change events.
    Stores security-relevant information for compliance and investigation.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='password_change_logs',
    )
    event_type = models.CharField(
        max_length=50,
        choices=[
            ('password_changed', 'Password Changed'),
            ('password_reset', 'Password Reset'),
            ('admin_password_reset', 'Admin-Forced Password Reset'),
            ('password_change_failed', 'Password Change Failed'),
        ],
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    location = models.CharField(max_length=255, blank=True, default='')
    success = models.BooleanField(default=True)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at'], name='pwdlog_user_created_idx'),
            models.Index(fields=['event_type', '-created_at'], name='pwdlog_event_idx'),
            models.Index(fields=['created_at'], name='pwdlog_created_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.event_type} - {self.created_at}"

    @classmethod
    def log_password_change(
        cls,
        user: User,
        event_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        location: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict] = None,
    ) -> 'PasswordChangeAuditLog':
        """
        Create an audit log entry for password change event.
        
        Args:
            user: User object
            event_type: Type of event
            ip_address: Client IP address
            user_agent: Browser user agent
            location: Optional location info
            success: Whether the change was successful
            details: Additional details as dict
            
        Returns:
            Created audit log entry
        """
        return cls.objects.create(
            user=user,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent or '',
            location=location or '',
            success=success,
            details=details or {},
        )


# ─────────────────────────────────────────────────────────────────────────────
# Email Queue System
# ─────────────────────────────────────────────────────────────────────────────

class EmailQueueEntry(models.Model):
    """
    Email queue entry for async email delivery with retry mechanism.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('max_retries_exceeded', 'Max Retries Exceeded'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='email_queue_entries',
    )
    email_type = models.CharField(
        max_length=50,
        choices=[
            ('password_changed', 'Password Changed'),
            ('password_reset', 'Password Reset'),
            ('admin_password_reset', 'Admin-Forced Password Reset'),
        ],
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pending',
    )
    retry_count = models.IntegerField(default=0)
    last_error = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at'], name='emailqueue_status_idx'),
            models.Index(fields=['user', 'status'], name='emailqueue_user_status_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.email_type} - {self.status}"

    def mark_sending(self):
        """Mark email as being sent."""
        self.status = 'sending'
        self.save(update_fields=['status'])

    def mark_sent(self):
        """Mark email as successfully sent."""
        self.status = 'sent'
        self.sent_at = django_timezone.now()
        self.save(update_fields=['status', 'sent_at'])

    def mark_failed(self, error: str):
        """Mark email as failed."""
        self.status = 'failed'
        self.last_error = error[:500]  # Truncate long errors
        self.retry_count += 1
        self.save(update_fields=['status', 'last_error', 'retry_count'])

    def mark_max_retries_exceeded(self):
        """Mark email as max retries exceeded."""
        self.status = 'max_retries_exceeded'
        self.save(update_fields=['status'])


# ─────────────────────────────────────────────────────────────────────────────
# Password Change Email Service
# ─────────────────────────────────────────────────────────────────────────────

class PasswordChangeEmailService:
    """
    Secure password change email notification service.
    Handles email generation, rate limiting, queueing, and delivery.
    """
    
    def __init__(self):
        """Initialize password change email service."""
        self.channel_layer = get_channel_layer()
        self.base_url = getattr(settings, "MAIL_SERVICE_URL", "http://127.0.0.1:4000").rstrip("/")
        self.rate_limit_config = RATE_LIMIT_CONFIG
        self.logger = logger
    
    def send_password_changed_email(
        self,
        user: User,
        event_type: str = 'password_changed',
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        location: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict] = None,
    ) -> bool:
        """
        Send password change notification email.
        
        Args:
            user: User object
            event_type: Type of event (password_changed, password_reset, admin_password_reset)
            ip_address: Client IP address
            user_agent: Browser user agent
            location: Optional location info
            success: Whether the change was successful
            details: Additional details
            
        Returns:
            True if email queued successfully, False otherwise
        """
        if not user or not user.is_authenticated:
            self.logger.warning("Cannot send password change email: user not authenticated")
            return False
        
        # Check rate limits
        if not self._check_rate_limits(user, ip_address):
            self.logger.warning(
                f"Rate limit exceeded for user {user.id} - email not sent"
            )
            return False
        
        # Create audit log
        self._create_audit_log(
            user=user,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            location=location,
            success=success,
            details=details,
        )
        
        # Generate email content
        email_data = self._build_email_data(
            user=user,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            location=location,
            success=success,
            details=details,
        )
        
        # Queue email for async delivery
        email_queued = self._queue_email(
            user=user,
            email_type=event_type,
            email_data=email_data,
        )
        
        if email_queued:
            self.logger.info(
                f"Password change email queued for user {user.id}: {event_type}"
            )
        else:
            self.logger.error(
                f"Failed to queue password change email for user {user.id}"
            )
        
        return email_queued
    
    def _check_rate_limits(self, user: User, ip_address: Optional[str] = None) -> bool:
        """
        Check rate limits for password change emails.
        
        Args:
            user: User object
            ip_address: Client IP address
            
        Returns:
            True if within rate limits, False otherwise
        """
        now = time.time()
        
        # Per-user rate limit
        user_key = f"pwd_change_rate_limit:user:{user.id}"
        user_count = cache.get(user_key, 0)
        
        if user_count >= self.rate_limit_config['per_user_per_hour']:
            return False
        
        # Per-IP rate limit (if IP provided)
        if ip_address:
            ip_key = f"pwd_change_rate_limit:ip:{ip_address}"
            ip_count = cache.get(ip_key, 0)
            
            if ip_count >= self.rate_limit_config['per_ip_per_hour']:
                return False
        
        # Global rate limit
        global_key = "pwd_change_rate_limit:global"
        global_count = cache.get(global_key, 0)
        
        if global_count >= self.rate_limit_config['global_per_minute']:
            return False
        
        # Update rate limit counters
        cache.set(user_key, user_count + 1, 3600)  # 1 hour
        if ip_address:
            cache.set(ip_key, ip_count + 1, 3600)  # 1 hour
        cache.set(global_key, global_count + 1, 60)  # 1 minute
        
        return True
    
    def _create_audit_log(
        self,
        user: User,
        event_type: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        location: Optional[str],
        success: bool,
        details: Optional[Dict],
    ) -> None:
        """
        Create audit log entry for password change event.
        
        Args:
            user: User object
            event_type: Type of event
            ip_address: Client IP address
            user_agent: Browser user agent
            location: Location info
            success: Whether successful
            details: Additional details
        """
        try:
            PasswordChangeAuditLog.log_password_change(
                user=user,
                event_type=event_type,
                ip_address=ip_address,
                user_agent=user_agent,
                location=location,
                success=success,
                details=details or {},
            )
        except Exception as e:
            self.logger.error(f"Failed to create audit log: {e}")
    
    def _build_email_data(
        self,
        user: User,
        event_type: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        location: Optional[str],
        success: bool,
        details: Optional[Dict],
    ) -> Dict[str, Any]:
        """
        Build email data for password change notification.
        
        Args:
            user: User object
            event_type: Type of event
            ip_address: Client IP address
            user_agent: Browser user agent
            location: Location info
            success: Whether successful
            details: Additional details
            
        Returns:
            Email data dictionary
        """
        # Parse user agent for device info
        device_info = self._parse_user_agent(user_agent) if user_agent else {}
        
        # Get timestamp
        timestamp = django_timezone.now()
        
        # Build email data
        email_data = {
            'email': user.email,
            'username': user.username,
            'event_type': event_type,
            'timestamp': timestamp.isoformat(),
            'timestamp_formatted': timestamp.strftime('%B %d, %Y at %I:%M %p %Z'),
            'security_warning': True,
            'support_contact': getattr(settings, 'SUPPORT_EMAIL', 'support@skilltree.ai'),
            'recovery_instructions': True,
            'ip_address': ip_address,
            'location': location,
            'device_info': device_info,
            'user_agent': user_agent,
            'success': success,
            'details': details or {},
        }
        
        return email_data
    
    def _parse_user_agent(self, user_agent: str) -> Dict[str, str]:
        """
        Parse user agent string for device info.
        
        Args:
            user_agent: User agent string
            
        Returns:
            Dictionary with device info
        """
        device_info = {
            'browser': 'Unknown',
            'os': 'Unknown',
            'device': 'Unknown',
        }
        
        if not user_agent:
            return device_info
        
        # Simple user agent parsing
        ua_lower = user_agent.lower()
        
        # Browser detection
        if 'chrome' in ua_lower and 'edg' not in ua_lower:
            device_info['browser'] = 'Chrome'
        elif 'firefox' in ua_lower:
            device_info['browser'] = 'Firefox'
        elif 'safari' in ua_lower and 'chrome' not in ua_lower:
            device_info['browser'] = 'Safari'
        elif 'edg' in ua_lower:
            device_info['browser'] = 'Edge'
        elif 'msie' in ua_lower or 'trident' in ua_lower:
            device_info['browser'] = 'Internet Explorer'
        
        # OS detection
        if 'windows' in ua_lower:
            device_info['os'] = 'Windows'
        elif 'mac' in ua_lower:
            device_info['os'] = 'macOS'
        elif 'linux' in ua_lower:
            device_info['os'] = 'Linux'
        elif 'android' in ua_lower:
            device_info['os'] = 'Android'
        elif 'iphone' in ua_lower or 'ipad' in ua_lower:
            device_info['os'] = 'iOS'
        
        # Device detection
        if 'mobile' in ua_lower or 'android' in ua_lower or 'iphone' in ua_lower:
            device_info['device'] = 'Mobile'
        elif 'ipad' in ua_lower or 'tablet' in ua_lower:
            device_info['device'] = 'Tablet'
        else:
            device_info['device'] = 'Desktop'
        
        return device_info
    
    def _queue_email(
        self,
        user: User,
        email_type: str,
        email_data: Dict[str, Any],
    ) -> bool:
        """
        Queue email for async delivery.
        
        Args:
            user: User object
            email_type: Type of email
            email_data: Email data
            
        Returns:
            True if queued successfully, False otherwise
        """
        try:
            # Create queue entry
            queue_entry = EmailQueueEntry.objects.create(
                user=user,
                email_type=email_type,
                status='pending',
                metadata=email_data,
            )
            
            # Trigger async email delivery
            self._trigger_async_email_delivery(queue_entry)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to queue email: {e}")
            return False
    
    def _trigger_async_email_delivery(self, queue_entry: EmailQueueEntry) -> None:
        """
        Trigger async email delivery via Celery or sync fallback.
        
        Args:
            queue_entry: Email queue entry
        """
        try:
            # Try Celery first
            from executor.tasks import send_password_change_email_task
            send_password_change_email_task.delay(queue_entry.id)
        except Exception:
            # Fallback to sync delivery
            self._deliver_email_sync(queue_entry)
    
    def _deliver_email_sync(self, queue_entry: EmailQueueEntry) -> bool:
        """
        Deliver email synchronously (fallback when Celery unavailable).
        
        Args:
            queue_entry: Email queue entry
            
        Returns:
            True if delivered successfully, False otherwise
        """
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
            response = requests.post(
                f"{self.base_url}/auth-mail/password-change",
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            
            queue_entry.mark_sent()
            return True
            
        except requests.RequestException as e:
            queue_entry.mark_failed(str(e))
            
            # Retry if not max retries exceeded
            if queue_entry.retry_count < self.rate_limit_config['max_retries']:
                delay = self.rate_limit_config['retry_delay_seconds'][queue_entry.retry_count - 1]
                self.logger.info(
                    f"Retrying email delivery in {delay} seconds for queue entry {queue_entry.id}"
                )
                # Schedule retry
                self._schedule_retry(queue_entry, delay)
            
            return False
    
    def _schedule_retry(self, queue_entry: EmailQueueEntry, delay: int) -> None:
        """
        Schedule email retry with delay.
        
        Args:
            queue_entry: Email queue entry
            delay: Delay in seconds
        """
        try:
            from executor.tasks import send_password_change_email_task
            send_password_change_email_task.apply_async(
                args=[queue_entry.id],
                countdown=delay,
            )
        except Exception as e:
            self.logger.error(f"Failed to schedule retry: {e}")
            queue_entry.mark_max_retries_exceeded()
    
    def process_email_queue(self) -> int:
        """
        Process pending emails in queue.
        
        Returns:
            Number of emails processed
        """
        pending_emails = EmailQueueEntry.objects.filter(status__in=['pending', 'failed'])
        
        processed = 0
        for queue_entry in pending_emails[:100]:  # Process max 100 at a time
            if queue_entry.retry_count >= self.rate_limit_config['max_retries']:
                queue_entry.mark_max_retries_exceeded()
                continue
            
            success = self._deliver_email_sync(queue_entry)
            if success:
                processed += 1
        
        return processed
    
    def get_user_email_history(self, user: User) -> List[Dict[str, Any]]:
        """
        Get email delivery history for user.
        
        Args:
            user: User object
            
        Returns:
            List of email delivery records
        """
        emails = EmailQueueEntry.objects.filter(user=user).order_by('-created_at')[:50]
        
        return [
            {
                'id': email.id,
                'email_type': email.email_type,
                'status': email.status,
                'retry_count': email.retry_count,
                'created_at': email.created_at.isoformat(),
                'sent_at': email.sent_at.isoformat() if email.sent_at else None,
                'last_error': email.last_error,
            }
            for email in emails
        ]
    
    def get_audit_logs(self, user: User, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get audit logs for user's password changes.
        
        Args:
            user: User object
            event_type: Optional event type filter
            
        Returns:
            List of audit log entries
        """
        logs = PasswordChangeAuditLog.objects.filter(user=user)
        
        if event_type:
            logs = logs.filter(event_type=event_type)
        
        logs = logs.order_by('-created_at')[:100]
        
        return [
            {
                'id': log.id,
                'event_type': log.event_type,
                'ip_address': log.ip_address,
                'location': log.location,
                'success': log.success,
                'details': log.details,
                'created_at': log.created_at.isoformat(),
            }
            for log in logs
        ]


# Singleton instance
password_change_email_service = PasswordChangeEmailService()
