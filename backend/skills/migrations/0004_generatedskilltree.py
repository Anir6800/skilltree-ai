"""
Migration to add GeneratedSkillTree model for AI-powered skill tree generation.
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('skills', '0003_usercurriculum'),
    ]

    operations = [
        migrations.CreateModel(
            name='GeneratedSkillTree',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('topic', models.CharField(max_length=200)),
                ('is_public', models.BooleanField(default=False)),
                ('raw_ai_response', models.JSONField(default=dict)),
                ('status', models.CharField(choices=[('generating', 'Generating'), ('ready', 'Ready'), ('failed', 'Failed')], default='generating', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='generated_trees', to=settings.AUTH_USER_MODEL)),
                ('skills_created', models.ManyToManyField(blank=True, related_name='generated_from_trees', to='skills.skill')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='generatedskilltree',
            index=models.Index(fields=['created_by', 'status'], name='skills_gene_created_idx'),
        ),
        migrations.AddIndex(
            model_name='generatedskilltree',
            index=models.Index(fields=['is_public', 'status'], name='skills_gene_is_publ_idx'),
        ),
    ]
