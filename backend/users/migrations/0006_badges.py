"""
Migration: Add Badge and UserBadge models
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_adaptive_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='Badge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('icon_emoji', models.CharField(max_length=10)),
                ('rarity', models.CharField(choices=[('common', 'Common'), ('rare', 'Rare'), ('epic', 'Epic'), ('legendary', 'Legendary')], default='common', max_length=20)),
                ('unlock_condition', models.JSONField(default=dict, help_text='Condition to unlock badge: {event_type, criteria}')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['rarity', 'name'],
            },
        ),
        migrations.CreateModel(
            name='UserBadge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('earned_at', models.DateTimeField(auto_now_add=True)),
                ('seen', models.BooleanField(default=False)),
                ('badge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_badges', to='users.badge')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='badges', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-earned_at'],
                'unique_together': {('user', 'badge')},
            },
        ),
        migrations.AddIndex(
            model_name='badge',
            index=models.Index(fields=['slug'], name='users_badge_slug_idx'),
        ),
        migrations.AddIndex(
            model_name='badge',
            index=models.Index(fields=['rarity'], name='users_badge_rarity_idx'),
        ),
        migrations.AddIndex(
            model_name='userbadge',
            index=models.Index(fields=['user', 'seen'], name='users_userbadge_user_seen_idx'),
        ),
        migrations.AddIndex(
            model_name='userbadge',
            index=models.Index(fields=['badge'], name='users_userbadge_badge_idx'),
        ),
    ]
