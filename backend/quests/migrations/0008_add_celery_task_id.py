# Generated migration for adding celery_task_id field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quests', '0007_populate_quests'),
    ]

    operations = [
        migrations.AddField(
            model_name='questsubmission',
            name='celery_task_id',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
        migrations.AddIndex(
            model_name='questsubmission',
            index=models.Index(fields=['celery_task_id'], name='quests_quest_celery_task_id_idx'),
        ),
    ]
