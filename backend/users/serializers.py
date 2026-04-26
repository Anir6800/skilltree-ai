from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import XPLog
from quests.serializers import QuestListSerializer

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    rank = serializers.IntegerField(read_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'xp', 'level', 
            'streak_days', 'last_active', 'role', 'avatar_url', 'rank',
            'is_staff', 'is_superuser'
        ]

class XPLogSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(source='created_at', format='%Y-%m-%d')
    
    class Meta:
        model = XPLog
        fields = ['date', 'amount']

class DashboardSerializer(serializers.Serializer):
    user = UserProfileSerializer()
    xp_history = serializers.ListField(child=serializers.DictField())
    active_quests = QuestListSerializer(many=True)
    top_leaderboard = serializers.ListField(child=serializers.DictField())
    skills_progress = serializers.DictField()
