from django.db import models
from django.conf import settings

class LeaderboardSnapshot(models.Model):
    """
    Historical record of user rankings for progress tracking.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leaderboard_snapshots')
    total_xp = models.IntegerField()
    rank = models.IntegerField()
    streak_days = models.IntegerField()
    snapshot_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['rank']
        get_latest_by = 'snapshot_at'
        indexes = [
            models.Index(fields=['user', 'snapshot_at'], name='leaderboard_user_snap_idx'),
            models.Index(fields=['-snapshot_at'], name='leaderboard_snap_at_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} - Rank #{self.rank} ({self.total_xp} XP)"