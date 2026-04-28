"""
SkillTree AI - Celery Configuration
Async task processing for AI evaluation and skill tree updates.
"""

import os
import sys
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('skilltree_ai')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Windows-specific configuration
# Use solo pool on Windows to avoid multiprocessing issues
if sys.platform == 'win32':
    app.conf.update(
        worker_pool='solo',
        worker_concurrency=1,
    )

# Load task modules from all registered Django apps.
# Explicitly list apps with tasks to ensure they're discovered
app.autodiscover_tasks([
    'skills',
    'ai_evaluation',
    'executor',
    'quests',
    'users',
    'admin_panel',
    'multiplayer',
    'leaderboard',
])

# Celery Beat periodic schedule
app.conf.beat_schedule = {
    # Snapshot Redis rankings to DB every 5 minutes
    'snapshot-leaderboard-every-5-minutes': {
        'task': 'leaderboard.tasks.snapshot_leaderboard',
        'schedule': 300.0,  # seconds
    },
    # Reset weekly leaderboard every Monday at 00:00 UTC
    'reset-weekly-leaderboard-monday': {
        'task': 'leaderboard.tasks.reset_weekly',
        'schedule': crontab(hour=0, minute=0, day_of_week='monday'),
    },
    # Periodic tree adaptation every 24 hours at 02:00 UTC
    'periodic-tree-adaptation-daily': {
        'task': 'skills.adaptive_tasks.periodic_tree_adaptation',
        'schedule': crontab(hour=2, minute=0),
    },
    # Generate weekly reports every Monday at 08:00 UTC
    'generate-weekly-reports-monday': {
        'task': 'users.tasks.generate_weekly_reports_for_all_users',
        'schedule': crontab(hour=8, minute=0, day_of_week='monday'),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f'Request: {self.request!r}')
