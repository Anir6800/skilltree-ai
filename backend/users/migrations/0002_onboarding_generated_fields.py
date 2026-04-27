# Generated migration for onboarding generated fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='onboardingprofile',
            name='generated_tree_id',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='onboardingprofile',
            name='generated_topic',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
    ]
