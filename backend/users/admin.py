from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .adaptive_admin import AdaptiveProfileAdmin, UserSkillFlagAdmin
from .badge_admin import BadgeAdmin, UserBadgeAdmin


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'level', 'xp', 'streak_days', 'role')
    list_filter = ('role', 'level')
    fieldsets = UserAdmin.fieldsets + (
        ('SkillTree Info', {'fields': ('xp', 'level', 'streak_days', 'last_active', 'role', 'avatar_url')}),
    )
