"""
SkillTree AI - Adaptive Learning Models
Tracks user ability scores, difficulty preferences, and skill flags.
"""

from django.db import models
from django.conf import settings
from skills.models import Skill


class AdaptiveProfile(models.Model):
    """
    Stores adaptive learning profile for a user.
    Tracks ability score, preferred difficulty, and adjustment history.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='adaptive_profile'
    )
    ability_score = models.FloatField(
        default=0.5,
        help_text="0.0 (struggling) to 1.0 (advanced), updated via Bayesian formula"
    )
    preferred_difficulty = models.IntegerField(
        default=3,
        help_text="Auto-set to ceil(ability_score * 5), range 1-5"
    )
    adjustment_history = models.JSONField(
        default=list,
        help_text="Log of every adjustment with timestamp and reason"
    )
    last_adjusted = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp of last adaptation"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Adaptive Profile"
        verbose_name_plural = "Adaptive Profiles"
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['ability_score']),
            models.Index(fields=['preferred_difficulty']),
        ]

    def __str__(self):
        return f"{self.user.username} - Ability: {self.ability_score:.2f}, Difficulty: {self.preferred_difficulty}"


class UserSkillFlag(models.Model):
    """
    Flags for user-skill relationships indicating special states.
    Examples: "too_easy", "struggling", "mastered"
    """
    FLAG_CHOICES = [
        ('too_easy', 'Too Easy'),
        ('struggling', 'Struggling'),
        ('mastered', 'Mastered'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='skill_flags'
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='user_flags'
    )
    flag = models.CharField(
        max_length=20,
        choices=FLAG_CHOICES,
        help_text="Type of flag (too_easy, struggling, mastered)"
    )
    reason = models.TextField(
        blank=True,
        default='',
        help_text="Reason for flagging (e.g., 'Consecutive failures: 3')"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'skill', 'flag')
        verbose_name = "User Skill Flag"
        verbose_name_plural = "User Skill Flags"
        indexes = [
            models.Index(fields=['user', 'flag']),
            models.Index(fields=['skill', 'flag']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.skill.title}: {self.flag}"
