from django.db import models
from quests.models import QuestSubmission

class EvaluationResult(models.Model):
    """
    Detailed AI evaluation results for specific quest submissions.
    """
    submission = models.OneToOneField(QuestSubmission, on_delete=models.CASCADE, related_name='detailed_evaluation')
    score = models.FloatField(default=0.0)
    summary = models.TextField(blank=True, default='')
    pros = models.JSONField(default=list)
    cons = models.JSONField(default=list)
    suggestions = models.JSONField(default=list)
    evaluated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-evaluated_at']

    def __str__(self):
        return f"Evaluation for Submission #{self.submission.id} (Score: {self.score})"