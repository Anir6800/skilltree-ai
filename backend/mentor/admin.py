from django.contrib import admin
from .models import AIInteraction


@admin.register(AIInteraction)
class AIInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'interaction_type', 'tokens_used', 'created_at')
    list_filter = ('interaction_type',)
    search_fields = ('user__username',)
