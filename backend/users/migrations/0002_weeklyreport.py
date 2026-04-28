"""
Migration to add WeeklyReport model.
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='WeeklyReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week_number', models.IntegerField(help_text='ISO week number (1-53)')),
                ('year', models.IntegerField(default=2026)),
                ('pdf_path', models.CharField(help_text='Path to generated PDF file', max_length=500)),
                ('data', models.JSONField(default=dict, help_text='Collected metrics for the week')),
                ('narrative', models.JSONField(default=dict, help_text='AI-generated narrative sections')),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('viewed_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='weekly_reports', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-generated_at'],
            },
        ),
        migrations.AddIndex(
            model_name='weeklyreport',
            index=models.Index(fields=['user', '-generated_at'], name='users_weekl_user_id_generated_idx'),
        ),
        migrations.AddIndex(
            model_name='weeklyreport',
            index=models.Index(fields=['week_number', 'year'], name='users_weekl_week_nu_year_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='weeklyreport',
            unique_together={('user', 'week_number', 'year')},
        ),
    ]
