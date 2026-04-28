"""
Migration: Add HintUsage model for tiered hint system
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mentor', '0001_initial'),
        ('quests', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HintUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hint_level', models.IntegerField(choices=[(1, 'Nudge'), (2, 'Approach'), (3, 'Near-Solution')])),
                ('hint_text', models.TextField()),
                ('xp_penalty', models.IntegerField(default=0)),
                ('requested_at', models.DateTimeField(auto_now_add=True)),
                ('quest', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hint_usages', to='quests.quest')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hint_usages', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-requested_at'],
            },
        ),
        migrations.AddIndex(
            model_name='hintusage',
            index=models.Index(fields=['user', 'quest'], name='mentor_hintusage_user_quest_idx'),
        ),
        migrations.AddIndex(
            model_name='hintusage',
            index=models.Index(fields=['user', 'requested_at'], name='mentor_hintusage_user_requested_idx'),
        ),
    ]
