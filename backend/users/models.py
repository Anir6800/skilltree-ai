from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone

class User(AbstractUser):
    """
    SkillTree AI Custom User model.
    Tracks player progression, XP, and immersive attributes.
    """
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
    ]
    
    xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    streak_days = models.IntegerField(default=0)
    last_active = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    avatar_url = models.CharField(max_length=500, default='', blank=True)

    def save(self, *args, **kwargs):
        # Auto-compute level from XP: level = xp // 500 + 1
        self.level = (self.xp // 500) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} (Lvl {self.level})"

class XPLog(models.Model):
    """
    Log of XP gained by a user. Used for history charts.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='xp_logs')
    amount = models.IntegerField()
    source = models.CharField(max_length=200) # e.g. "Quest: Python Basics"
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} +{self.amount} XP from {self.source}"


class Badge(models.Model):
    """
    Achievement badge definition.
    Defines badge metadata and unlock conditions.
    """
    RARITY_CHOICES = [
        ('common', 'Common'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
        ('legendary', 'Legendary'),
    ]

    slug = models.SlugField(unique=True, max_length=100)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon_emoji = models.CharField(max_length=10)
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, default='common')
    unlock_condition = models.JSONField(
        default=dict,
        help_text="Condition to unlock badge: {event_type, criteria}"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['rarity', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['rarity']),
        ]

    def __str__(self):
        return f"{self.icon_emoji} {self.name} ({self.rarity})"


class UserBadge(models.Model):
    """
    User's earned badge.
    Tracks when user earned a badge and whether they've seen it.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='user_badges')
    earned_at = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'badge')
        ordering = ['-earned_at']
        indexes = [
            models.Index(fields=['user', 'seen']),
            models.Index(fields=['badge']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"



class WeeklyReport(models.Model):
    """
    Weekly progress report for a user.
    Generated every Monday with AI narrative and PDF.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_reports')
    week_number = models.IntegerField(help_text='ISO week number (1-53)')
    year = models.IntegerField(default=2026)
    pdf_path = models.CharField(max_length=500, help_text='Path to generated PDF file')
    data = models.JSONField(default=dict, help_text='Collected metrics for the week')
    narrative = models.JSONField(default=dict, help_text='AI-generated narrative sections')
    generated_at = models.DateTimeField(auto_now_add=True)
    viewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-generated_at']
        unique_together = ('user', 'week_number', 'year')
        indexes = [
            models.Index(fields=['user', '-generated_at']),
            models.Index(fields=['week_number', 'year']),
        ]

    def __str__(self):
        return f"{self.user.username} - Week {self.week_number}/{self.year}"

    def mark_viewed(self):
        """Mark report as viewed."""
        if not self.viewed_at:
            self.viewed_at = timezone.now()
            self.save(update_fields=['viewed_at'])
