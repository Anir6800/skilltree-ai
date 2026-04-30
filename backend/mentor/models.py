"""
Mentor Domain Models — SkillTree AI
=====================================
AIInteraction — AI mentoring interaction log (hints, explanations, path suggestions)
HintUsage     — Per-user per-quest hint consumption tracker with rate limiting
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class AIInteraction(models.Model):
    """
    Audit log for all AI-driven mentoring interactions.

    Used for:
        - token usage monitoring
        - quality review of AI responses
        - rate limiting (future)
        - analytics on interaction type distribution

    context_prompt and response are stored in full for auditability.
    Do NOT truncate these fields.
    """
    INTERACTION_TYPE_CHOICES = [
        ('hint', 'Hint'),
        ('explanation', 'Explanation'),
        ('path_suggestion', 'Path Suggestion'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_interactions',
    )
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPE_CHOICES)
    context_prompt = models.TextField()
    response = models.TextField()
    tokens_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            # "show all hint interactions for user X"
            models.Index(fields=['user', 'interaction_type', '-created_at'], name='aiinteraction_user_type_idx'),
            # Token usage analytics: "total tokens used per type this month"
            models.Index(fields=['interaction_type', 'created_at'], name='aiinteraction_type_date_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} — {self.interaction_type} ({self.created_at.strftime('%Y-%m-%d')})"


class HintUsage(models.Model):
    """
    Per-user per-quest hint consumption record.

    Hint levels:
        1 = Nudge       (minimal guidance, low XP penalty)
        2 = Approach    (strategic guidance, medium XP penalty)
        3 = Near-Solution (near-complete guidance, high XP penalty)

    Rate limiting:
        can_request_hint() enforces a maximum of MAX_DAILY_HINTS (5) per quest per day.
        The daily window resets at midnight UTC.

    xp_penalty: applied when the user next passes the quest; reduces total XP awarded.
    """
    MAX_DAILY_HINTS = 5

    HINT_LEVEL_CHOICES = [
        (1, 'Nudge'),
        (2, 'Approach'),
        (3, 'Near-Solution'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hint_usages',
    )
    quest = models.ForeignKey(
        'quests.Quest',
        on_delete=models.CASCADE,
        related_name='hint_usages',
    )
    hint_level = models.IntegerField(choices=HINT_LEVEL_CHOICES)
    hint_text = models.TextField()
    xp_penalty = models.IntegerField(default=0)
    requested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-requested_at']
        indexes = [
            # "how many hints has user X used for quest Y today?" (rate limiting)
            models.Index(fields=['user', 'quest', 'requested_at'], name='hintusage_user_quest_date_idx'),
            # User hint history dashboard
            models.Index(fields=['user', '-requested_at'], name='hintusage_user_history_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} — {self.quest.title} (L{self.hint_level})"

    @classmethod
    def get_hints_used_today(cls, user, quest) -> int:
        """Return number of hints used for quest today (UTC midnight reset)."""
        today = timezone.now().date()
        return cls.objects.filter(
            user=user,
            quest=quest,
            requested_at__date=today,
        ).count()

    @classmethod
    def get_hints_used_for_quest(cls, user, quest):
        """Return all hints used for a quest across all time, ordered by level."""
        return cls.objects.filter(user=user, quest=quest).order_by('hint_level')

    @classmethod
    def can_request_hint(cls, user, quest) -> bool:
        """Return True if user has not yet hit the daily hint limit for this quest."""
        return cls.get_hints_used_today(user, quest) < cls.MAX_DAILY_HINTS