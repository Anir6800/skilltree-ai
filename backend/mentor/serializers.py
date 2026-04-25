"""
AI Mentor Serializers
Request/response validation for mentor chat and path suggestions.
"""

from rest_framework import serializers
from .models import AIInteraction


class ChatRequestSerializer(serializers.Serializer):
    """Validate chat request from frontend."""
    message = serializers.CharField(max_length=2000, required=True)
    context_skill_id = serializers.IntegerField(required=False, allow_null=True)
    context_quest_id = serializers.IntegerField(required=False, allow_null=True)
    
    def validate_message(self, value):
        """Ensure message is not empty after stripping."""
        if not value.strip():
            raise serializers.ValidationError("Message cannot be empty.")
        return value.strip()


class ChatResponseSerializer(serializers.Serializer):
    """Format chat response."""
    response = serializers.CharField()
    tokens_used = serializers.IntegerField()
    interaction_id = serializers.IntegerField()


class SuggestedSkillSerializer(serializers.Serializer):
    """Format suggested skill data."""
    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField()
    category = serializers.CharField()
    difficulty = serializers.IntegerField()
    xp_required = serializers.IntegerField()
    reason = serializers.CharField()


class PathSuggestionResponseSerializer(serializers.Serializer):
    """Format path suggestion response."""
    suggested_skills = SuggestedSkillSerializer(many=True)
    reasoning = serializers.CharField()
    current_level = serializers.CharField()


class AIInteractionSerializer(serializers.ModelSerializer):
    """Serialize AI interaction history."""
    class Meta:
        model = AIInteraction
        fields = ['id', 'interaction_type', 'context_prompt', 'response', 'tokens_used', 'created_at']
        read_only_fields = ['id', 'created_at']
