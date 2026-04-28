"""
SkillTree AI - Badge Admin Configuration
Django admin interface for badge management.
"""

from django.contrib import admin
from django.utils.html import format_html
from users.models import Badge, UserBadge


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    """Admin interface for Badge model."""
    list_display = ['badge_display', 'name', 'rarity', 'unlock_count']
    list_filter = ['rarity', 'created_at']
    search_fields = ['name', 'slug', 'description']
    readonly_fields = ['created_at', 'unlock_condition_display']

    fieldsets = (
        ('Badge Info', {
            'fields': ('slug', 'name', 'icon_emoji', 'description'),
        }),
        ('Rarity & Unlock', {
            'fields': ('rarity', 'unlock_condition_display'),
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    def badge_display(self, obj):
        """Display badge with emoji and name."""
        return format_html(
            '<span style="font-size: 20px; margin-right: 8px;">{}</span> {}',
            obj.icon_emoji,
            obj.name
        )
    badge_display.short_description = 'Badge'

    def rarity_display(self, obj):
        """Display rarity with color coding."""
        colors = {
            'common': '#94a3b8',
            'rare': '#3b82f6',
            'epic': '#a855f7',
            'legendary': '#f59e0b',
        }
        color = colors.get(obj.rarity, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_rarity_display()
        )
    rarity_display.short_description = 'Rarity'

    def unlock_condition_display(self, obj):
        """Display unlock condition as formatted JSON."""
        import json
        return format_html(
            '<pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">{}</pre>',
            json.dumps(obj.unlock_condition, indent=2)
        )
    unlock_condition_display.short_description = 'Unlock Condition'

    def unlock_count(self, obj):
        """Display number of users who earned this badge."""
        count = obj.user_badges.count()
        return format_html(
            '<span style="background: #e3f2fd; padding: 4px 8px; border-radius: 4px;">{} users</span>',
            count
        )
    unlock_count.short_description = 'Earned By'


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    """Admin interface for UserBadge model."""
    list_display = ['user', 'badge_display', 'earned_at', 'seen_status']
    list_filter = ['badge__rarity', 'earned_at', 'seen']
    search_fields = ['user__username', 'badge__name']
    readonly_fields = ['earned_at']

    fieldsets = (
        ('Badge Assignment', {
            'fields': ('user', 'badge'),
        }),
        ('Status', {
            'fields': ('seen', 'earned_at'),
        }),
    )

    def badge_display(self, obj):
        """Display badge with emoji."""
        return format_html(
            '<span style="font-size: 18px; margin-right: 8px;">{}</span> {}',
            obj.badge.icon_emoji,
            obj.badge.name
        )
    badge_display.short_description = 'Badge'

    def seen_status(self, obj):
        """Display seen status with icon."""
        if obj.seen:
            return format_html(
                '<span style="color: #22c55e; font-weight: bold;">✓ Seen</span>'
            )
        else:
            return format_html(
                '<span style="color: #ef4444; font-weight: bold;">✕ New</span>'
            )
    seen_status.short_description = 'Status'

    actions = ['mark_as_seen', 'mark_as_unseen']

    def mark_as_seen(self, request, queryset):
        """Mark selected badges as seen."""
        count = queryset.update(seen=True)
        self.message_user(request, f'{count} badges marked as seen.')
    mark_as_seen.short_description = 'Mark selected as seen'

    def mark_as_unseen(self, request, queryset):
        """Mark selected badges as unseen."""
        count = queryset.update(seen=False)
        self.message_user(request, f'{count} badges marked as unseen.')
    mark_as_unseen.short_description = 'Mark selected as unseen'
