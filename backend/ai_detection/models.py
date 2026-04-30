"""
AI Detection Domain Models — SkillTree AI
==========================================
DetectionLog — Per-submission AI-generation detection analysis record.
"""

from django.db import models
from quests.models import QuestSubmission


class DetectionLog(models.Model):
    """
    Detailed per-submission AI detection analysis result.

    Scores range 0.0–1.0 (higher = more likely AI-generated).
    final_score is the weighted combination of the three sub-scores.

    A submission can have multiple DetectionLogs if re-analyzed
    (e.g. after an appeal or model update). Use the latest analyzed_at.

    llm_reasoning JSON structure:
        {
            "explanation": str,
            "patterns_found": [str],
            "confidence": float
        }
    """

    submission = models.ForeignKey(
        QuestSubmission,
        on_delete=models.CASCADE,
        related_name='detection_logs',
    )
    embedding_score = models.FloatField(default=0.0, help_text='Vector similarity score (0-1)')
    llm_score = models.FloatField(default=0.0, help_text='LLM-based detection score (0-1)')
    heuristic_score = models.FloatField(default=0.0, help_text='Rule-based heuristic score (0-1)')
    final_score = models.FloatField(default=0.0, help_text='Weighted combination (0-1)')
    llm_reasoning = models.JSONField(default=dict, help_text='Detailed LLM decision breakdown')
    analyzed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-analyzed_at']
        indexes = [
            # "latest detection analysis for submission X"
            models.Index(fields=['submission', '-analyzed_at'], name='detectionlog_submission_idx'),
            # Batch review: "all high-score detections in the last 30 days"
            models.Index(fields=['final_score', '-analyzed_at'], name='detectionlog_score_idx'),
        ]

    def __str__(self):
        return f"Detection#{self.id} for Submission#{self.submission_id} (score={self.final_score:.2f})"