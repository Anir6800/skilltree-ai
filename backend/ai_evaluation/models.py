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


class StyleReport(models.Model):
    """
    Code style analysis report for passed quest submissions.
    Generated after quest passes to provide style and readability feedback.
    """
    submission = models.OneToOneField(QuestSubmission, on_delete=models.CASCADE, related_name='style_report')
    readability_score = models.IntegerField(default=0, help_text='0-10 readability score')
    naming_quality = models.TextField(blank=True, default='', help_text='Assessment of naming quality')
    idiomatic_patterns = models.TextField(blank=True, default='', help_text='Assessment of idiomatic patterns')
    style_issues = models.JSONField(default=list, help_text='List of style issues with suggestions')
    positive_patterns = models.JSONField(default=list, help_text='List of positive patterns found')
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['submission']),
            models.Index(fields=['-generated_at']),
        ]

    def __str__(self):
        return f"Style Report for Submission #{self.submission.id} (Score: {self.readability_score}/10)"
