"""
Executor Domain Models — SkillTree AI
=======================================
ExecutionTask — Async Celery task record for code execution jobs.
"""

from django.db import models
from quests.models import QuestSubmission


class ExecutionTask(models.Model):
    """
    Tracks an async code execution Celery task.

    Lifecycle: queued → processing → completed | failed

    task_id maps 1:1 to a Celery task UUID. The unique constraint prevents
    duplicate task records for the same Celery task.

    worker_node — identifies the Celery worker hostname that picked up the task.
    Used for worker health monitoring and debugging.

    Duration = finished_at - started_at (both nullable until the task runs).
    """
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    submission = models.ForeignKey(
        QuestSubmission,
        on_delete=models.CASCADE,
        related_name='execution_tasks',
    )
    task_id = models.CharField(max_length=100, unique=True, help_text='Celery task UUID')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    worker_node = models.CharField(max_length=100, blank=True, default='')
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            # "what tasks are in-flight for submission X?"
            models.Index(fields=['submission', 'status'], name='exectask_submission_status_idx'),
            # Task lookup by Celery ID (unique constraint also creates an index,
            # but an explicit named index gives us stable migration references)
            models.Index(fields=['task_id'], name='exectask_task_id_idx'),
            # Worker monitoring: "what is worker Y currently processing?"
            models.Index(fields=['worker_node', 'status'], name='exectask_worker_status_idx'),
            # Recency
            models.Index(fields=['-created_at'], name='exectask_created_at_idx'),
        ]

    def __str__(self):
        return f"Task {self.task_id} for Submission #{self.submission_id} ({self.status})"
