from rest_framework import serializers
from django.contrib.auth import get_user_model
from multiplayer.models import Match, MatchParticipant
from quests.serializers import QuestDetailSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Simple user serializer for match participants."""
    class Meta:
        model = User
        fields = ['id', 'username', 'level', 'avatar_url', 'xp']


class MatchParticipantSerializer(serializers.ModelSerializer):
    """Serializer for match participants."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = MatchParticipant
        fields = ['user', 'joined_at', 'score']


class MatchSerializer(serializers.ModelSerializer):
    """Basic match serializer for list views — includes participant data."""
    quest = QuestDetailSerializer(read_only=True)
    participants = serializers.SerializerMethodField()
    participant_count = serializers.SerializerMethodField()

    class Meta:
        model = Match
        fields = [
            'id',
            'quest',
            'status',
            'participants',
            'participant_count',
            'started_at',
            'ended_at'
        ]

    def get_participants(self, obj):
        # Use prefetched data if available to avoid N+1
        if hasattr(obj, '_prefetched_objects_cache') and 'matchparticipant_set' in obj._prefetched_objects_cache:
            participants = obj.matchparticipant_set.all()
        else:
            participants = MatchParticipant.objects.filter(match=obj).select_related('user')
        return MatchParticipantSerializer(participants, many=True).data

    def get_participant_count(self, obj):
        return obj.participants.count()


class MatchDetailSerializer(serializers.ModelSerializer):
    """Detailed match serializer with participants."""
    quest = QuestDetailSerializer(read_only=True)
    participants = serializers.SerializerMethodField()
    winner = UserSerializer(read_only=True)
    
    class Meta:
        model = Match
        fields = [
            'id',
            'quest',
            'status',
            'participants',
            'winner',
            'started_at',
            'ended_at'
        ]
    
    def get_participants(self, obj):
        participants = MatchParticipant.objects.filter(match=obj).select_related('user')
        return MatchParticipantSerializer(participants, many=True).data


class MatchCreateSerializer(serializers.Serializer):
    """Serializer for creating a new match."""
    quest_id = serializers.IntegerField(required=True)
    max_participants = serializers.IntegerField(default=2, min_value=2, max_value=10)
    
    def validate_quest_id(self, value):
        from quests.models import Quest
        if not Quest.objects.filter(id=value).exists():
            raise serializers.ValidationError("Quest does not exist")
        return value
