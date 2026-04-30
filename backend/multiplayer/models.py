"""
Multiplayer Domain Models — SkillTree AI
==========================================
Match              — Real-time competitive match between users on a shared quest
MatchParticipant   — Through-model for Match ↔ User with per-player scoring
"""

from django.db import models
from django.conf import settings
from quests.models import Quest


class Match(models.Model):
    """
    A real-time competitive match where participants solve the same Quest.

    Status lifecycle:
        waiting  → waiting for more participants to join
        active   → all participants are solving (started_at set)
        finished → at least one participant has passed (ended_at set, winner set)

    winner: SET_NULL on User delete — we keep the match record even if the
    winning user's account is deleted.

    Matches are delivered in real-time via Django Channels WebSocket consumers
    in multiplayer/consumers.py.
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
        related_name='matches',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_matches',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Matches'
        ordering = ['-created_at']
        indexes = [
            # Lobby listing: "show open matches for quest X"
            models.Index(fields=['status', 'quest'], name='match_status_quest_idx'),
            # Leaderboard: "how many times did user X win?"
            models.Index(fields=['winner'], name='match_winner_idx'),
            # Timeline / admin
            models.Index(fields=['-created_at'], name='match_created_at_idx'),
        ]

    def __str__(self):
        return f"Match#{self.id} — {self.quest.title} ({self.status})"


class MatchParticipant(models.Model):
    """
    Explicit through-model for Match ↔ User participation.

    score: points accumulated during this match (correct test cases × speed bonus).
    unique_together prevents a user joining the same match twice.
    """
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='match_participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='match_participations')
    score = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('match', 'user')
        indexes = [
            # "show all matches user X has participated in, newest first"
            models.Index(fields=['user', '-joined_at'], name='matchpart_user_joined_idx'),
            # "rank participants in match X by score"
            models.Index(fields=['match', '-score'], name='matchpart_match_score_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} in Match#{self.match_id} (score={self.score})"