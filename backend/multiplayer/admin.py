from django.contrib import admin
from multiplayer.models import Match, MatchParticipant


class MatchParticipantInline(admin.TabularInline):
    model = MatchParticipant
    extra = 0
    readonly_fields = ['joined_at']


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    """Admin interface for Match model."""
    list_display = ['id', 'quest', 'status', 'winner', 'started_at', 'ended_at']
    list_filter = ['status', 'started_at']
    search_fields = ['quest__title', 'winner__username']
    readonly_fields = ['started_at', 'ended_at']
    inlines = [MatchParticipantInline]

    fieldsets = (
        ('Match Info', {
            'fields': ('quest', 'status', 'winner')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'ended_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MatchParticipant)
class MatchParticipantAdmin(admin.ModelAdmin):
    """Admin interface for MatchParticipant model."""
    list_display = ['id', 'match', 'user', 'score', 'joined_at']
    list_filter = ['joined_at']
    search_fields = ['match__id', 'user__username']
    readonly_fields = ['joined_at']
