from rest_framework import serializers
from .models import Skill, SkillProgress

class SkillSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for Skill nodes.
    """
    status = serializers.SerializerMethodField()

    class Meta:
        model = Skill
        fields = ['id', 'title', 'description', 'category', 'difficulty', 'xp_required_to_unlock', 'status']

    def get_status(self, obj):
        user = self.context.get('request').user
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
