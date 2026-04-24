from django.contrib import admin
from .models import Skill, SkillProgress


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'difficulty', 'xp_required_to_unlock')
    list_filter = ('category', 'difficulty')
    search_fields = ('title', 'description')


@admin.register(SkillProgress)
class SkillProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill', 'status', 'completed_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'skill__title')
