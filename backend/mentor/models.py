from django.db import models
from django.conf import settings

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