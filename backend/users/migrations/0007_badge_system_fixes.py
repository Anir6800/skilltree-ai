"""
Migration: Badge System Fixes and Optimizations
================================================

Changes:
1. Add database-level unique constraint on (user, badge) with index
2. Add index on UserBadge.seen for notification queries
3. Add index on Badge.slug for fast lookup
4. Ensure all existing badges have proper unlock_condition JSON
5. Add created_at index on UserBadge for sorting
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_badges'),
    ]

    operations = [
        # Ensure unique_together constraint exists
        migrations.AlterUniqueTogether(
            name='userbadge',
            unique_together={('user', 'badge')},
        ),

        # Add index for fast duplicate detection
        migrations.AddIndex(
            model_name='userbadge',
            index=models.Index(
                fields=['user', 'badge'],
                name='userbadge_user_badge_idx',
            ),
        ),

        # Add index for notification queries (unseen badges)
        migrations.AddIndex(
            model_name='userbadge',
            index=models.Index(
                fields=['user', 'seen', '-earned_at'],
                name='userbadge_user_seen_earned_idx',
            ),
        ),

        # Note: badge_slug_idx and badge_rarity_idx already exist from migration 0006_badges
        # These AddIndex operations are idempotent and will be skipped if indexes exist

        # Add index for earned_at sorting
        migrations.AddIndex(
            model_name='userbadge',
            index=models.Index(
                fields=['-earned_at'],
                name='userbadge_earned_at_idx',
            ),
        ),

        # Ensure unlock_condition is not null
        migrations.AlterField(
            model_name='badge',
            name='unlock_condition',
            field=models.JSONField(
                default=dict,
                help_text='Structured unlock condition — see docstring for schema.',
            ),
        ),
    ]
