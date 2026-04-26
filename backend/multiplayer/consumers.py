import json
import logging
from datetime import datetime
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from multiplayer.models import Match, MatchParticipant
from users.models import User

logger = logging.getLogger(__name__)


class MatchConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time multiplayer matches.
    Handles connection lifecycle, player readiness, code updates, and submission results.
    """

    async def connect(self):
        """
        Handle WebSocket connection.
        Extract match_id from URL, verify JWT token, and join channel group.
        """
        self.match_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'match_{self.match_id}'
        self.user = None

        # Extract JWT token from query string
        query_string = self.scope.get('query_string', b'').decode('utf-8')
        token = None
        
        for param in query_string.split('&'):
            if param.startswith('token='):
                token = param.split('=', 1)[1]
                break

        if not token:
            logger.warning(f"Connection rejected: No token provided for match {self.match_id}")
            await self.accept()
            await self.close(code=4001)
            return

        # Verify JWT token and extract user
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            self.user = await self.get_user(user_id)

            if not self.user:
                logger.warning(f"Connection rejected: Invalid user_id {user_id}")
                await self.accept()
                await self.close(code=4002)
                return

        except TokenError as e:
            logger.warning(f"Connection rejected: Invalid token - {str(e)}")
            await self.accept()
            await self.close(code=4003)
            return

        # Verify user is a participant in this match
        is_participant = await self.verify_participant(self.match_id, self.user.id)
        if not is_participant:
            logger.warning(f"Connection rejected: User {self.user.id} not in match {self.match_id}")
            await self.accept()
            await self.close(code=4004)
            return

        # Accept connection and join channel group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Send initial match state
        match_state = await self.get_match_state(self.match_id)
        await self.send_json({
            'type': 'connected',
            'match_state': match_state
        })

        logger.info(f"User {self.user.username} connected to match {self.match_id}")

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        Leave channel group and broadcast player disconnection if match is still active.
        """
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

        if self.user and hasattr(self, 'match_id'):
            # Check if match is still active
            match_active = await self.is_match_active(self.match_id)
            if match_active:
                await self.broadcast_to_match(self.match_id, {
                    'type': 'player_disconnected',
                    'user_id': self.user.id,
                    'username': self.user.username
                })
                logger.info(f"User {self.user.username} disconnected from active match {self.match_id}")

    async def receive_json(self, content):
        """
        Handle incoming JSON messages from WebSocket.
        Routes messages based on event type.
        """
        event_type = content.get('type')

        if not event_type:
            await self.send_json({
                'type': 'error',
                'message': 'Missing event type'
            })
            return

        try:
            if event_type == 'ready':
                await self.handle_ready()
            elif event_type == 'code_update':
                await self.handle_code_update()
            elif event_type == 'submission_result':
                await self.handle_submission_result(content)
            elif event_type == 'surrender':
                await self.handle_surrender()
            else:
                await self.send_json({
                    'type': 'error',
                    'message': f'Unknown event type: {event_type}'
                })
        except Exception as e:
            logger.error(f"Error handling event {event_type}: {str(e)}", exc_info=True)
            await self.send_json({
                'type': 'error',
                'message': 'Internal server error'
            })

    async def handle_ready(self):
        """
        Mark player as ready. If all players are ready, start the match.
        """
        ready_count = await self.mark_player_ready(self.match_id, self.user.id)
        total_participants = await self.get_participant_count(self.match_id)

        await self.broadcast_to_match(self.match_id, {
            'type': 'player_ready',
            'user_id': self.user.id,
            'username': self.user.username,
            'ready_count': ready_count,
            'total_participants': total_participants
        })

        # If all players are ready, start the match
        if ready_count >= total_participants:
            started_at = await self.start_match(self.match_id)
            await self.broadcast_to_match(self.match_id, {
                'type': 'match_started',
                'started_at': started_at.isoformat() if started_at else None
            })
            logger.info(f"Match {self.match_id} started with {total_participants} players")

    async def handle_code_update(self):
        """
        Broadcast typing indicator to other players.
        Does not send actual code content for security.
        """
        await self.broadcast_to_match(self.match_id, {
            'type': 'opponent_typing',
            'user_id': self.user.id,
            'username': self.user.username
        }, exclude_sender=True)

    async def handle_submission_result(self, content):
        """
        Broadcast submission result to all players.
        """
        tests_passed = content.get('tests_passed', 0)
        tests_total = content.get('tests_total', 0)
        is_winner = content.get('is_winner', False)

        # Update participant score
        await self.update_participant_score(self.match_id, self.user.id, tests_passed)

        # If this is a winning submission, update match winner
        if is_winner:
            await self.set_match_winner(self.match_id, self.user.id)

        await self.broadcast_to_match(self.match_id, {
            'type': 'submission_result',
            'user_id': self.user.id,
            'username': self.user.username,
            'tests_passed': tests_passed,
            'tests_total': tests_total,
            'is_winner': is_winner
        })

        logger.info(f"User {self.user.username} submitted in match {self.match_id}: {tests_passed}/{tests_total}")

    async def handle_surrender(self):
        """
        Handle player surrender/forfeit.
        """
        await self.forfeit_match(self.match_id, self.user.id)
        
        await self.broadcast_to_match(self.match_id, {
            'type': 'player_surrendered',
            'user_id': self.user.id,
            'username': self.user.username
        })

        logger.info(f"User {self.user.username} surrendered in match {self.match_id}")

    async def broadcast_to_match(self, match_id, message_dict, exclude_sender=False):
        """
        Broadcast message to all participants in the match.
        
        Args:
            match_id: The match ID
            message_dict: Dictionary containing the message data
            exclude_sender: If True, don't send to the current user
        """
        if exclude_sender and self.user:
            message_dict['_exclude_user_id'] = self.user.id

        await self.channel_layer.group_send(
            f'match_{match_id}',
            {
                'type': 'match_message',
                'message': message_dict
            }
        )

    async def match_message(self, event):
        """
        Receive message from channel layer and send to WebSocket.
        This is called when broadcast_to_match sends a message.
        """
        message = event['message']
        
        # Check if this message should be excluded for this user
        exclude_user_id = message.pop('_exclude_user_id', None)
        if exclude_user_id and self.user and exclude_user_id == self.user.id:
            return

        await self.send_json(message)

    # Database operations (sync functions wrapped with database_sync_to_async)

    @database_sync_to_async
    def get_user(self, user_id):
        """Get user by ID."""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def verify_participant(self, match_id, user_id):
        """Verify user is a participant in the match."""
        try:
            match = Match.objects.get(id=match_id)
            return match.participants.filter(id=user_id).exists()
        except Match.DoesNotExist:
            return False

    @database_sync_to_async
    def get_match_state(self, match_id):
        """Get current match state."""
        try:
            match = Match.objects.prefetch_related('participants', 'quest').get(id=match_id)
            participants = [
                {
                    'id': p.id,
                    'username': p.username,
                    'level': p.level,
                    'avatar_url': p.avatar_url
                }
                for p in match.participants.all()
            ]
            
            return {
                'id': match.id,
                'status': match.status,
                'participants': participants,
                'quest': {
                    'id': match.quest.id,
                    'title': match.quest.title,
                    'description': match.quest.description,
                    'starter_code': match.quest.starter_code,
                    'xp_reward': match.quest.xp_reward
                },
                'started_at': match.started_at.isoformat() if match.started_at else None,
                'ended_at': match.ended_at.isoformat() if match.ended_at else None
            }
        except Match.DoesNotExist:
            return None

    @database_sync_to_async
    def is_match_active(self, match_id):
        """Check if match is still active."""
        try:
            match = Match.objects.get(id=match_id)
            return match.status in ['waiting', 'active']
        except Match.DoesNotExist:
            return False

    @database_sync_to_async
    def mark_player_ready(self, match_id, user_id):
        """
        Mark player as ready and return count of ready players.
        For simplicity, we consider all connected players as ready.
        Returns the total participant count.
        """
        try:
            match = Match.objects.get(id=match_id)
            return match.participants.count()
        except Match.DoesNotExist:
            return 0

    @database_sync_to_async
    def get_participant_count(self, match_id):
        """Get total number of participants in match."""
        try:
            match = Match.objects.get(id=match_id)
            return match.participants.count()
        except Match.DoesNotExist:
            return 0

    @database_sync_to_async
    def start_match(self, match_id):
        """Start the match and return started_at timestamp."""
        try:
            match = Match.objects.get(id=match_id)
            if match.status == 'waiting':
                match.status = 'active'
                match.started_at = timezone.now()
                match.save()
                return match.started_at
            return match.started_at
        except Match.DoesNotExist:
            return None

    @database_sync_to_async
    def update_participant_score(self, match_id, user_id, score):
        """Update participant score."""
        try:
            participant = MatchParticipant.objects.get(match_id=match_id, user_id=user_id)
            participant.score = max(participant.score, score)
            participant.save()
        except MatchParticipant.DoesNotExist:
            pass

    @database_sync_to_async
    def set_match_winner(self, match_id, user_id):
        """Set match winner and finish the match."""
        try:
            match = Match.objects.get(id=match_id)
            if match.status == 'active':
                match.winner_id = user_id
                match.status = 'finished'
                match.ended_at = timezone.now()
                match.save()
        except Match.DoesNotExist:
            pass

    @database_sync_to_async
    def forfeit_match(self, match_id, user_id):
        """Handle player forfeit."""
        try:
            match = Match.objects.get(id=match_id)
            if match.status == 'active':
                # Find another participant to declare winner
                other_participant = match.participants.exclude(id=user_id).first()
                if other_participant:
                    match.winner = other_participant
                    match.status = 'finished'
                    match.ended_at = timezone.now()
                    match.save()
        except Match.DoesNotExist:
            pass
