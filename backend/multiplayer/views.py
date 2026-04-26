import secrets
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from multiplayer.models import Match, MatchParticipant
from multiplayer.serializers import MatchSerializer, MatchDetailSerializer, MatchCreateSerializer
from quests.models import Quest


class MatchViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing multiplayer matches.
    
    Endpoints:
    - POST /api/matches/ - Create a new match
    - POST /api/matches/join/ - Join a match by invite code
    - GET /api/matches/ - List open matches
    - GET /api/matches/{id}/ - Get match details
    """
    queryset = Match.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MatchCreateSerializer
        elif self.action == 'retrieve':
            return MatchDetailSerializer
        return MatchSerializer

    def get_queryset(self):
        """
        Filter matches based on query parameters.
        Default: show only waiting matches.
        """
        queryset = Match.objects.select_related('quest', 'winner').prefetch_related('participants')
        
        # Filter by status
        match_status = self.request.query_params.get('status', 'waiting')
        if match_status:
            queryset = queryset.filter(status=match_status)
        
        # Filter by quest
        quest_id = self.request.query_params.get('quest_id')
        if quest_id:
            queryset = queryset.filter(quest_id=quest_id)
        
        return queryset.order_by('-id')

    def create(self, request, *args, **kwargs):
        """
        Create a new match.
        
        Request body:
        {
            "quest_id": 1,
            "max_participants": 2
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        quest_id = serializer.validated_data['quest_id']
        max_participants = serializer.validated_data.get('max_participants', 2)
        
        # Validate quest exists
        quest = get_object_or_404(Quest, id=quest_id)
        
        # Create match
        match = Match.objects.create(
            quest=quest,
            status='waiting'
        )
        
        # Add creator as first participant
        MatchParticipant.objects.create(
            match=match,
            user=request.user
        )
        
        # Generate invite code (stored in a custom field if needed, or use match ID)
        # For simplicity, we'll use match ID as the invite code
        invite_code = f"MATCH-{match.id}"
        
        response_serializer = MatchDetailSerializer(match)
        return Response({
            **response_serializer.data,
            'invite_code': invite_code
        }, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        """Get detailed match information."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='join')
    def join_match(self, request):
        """
        Join a match by invite code.
        
        Request body:
        {
            "invite_code": "MATCH-123"
        }
        """
        invite_code = request.data.get('invite_code')
        
        if not invite_code:
            return Response(
                {'error': 'invite_code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract match ID from invite code
        try:
            if invite_code.startswith('MATCH-'):
                match_id = int(invite_code.split('-')[1])
            else:
                match_id = int(invite_code)
        except (ValueError, IndexError):
            return Response(
                {'error': 'Invalid invite code'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get match
        match = get_object_or_404(Match, id=match_id)
        
        # Validate match is waiting
        if match.status != 'waiting':
            return Response(
                {'error': 'Match is not accepting new players'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is already a participant
        if match.participants.filter(id=request.user.id).exists():
            return Response(
                {'error': 'You are already in this match'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check max participants (default 2)
        max_participants = 2  # Can be made configurable
        if match.participants.count() >= max_participants:
            return Response(
                {'error': 'Match is full'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add user as participant
        MatchParticipant.objects.create(
            match=match,
            user=request.user
        )
        
        serializer = MatchDetailSerializer(match)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='leave')
    def leave_match(self, request, pk=None):
        """
        Leave a match.
        Only allowed if match is still waiting.
        """
        match = self.get_object()
        
        # Check if user is a participant
        if not match.participants.filter(id=request.user.id).exists():
            return Response(
                {'error': 'You are not in this match'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Only allow leaving if match is waiting
        if match.status != 'waiting':
            return Response(
                {'error': 'Cannot leave an active or finished match'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove participant
        MatchParticipant.objects.filter(match=match, user=request.user).delete()
        
        # If no participants left, delete the match
        if match.participants.count() == 0:
            match.delete()
            return Response(
                {'message': 'Match deleted (no participants remaining)'},
                status=status.HTTP_200_OK
            )
        
        return Response(
            {'message': 'Left match successfully'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'], url_path='status')
    def match_status(self, request, pk=None):
        """
        Get current match status and participant info.
        """
        match = self.get_object()
        
        participants_data = [
            {
                'id': p.user.id,
                'username': p.user.username,
                'level': p.user.level,
                'score': p.score,
                'joined_at': p.joined_at.isoformat()
            }
            for p in match.matchparticipant_set.select_related('user').all()
        ]
        
        return Response({
            'id': match.id,
            'status': match.status,
            'quest': {
                'id': match.quest.id,
                'title': match.quest.title
            },
            'participants': participants_data,
            'winner': {
                'id': match.winner.id,
                'username': match.winner.username
            } if match.winner else None,
            'started_at': match.started_at.isoformat() if match.started_at else None,
            'ended_at': match.ended_at.isoformat() if match.ended_at else None
        })
