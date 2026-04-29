# Generated migration to add depth tracking fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('skills', '0006_populate_skills'),
    ]

    operations = [
        # Add depth field to GeneratedSkillTree
        migrations.AddField(
            model_name='generatedskilltree',
            name='depth',
            field=models.IntegerField(default=3, help_text='Tree depth (1-5) used during generation'),
        ),
        
        # Add tree_depth field to Skill for tracking hierarchy level
        migrations.AddField(
            model_name='skill',
            name='tree_depth',
            field=models.IntegerField(default=0, help_text='Depth level in the generated tree (0=root)'),
        ),
        
        # Add quest_completion_count to SkillProgress
        migrations.AddField(
            model_name='skillprogress',
            name='quest_completion_count',
            field=models.IntegerField(default=0, help_text='Number of quests completed for this skill'),
        ),
        
        # Add time_spent_minutes to SkillProgress
        migrations.AddField(
            model_name='skillprogress',
            name='time_spent_minutes',
            field=models.IntegerField(default=0, help_text='Total time spent on this skill'),
        ),
        
        # Add attempts_count to SkillProgress
        migrations.AddField(
            model_name='skillprogress',
            name='attempts_count',
            field=models.IntegerField(default=0, help_text='Number of quest attempts for this skill'),
        ),
        
        # Add index on tree_depth for hierarchy queries
        migrations.AddIndex(
            model_name='skill',
            index=models.Index(fields=['tree_depth'], name='skill_depth_idx'),
        ),
    ]
