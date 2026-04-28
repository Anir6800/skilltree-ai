from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class AIInteraction(models.Model):
    """
    Tracks AI-driven mentoring interactions for auditing and usage analysis.
    """
    INTERACTION_TYPE_CHOICES = [
        ('hint', 'Hint'),
        ('explanation', 'Explanation'),
        ('path_suggestion', 'Path Suggestion'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_interactions')
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPE_CHOICES)
    context_prompt = models.TextField()
    response = models.TextField()
    tokens_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.interaction_type} ({self.created_at.strftime('%Y-%m-%d')})"


class HintUsage(models.Model):
    """
    Tracks hint usage per user per quest with XP penalties.
    Enforces rate limiting (max 5 hints per quest per user).
    """
    HINT_LEVEL_CHOICES = [
        (1, 'Nudge'),
        (2, 'Approach'),
        (3, 'Near-Solution'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hint_usages')
    quest = models.ForeignKey('quests.Quest', on_delete=models.CASCADE, related_name='hint_usages')
    hint_level = models.IntegerField(choices=HINT_LEVEL_CHOICES)
    hint_text = models.TextField()
    xp_penalty = models.IntegerField(default=0)
    requested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['user', 'quest']),
            models.Index(fields=['user', 'requested_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.quest.title} (L{self.hint_level})"

    @classmethod
    def get_hints_used_today(cls, user, quest):
        """Get count of hints used for this quest today."""
        today = timezone.now().date()
        return cls.objects.filter(
            user=user,
            quest=quest,
            requested_at__date=today
        ).count()

    @classmethod
    def get_hints_used_for_quest(cls, user, quest):
        """Get all hints used for this quest (all time)."""
        return cls.objects.filter(
            user=user,
            quest=quest
        ).order_by('hint_level')

    @classmethod
    def can_request_hint(cls, user, quest):
        """Check if user can request another hint for this quest."""
        hints_used = cls.get_hints_used_today(user, quest)
        return hints_used < 5