from rest_framework import serializers
from .models import Skill, SkillProgress, GeneratedSkillTree

class SkillSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for Skill nodes.
    """
    status = serializers.SerializerMethodField()

    class Meta:
        model = Skill
        fields = ['id', 'title', 'description', 'category', 'difficulty', 'xp_required_to_unlock', 'status']

    def get_status(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return 'locked'
        
        try:
            progress = SkillProgress.objects.get(user=user, skill=obj)
            return progress.status
        except SkillProgress.DoesNotExist:
            # Check if prerequisites are met
            unmet_prereqs = obj.prerequisites.exclude(
                user_progress__user=user, 
                user_progress__status='completed'
            ).exists()
            
            if not unmet_prereqs and user.xp >= obj.xp_required_to_unlock:
                return 'available'
            return 'locked'

class SkillProgressSerializer(serializers.ModelSerializer):
    """
    Serializer for tracking user's journey through a skill.
    """
    class Meta:
        model = SkillProgress
        fields = ['id', 'skill', 'status', 'completed_at']
        read_only_fields = ['id', 'completed_at']


class GeneratedSkillTreeSerializer(serializers.ModelSerializer):
    """
    Serializer for AI-generated skill trees.
    """
    skills_count = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = GeneratedSkillTree
        fields = [
            'id', 'topic', 'created_by', 'created_by_username', 'is_public',
            'status', 'skills_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'status', 'created_at', 'updated_at']
    
    def get_skills_count(self, obj):
        return obj.skills_created.count()


class GeneratedSkillTreeDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for AI-generated skill trees with full skill data.
    """
    skills = SkillSerializer(source='skills_created', many=True, read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = GeneratedSkillTree
        fields = [
            'id', 'topic', 'created_by', 'created_by_username', 'is_public',
            'status', 'skills', 'raw_ai_response', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_by', 'status', 'skills', 'raw_ai_response',
            'created_at', 'updated_at'
        ]
