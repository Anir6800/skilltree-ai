"""
Onboarding Serializers
Request/response validation for onboarding flow.
"""

from rest_framework import serializers
from .onboarding_models import OnboardingProfile


class OnboardingSubmitSerializer(serializers.Serializer):
    """Validate onboarding submission."""
    primary_goal = serializers.ChoiceField(
        choices=['job_prep', 'interview', 'upskill', 'passion'],
        required=True
    )
    target_role = serializers.CharField(max_length=200, required=True)
    experience_years = serializers.IntegerField(min_value=0, max_value=50, required=True)
    category_levels = serializers.JSONField(required=True)
    selected_interests = serializers.ListField(
        child=serializers.CharField(max_length=100),
        min_length=2,
        required=True
    )
    weekly_hours = serializers.IntegerField(min_value=1, max_value=40, required=True)
    
    def validate_category_levels(self, value):
        """Validate category levels structure."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("category_levels must be a dictionary")
        
        valid_categories = ['algorithms', 'ds', 'systems', 'webdev', 'aiml']
        valid_levels = ['beginner', 'intermediate', 'advanced']
        
        for category, level in value.items():
            if category not in valid_categories:
                raise serializers.ValidationError(f"Invalid category: {category}")
            if level not in valid_levels:
                raise serializers.ValidationError(f"Invalid level: {level}")
        
        return value
    
    def validate_selected_interests(self, value):
        """Validate selected interests."""
        if len(value) < 2:
            raise serializers.ValidationError("Select at least 2 interests")
        if len(value) > 20:
            raise serializers.ValidationError("Maximum 20 interests allowed")
        return value


class OnboardingProfileSerializer(serializers.ModelSerializer):
    """Serialize onboarding profile."""
    class Meta:
        model = OnboardingProfile
        fields = [
            'id',
            'primary_goal',
            'target_role',
            'experience_years',
            'category_levels',
            'selected_interests',
            'weekly_hours',
            'completed_at',
            'path_generated',
            'generated_tree_id',
            'generated_topic'
        ]
        read_only_fields = ['id', 'completed_at']


class OnboardingStatusSerializer(serializers.Serializer):
    """Serialize onboarding status response."""
    completed = serializers.BooleanField()
    profile = OnboardingProfileSerializer(allow_null=True)
    path_generated = serializers.BooleanField()
