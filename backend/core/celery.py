"""
SkillTree AI - Celery Configuration
Async task processing for AI evaluation and skill tree updates.
"""

import os
import sys
from celery import Celery

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
])


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f'Request: {self.request!r}')
