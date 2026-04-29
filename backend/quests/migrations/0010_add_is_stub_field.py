# Generated migration to add is_stub field for reliable stub detection

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quests', '0009_rename_quests_quest_celery_task_id_idx_quests_ques_celery__c1e7e4_idx'),
    ]

    operations = [
        # Add is_stub flag to Quest for reliable stub detection
        migrations.AddField(
            model_name='quest',
            name='is_stub',
            field=models.BooleanField(default=False, help_text='True if quest is auto-generated stub awaiting content'),
        ),
        
        # Add index on is_stub for faster stub detection
        migrations.AddIndex(
            model_name='quest',
            index=models.Index(fields=['is_stub', 'skill'], name='quest_stub_skill_idx'),
        ),
    ]
