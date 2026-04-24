from django.db import models
from django.conf import settings
from quests.models import Quest

class Match(models.Model):
    """
    Real-time multiplayer matches for competitive learning.
    """
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('active', 'Active'),
        ('finished', 'Finished'),
    ]

    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='matches')
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        through='MatchParticipant',
        related_name='matches'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='won_matches'
    )
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Matches"

    def __str__(self):
        return f"Match #{self.id} - {self.quest.title} ({self.status})"

class MatchParticipant(models.Model):
    """
    Explicit through model for Match participants.
    """
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(default=0)

    class Meta:
        unique_together = ('match', 'user')

    def __str__(self):
        return f"{self.user.username} in Match #{self.match.id}"