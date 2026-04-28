"""
SkillTree AI - AI Evaluation Serializers
Serializers for evaluation results and style reports.
"""

from rest_framework import serializers
from ai_evaluation.models import StyleReport
from quests.models import QuestSubmission  # Used by StyleReportSerializer via submission FK


class StyleReportSerializer(serializers.ModelSerializer):
    """Serializer for StyleReport model."""

    submission_id = serializers.IntegerField(source='submission.id', read_only=True)
    quest_title = serializers.CharField(source='submission.quest.title', read_only=True)
    language = serializers.CharField(source='submission.language', read_only=True)

    class Meta:
        model = StyleReport
        fields = [
            'id',
            'submission_id',
            'quest_title',
            'language',
            'readability_score',
            'naming_quality',
            'idiomatic_patterns',
            'style_issues',
            'positive_patterns',
            'generated_at'
        ]
        read_only_fields = [
            'id',
            'submission_id',
            'quest_title',
            'language',
            'readability_score',
            'naming_quality',
            'idiomatic_patterns',
            'style_issues',
            'positive_patterns',
            'generated_at'
        ]
