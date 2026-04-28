"""
SkillTree AI - User Serializers
Serializers for user-related models.
"""

from rest_framework import serializers
from users.models import User, WeeklyReport, StudyGroup, StudyGroupMembership, StudyGroupMessage, StudyGroupGoal
from quests.serializers import QuestListSerializer
from auth_app.serializers import UserProfileSerializer

class DashboardSerializer(serializers.Serializer):
    user = UserProfileSerializer()
    xp_history = serializers.ListField(child=serializers.DictField())
    active_quests = QuestListSerializer(many=True)
    top_leaderboard = serializers.ListField(child=serializers.DictField())
    skills_progress = serializers.DictField()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'xp', 'level', 'streak_days', 'avatar_url']
        read_only_fields = ['id', 'xp', 'level']


class WeeklyReportSerializer(serializers.ModelSerializer):
    """Serializer for WeeklyReport model."""

    user_username = serializers.CharField(source='user.username', read_only=True)
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = WeeklyReport
        fields = [
            'id',
            'user_username',
            'week_number',
            'year',
            'pdf_path',
            'pdf_url',
            'data',
            'narrative',
            'generated_at',
            'viewed_at'
        ]
        read_only_fields = [
            'id',
            'user_username',
            'pdf_path',
            'data',
            'narrative',
            'generated_at',
            'viewed_at'
        ]

    def get_pdf_url(self, obj):
        """Generate download URL for PDF."""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/reports/{obj.id}/download/')
        return None


class StudyGroupMemberSerializer(serializers.ModelSerializer):
    """Serializer for StudyGroupMembership with user details."""

    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    avatar_url = serializers.CharField(source='user.avatar_url', read_only=True)
    level = serializers.IntegerField(source='user.level', read_only=True)
    xp = serializers.IntegerField(source='user.xp', read_only=True)

    class Meta:
        model = StudyGroupMembership
        fields = ['user_id', 'username', 'avatar_url', 'level', 'xp', 'role', 'joined_at']
        read_only_fields = ['user_id', 'username', 'avatar_url', 'level', 'xp', 'role', 'joined_at']


class StudyGroupGoalSerializer(serializers.ModelSerializer):
    """Serializer for StudyGroupGoal with skill details."""

    skill_id = serializers.IntegerField(source='skill.id', read_only=True)
    skill_title = serializers.CharField(source='skill.title', read_only=True)
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = StudyGroupGoal
        fields = ['id', 'skill_id', 'skill_title', 'target_date', 'completed', 'days_remaining', 'created_at']
        read_only_fields = ['id', 'skill_id', 'skill_title', 'created_at']

    def get_days_remaining(self, obj):
        """Calculate days remaining until target date."""
        from datetime import date
        today = date.today()
        if obj.target_date >= today:
            return (obj.target_date - today).days
        return 0


class StudyGroupMessageSerializer(serializers.ModelSerializer):
    """Serializer for StudyGroupMessage with sender details."""

    sender_id = serializers.IntegerField(source='sender.id', read_only=True)
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_avatar = serializers.CharField(source='sender.avatar_url', read_only=True)

    class Meta:
        model = StudyGroupMessage
        fields = ['id', 'sender_id', 'sender_username', 'sender_avatar', 'text', 'sent_at']
        read_only_fields = ['id', 'sender_id', 'sender_username', 'sender_avatar', 'sent_at']


class StudyGroupDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for StudyGroup with members and goals."""

    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    member_count = serializers.SerializerMethodField()
    members = StudyGroupMemberSerializer(many=True, read_only=True)
    goals = StudyGroupGoalSerializer(many=True, read_only=True)
    is_full = serializers.SerializerMethodField()

    class Meta:
        model = StudyGroup
        fields = ['id', 'name', 'invite_code', 'created_by_username', 'max_members', 'member_count', 'is_full', 'members', 'goals', 'created_at']
        read_only_fields = ['id', 'invite_code', 'created_by_username', 'member_count', 'is_full', 'members', 'goals', 'created_at']

    def get_member_count(self, obj):
        """Get current member count."""
        return obj.get_member_count()

    def get_is_full(self, obj):
        """Check if group is full."""
        return obj.is_full()


class StudyGroupListSerializer(serializers.ModelSerializer):
    """List serializer for StudyGroup."""

    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    member_count = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()

    class Meta:
        model = StudyGroup
        fields = ['id', 'name', 'invite_code', 'created_by_username', 'member_count', 'max_members', 'is_full', 'created_at']
        read_only_fields = ['id', 'invite_code', 'created_by_username', 'member_count', 'is_full', 'created_at']

    def get_member_count(self, obj):
        """Get current member count."""
        return obj.get_member_count()

    def get_is_full(self, obj):
        """Check if group is full."""
        return obj.is_full()
