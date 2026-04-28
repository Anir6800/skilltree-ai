"""
Django migration for SharedSolution and SolutionComment models.
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('quests', '0004_alter_questsubmission_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='SharedSolution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shared_at', models.DateTimeField(auto_now_add=True)),
                ('views_count', models.IntegerField(default=0)),
                ('is_anonymous', models.BooleanField(default=False)),
                ('submission', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='shared_solution', to='quests.questsubmission')),
                ('upvotes', models.ManyToManyField(blank=True, related_name='upvoted_solutions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-shared_at'],
            },
        ),
        migrations.CreateModel(
            name='SolutionComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(max_length=1000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='solution_comments', to=settings.AUTH_USER_MODEL)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='quests.solutioncomment')),
                ('solution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='quests.sharedsolution')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),

        migrations.AddIndex(
            model_name='sharedsolution',
            index=models.Index(fields=['-shared_at'], name='quests_shar_shared_idx'),
        ),
        migrations.AddIndex(
            model_name='solutioncomment',
            index=models.Index(fields=['solution', 'created_at'], name='quests_solu_solutio_idx'),
        ),
        migrations.AddIndex(
            model_name='solutioncomment',
            index=models.Index(fields=['author'], name='quests_solu_author_idx'),
        ),
    ]
