"""
SkillTree AI - Adaptive Profile Admin Configuration
Django admin interface for adaptive learning models.
"""

from django.contrib import admin
from django.utils.html import format_html
from users.models_adaptive import AdaptiveProfile, UserSkillFlag


@admin.register(AdaptiveProfile)
class AdaptiveProfileAdmin(admin.ModelAdmin):
    """Admin interface for AdaptiveProfile."""
    list_display = [
        'user',
        'ability_score_display',
        'preferred_difficulty',
        'last_adjusted',
    ]
    list_filter = ['preferred_difficulty', 'last_adjusted', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'last_adjusted', 'adjustment_history_display']

    fieldsets = (
        ('User', {
            'fields': ('user',),
        }),
        ('Ability Metrics', {
            'fields': ('ability_score', 'preferred_difficulty'),
        }),
        ('History', {
            'fields': ('adjustment_history_display', 'created_at', 'last_adjusted'),
            'classes': ('collapse',),
        }),
    )

    def ability_score_display(self, obj):
        """Display ability score with color coding."""
        score = obj.ability_score
        if score >= 0.8:
            color = '#28a745'  # Green
            label = 'Advanced'
        elif score >= 0.6:
            color = '#ffc107'  # Yellow
            label = 'Intermediate'
        elif score >= 0.4:
            color = '#fd7e14'  # Orange
            label = 'Beginner'
        else:
            color = '#dc3545'  # Red
            label = 'Struggling'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2f} ({})</span>',
            color, score, label
        )
    ability_score_display.short_description = 'Ability Score'

    def adjustment_history_display(self, obj):
        """Display adjustment history in readable format."""
        if not obj.adjustment_history:
            return 'No adjustments yet'

        html = '<ul style="list-style-type: none; padding: 0;">'
        for adjustment in obj.adjustment_history[-10:]:  # Show last 10
            timestamp = adjustment.get('timestamp', 'N/A')
            reason = adjustment.get('reason', 'N/A')
            changes = adjustment.get('changes', {})
            changes_str = ', '.join(f"{k}: {v}" for k, v in changes.items())

            html += f'<li style="margin-bottom: 10px; padding: 8px; background: #f5f5f5; border-radius: 4px;">'
            html += f'<strong>{timestamp}</strong><br/>'
            html += f'Reason: {reason}<br/>'
            html += f'Changes: {changes_str}'
            html += '</li>'

        html += '</ul>'
        return format_html(html)
    adjustment_history_display.short_description = 'Adjustment History'


@admin.register(UserSkillFlag)
class UserSkillFlagAdmin(admin.ModelAdmin):
    """Admin interface for UserSkillFlag."""
    list_display = [
        'user',
        'skill',
        'flag_display',
        'created_at',
    ]
    list_filter = ['flag', 'created_at', 'skill__difficulty']
    search_fields = ['user__username', 'skill__title']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Relationship', {
            'fields': ('user', 'skill'),
        }),
        ('Flag Details', {
            'fields': ('flag', 'reason'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def flag_display(self, obj):
        """Display flag with color coding."""
        colors = {
            'too_easy': '#28a745',      # Green
            'struggling': '#dc3545',    # Red
            'mastered': '#007bff',      # Blue
        }
        color = colors.get(obj.flag, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_flag_display()
        )
    flag_display.short_description = 'Flag'
