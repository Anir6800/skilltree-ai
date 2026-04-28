"""
Migration to add StyleReport model.
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('quests', '0001_initial'),
        ('ai_evaluation', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StyleReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('readability_score', models.IntegerField(default=0, help_text='0-10 readability score')),
                ('naming_quality', models.TextField(blank=True, default='', help_text='Assessment of naming quality')),
                ('idiomatic_patterns', models.TextField(blank=True, default='', help_text='Assessment of idiomatic patterns')),
                ('style_issues', models.JSONField(default=list, help_text='List of style issues with suggestions')),
                ('positive_patterns', models.JSONField(default=list, help_text='List of positive patterns found')),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('submission', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='style_report', to='quests.questsubmission')),
            ],
            options={
                'ordering': ['-generated_at'],
            },
        ),
        migrations.AddIndex(
            model_name='stylereport',
            index=models.Index(fields=['submission'], name='ai_evaluati_submiss_idx'),
        ),
        migrations.AddIndex(
            model_name='stylereport',
            index=models.Index(fields=['-generated_at'], name='ai_evaluati_generated_idx'),
        ),
    ]
