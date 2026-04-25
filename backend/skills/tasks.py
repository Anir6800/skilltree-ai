"""
SkillTree AI - Skills Tasks
Re-exports Celery tasks from services so autodiscover_tasks() can find them.
"""

# Import the shared_task so Celery registers it under 'skills.tasks'
from skills.services import resolve_unlocks_for_user  # noqa: F401
