from rest_framework import serializers
from .models import Quest, QuestSubmission

class QuestListSerializer(serializers.ModelSerializer):
    """
    Brief serializer for listing quests.
    """
    status = serializers.SerializerMethodField()

    class Meta:
        model = Quest
        fields = [
            'id', 'title', 'type', 'xp_reward', 
            'difficulty_multiplier', 'estimated_minutes', 'status'
        ]

    def get_status(self, obj):
        request = self.context.get('request')
        if not request:
            return 'not_started'
            
        user = request.user
        if not user or not user.is_authenticated:
            return 'not_started'
        
        submission = QuestSubmission.objects.filter(user=user, quest=obj).first()
        return submission.status if submission else 'not_started'

class QuestDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for a single quest.
    Hides expected output from test cases for security.
    """
    status = serializers.SerializerMethodField()
    test_cases = serializers.SerializerMethodField()

    class Meta:
        model = Quest
        fields = [
            'id', 'title', 'description', 'type', 'starter_code', 
            'test_cases', 'xp_reward', 'difficulty_multiplier', 
            'estimated_minutes', 'status'
        ]

    def get_status(self, obj):
        user = self.context.get('request').user
        submission = QuestSubmission.objects.filter(user=user, quest=obj).first()
        return submission.status if submission else 'not_started'

    def get_test_cases(self, obj):
        # Remove 'expected_output' to prevent cheating
        return [{"input": tc.get("input")} for tc in obj.test_cases]

class QuestSubmissionSerializer(serializers.ModelSerializer):
    """
    Serializer for quest attempts.
    """
    class Meta:
        model = QuestSubmission
        fields = ['id', 'quest', 'code', 'language', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']
