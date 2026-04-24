from django.contrib import admin
from .models import LeaderboardSnapshot


@admin.register(LeaderboardSnapshot)
class LeaderboardSnapshotAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_xp', 'rank', 'streak_days', 'snapshot_at')
    list_filter = ('snapshot_at',)
    search_fields = ('user__username',)
