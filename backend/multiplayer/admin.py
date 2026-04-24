from django.contrib import admin
from .models import Match


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'quest', 'status', 'winner', 'started_at', 'ended_at')
    list_filter = ('status',)
    search_fields = ('quest__title',)
