from django.contrib import admin
from .models import Quest, QuestSubmission


@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ('title', 'skill', 'type', 'xp_reward', 'difficulty_multiplier')
    list_filter = ('type', 'skill__category')
    search_fields = ('title', 'description')


@admin.register(QuestSubmission)
class QuestSubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'quest', 'language', 'status', 'created_at')
    list_filter = ('status', 'language')
    search_fields = ('user__username', 'quest__title')
