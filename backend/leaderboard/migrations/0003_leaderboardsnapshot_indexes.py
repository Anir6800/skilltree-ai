# Schema fix: add composite index on (user, snapshot_at) for efficient
# per-user history queries, and a standalone index on snapshot_at for
# global leaderboard range scans.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leaderboard', '0002_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='leaderboardsnapshot',
            index=models.Index(fields=['user', 'snapshot_at'], name='leaderboard_user_snap_idx'),
        ),
        migrations.AddIndex(
            model_name='leaderboardsnapshot',
            index=models.Index(fields=['-snapshot_at'], name='leaderboard_snap_at_idx'),
        ),
    ]
