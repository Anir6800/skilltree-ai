"""
Migration: Add AdaptiveProfile and UserSkillFlag models
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('skills', '0003_usercurriculum'),
        ('users', '0004_merge_20260427_1226'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdaptiveProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ability_score', models.FloatField(default=0.5, help_text='0.0 (struggling) to 1.0 (advanced), updated via Bayesian formula')),
                ('preferred_difficulty', models.IntegerField(default=3, help_text='Auto-set to ceil(ability_score * 5), range 1-5')),
                ('adjustment_history', models.JSONField(default=list, help_text='Log of every adjustment with timestamp and reason')),
                ('last_adjusted', models.DateTimeField(auto_now=True, help_text='Timestamp of last adaptation')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='adaptive_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Adaptive Profile',
                'verbose_name_plural': 'Adaptive Profiles',
            },
        ),
        migrations.CreateModel(
            name='UserSkillFlag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('flag', models.CharField(choices=[('too_easy', 'Too Easy'), ('struggling', 'Struggling'), ('mastered', 'Mastered')], help_text='Type of flag (too_easy, struggling, mastered)', max_length=20)),
                ('reason', models.TextField(blank=True, default='', help_text='Reason for flagging (e.g., "Consecutive failures: 3")')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('skill', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_flags', to='skills.skill')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='skill_flags', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Skill Flag',
                'verbose_name_plural': 'User Skill Flags',
            },
        ),
        migrations.AddIndex(
            model_name='adaptiveprofile',
            index=models.Index(fields=['user'], name='users_adapt_user_id_idx'),
        ),
        migrations.AddIndex(
            model_name='adaptiveprofile',
            index=models.Index(fields=['ability_score'], name='users_adapt_ability_idx'),
        ),
        migrations.AddIndex(
            model_name='adaptiveprofile',
            index=models.Index(fields=['preferred_difficulty'], name='users_adapt_diff_idx'),
        ),
        migrations.AddIndex(
            model_name='userskillflag',
            index=models.Index(fields=['user', 'flag'], name='users_userskill_user_flag_idx'),
        ),
        migrations.AddIndex(
            model_name='userskillflag',
            index=models.Index(fields=['skill', 'flag'], name='users_userskill_skill_flag_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='userskillflag',
            unique_together={('user', 'skill', 'flag')},
        ),
    ]
