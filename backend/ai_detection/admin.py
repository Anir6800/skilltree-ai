from django.contrib import admin
from .models import DetectionLog


@admin.register(DetectionLog)
class DetectionLogAdmin(admin.ModelAdmin):
    list_display = ('submission', 'final_score', 'embedding_score', 'llm_score', 'analyzed_at')
    list_filter = ('analyzed_at',)
    search_fields = ('submission__user__username',)
