from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone


class PasswordResetCode(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='password_reset_codes',
    )
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at'], name='resetcode_user_created_idx'),
            models.Index(fields=['expires_at'], name='resetcode_expires_idx'),
        ]

    @classmethod
    def create_for_user(cls, user, code, expires_at):
        return cls.objects.create(
            user=user,
            code_hash=make_password(code),
            expires_at=expires_at,
        )

    def matches(self, code):
        return check_password(code, self.code_hash)

    def is_active(self):
        return self.used_at is None and self.expires_at > timezone.now()

    def mark_used(self):
        self.used_at = timezone.now()
        self.save(update_fields=['used_at'])
