from django.db import models
from quests.models import QuestSubmission

class DetectionLog(models.Model):
    """
    Detailed logs for AI-assisted plagiarism and integrity checks.
    """
    submission = models.ForeignKey(QuestSubmission, on_delete=models.CASCADE, related_name='detection_logs')
    embedding_score = models.FloatField(default=0.0)
    llm_score = models.FloatField(default=0.0)
    heuristic_score = models.FloatField(default=0.0)
    final_score = models.FloatField(default=0.0)
    llm_reasoning = models.JSONField(default=dict)  # Detailed breakdown of LLM decision
    analyzed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-analyzed_at']

    def __str__(self):
        return f"Detection Log for Submission #{self.submission.id} (Score: {self.final_score})"