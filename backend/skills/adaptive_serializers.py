"""
SkillTree AI - Adaptive Profile Serializers
REST API serialization for adaptive learning data.
"""

from rest_framework import serializers
from users.models_adaptive import AdaptiveProfile, UserSkillFlag
from skills.models import Skill


class UserSkillFlagSerializer(serializers.ModelSerializer):
    """Serializer for user skill flags."""
    skill_id = serializers.IntegerField(source='skill.id', read_only=True)
    skill_title = serializers.CharField(source='skill.title', read_only=True)
    skill_difficulty = serializers.IntegerField(source='skill.difficulty', read_only=True)

    class Meta:
        model = UserSkillFlag
        fields = ['skill_id', 'skill_title', 'skill_difficulty', 'flag', 'reason', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class AdaptiveProfileSerializer(serializers.ModelSerializer):
    """Serializer for adaptive profile with flags."""
    flags = serializers.SerializerMethodField()
    adjustment_history_summary = serializers.SerializerMethodField()

    class Meta:
        model = AdaptiveProfile
        fields = [
            'ability_score',
            'preferred_difficulty',
            'flags',
            'last_adjusted',
            'adjustment_history_summary',
        ]
        read_only_fields = ['ability_score', 'preferred_difficulty', 'last_adjusted']

    def get_flags(self, obj) -> list:
        """Get all flags for this user."""
        flags = UserSkillFlag.objects.filter(user=obj.user)
        return UserSkillFlagSerializer(flags, many=True).data

    def get_adjustment_history_summary(self, obj) -> dict:
        """Get summary of recent adjustments."""
        if not obj.adjustment_history:
            return {'total_adjustments': 0, 'recent': []}

        recent = obj.adjustment_history[-5:] if len(obj.adjustment_history) > 5 else obj.adjustment_history
        return {
            'total_adjustments': len(obj.adjustment_history),
            'recent': recent,
        }
