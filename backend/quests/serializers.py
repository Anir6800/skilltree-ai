from rest_framework import serializers
from .models import Quest, QuestSubmission

class QuestListSerializer(serializers.ModelSerializer):
    """
    Brief serializer for listing quests.
    """
    status = serializers.SerializerMethodField()
    skill_name = serializers.CharField(source='skill.title', read_only=True)

    class Meta:
        model = Quest
        fields = [
            'id', 'title', 'type', 'description', 'xp_reward', 
            'difficulty_multiplier', 'estimated_minutes', 'status', 'skill_name'
        ]

    def get_status(self, obj):
        request = self.context.get('request')
        if not request:
            return 'not_started'
            
        user = request.user
        if not user or not user.is_authenticated:
            return 'not_started'
        
        # Check for passed submission first
        passed_submission = QuestSubmission.objects.filter(
            user=user, 
            quest=obj, 
            status='passed'
        ).first()
        
        if passed_submission:
            return 'passed'
        
        # Check for in-progress submission
        in_progress_submission = QuestSubmission.objects.filter(
            user=user, 
            quest=obj, 
            status__in=['pending', 'running']
        ).first()
        
        if in_progress_submission:
            return 'in_progress'
        
        return 'not_started'

class QuestDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for a single quest.
    Hides expected output from test cases for security.
    """
    status = serializers.SerializerMethodField()
    test_cases = serializers.SerializerMethodField()
    skill_name = serializers.CharField(source='skill.title', read_only=True)

    class Meta:
        model = Quest
        fields = [
            'id', 'title', 'description', 'type', 'starter_code', 
            'test_cases', 'xp_reward', 'difficulty_multiplier', 
            'estimated_minutes', 'status', 'skill_name'
        ]

    def get_status(self, obj):
        request = self.context.get('request')
        if not request:
            return 'not_started'
            
        user = request.user
        if not user or not user.is_authenticated:
            return 'not_started'
        
        # Check for passed submission first
        passed_submission = QuestSubmission.objects.filter(
            user=user, 
            quest=obj, 
            status='passed'
        ).first()
        
        if passed_submission:
            return 'passed'
        
        # Check for in-progress submission
        in_progress_submission = QuestSubmission.objects.filter(
            user=user, 
            quest=obj, 
            status__in=['pending', 'running']
        ).first()
        
        if in_progress_submission:
            return 'in_progress'
        
        return 'not_started'

    def get_test_cases(self, obj):
        # Remove 'expected_output' to prevent cheating
        return [{"input": tc.get("input")} for tc in obj.test_cases]

class QuestSubmissionSerializer(serializers.ModelSerializer):
    """
    Serializer for quest attempts.
    """
    quest_title = serializers.CharField(source='quest.title', read_only=True)
    
    class Meta:
        model = QuestSubmission
        fields = [
            'id', 'quest', 'quest_title', 'code', 'language', 
            'status', 'execution_result', 'ai_feedback', 
            'ai_detection_score', 'created_at'
        ]
        read_only_fields = [
            'id', 'status', 'execution_result', 'ai_feedback', 
            'ai_detection_score', 'created_at'
        ]
