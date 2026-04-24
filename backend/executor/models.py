from django.db import models
from quests.models import QuestSubmission

class ExecutionTask(models.Model):
    """
    Asynchronous execution task for code validation.
    """
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    submission = models.ForeignKey(QuestSubmission, on_delete=models.CASCADE, related_name='execution_tasks')
    task_id = models.CharField(max_length=100, unique=True)  # Celery task ID
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    worker_node = models.CharField(max_length=100, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Task {self.task_id} for Submission #{self.submission.id}"
