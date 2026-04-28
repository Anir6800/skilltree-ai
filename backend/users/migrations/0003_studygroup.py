"""
Django migration for StudyGroup models.
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('skills', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0002_weeklyreport'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudyGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('invite_code', models.CharField(db_index=True, max_length=6, unique=True)),
                ('max_members', models.IntegerField(default=6)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_groups', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='StudyGroupMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('owner', 'Owner'), ('member', 'Member')], default='member', max_length=20)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='users.studygroup')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='study_groups', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-joined_at'],
                'unique_together': {('group', 'user')},
            },
        ),
        migrations.CreateModel(
            name='StudyGroupMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='users.studygroup')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_messages', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['sent_at'],
            },
        ),
        migrations.CreateModel(
            name='StudyGroupGoal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('target_date', models.DateField()),
                ('completed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='goals', to='users.studygroup')),
                ('skill', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_goals', to='skills.skill')),
            ],
            options={
                'ordering': ['target_date'],
                'unique_together': {('group', 'skill')},
            },
        ),
        migrations.AddIndex(
            model_name='studygroup',
            index=models.Index(fields=['invite_code'], name='users_study_invite__idx'),
        ),
        migrations.AddIndex(
            model_name='studygroup',
            index=models.Index(fields=['created_by'], name='users_study_created__idx'),
        ),
        migrations.AddIndex(
            model_name='studygroupmembership',
            index=models.Index(fields=['group', 'user'], name='users_study_group_u_idx'),
        ),
        migrations.AddIndex(
            model_name='studygroupmembership',
            index=models.Index(fields=['user'], name='users_study_user_idx'),
        ),
        migrations.AddIndex(
            model_name='studygroupmessage',
            index=models.Index(fields=['group', 'sent_at'], name='users_study_group_s_idx'),
        ),
        migrations.AddIndex(
            model_name='studygroupmessage',
            index=models.Index(fields=['sender'], name='users_study_sender_idx'),
        ),
        migrations.AddIndex(
            model_name='studygroupgoal',
            index=models.Index(fields=['group', 'target_date'], name='users_study_group_t_idx'),
        ),
        migrations.AddIndex(
            model_name='studygroupgoal',
            index=models.Index(fields=['skill'], name='users_study_skill_idx'),
        ),
    ]
