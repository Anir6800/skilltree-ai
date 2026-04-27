import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class ExecutionStatusConsumer(AsyncWebsocketConsumer):
    """
    Consumer for tracking code execution status and pipeline progress.
    Provides real-time feedback on submission processing via WebSocket.
    
    Connects to: ws/execution/{submission_id}/
    Receives pipeline updates from Celery tasks via channel_layer.group_send()
    """
    async def connect(self):
        # SECURITY: Check authentication
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4001)  # Unauthorized
            return
        
        self.user = user
        self.submission_id = self.scope['url_route']['kwargs'].get('submission_id')
        
        if not self.submission_id:
            await self.close(code=4000)  # Bad request
            return
        
        # Verify user owns this submission
        from quests.models import QuestSubmission
        try:
            submission = await database_sync_to_async(
                QuestSubmission.objects.get
            )(id=self.submission_id, user=user)
        except QuestSubmission.DoesNotExist:
            await self.close(code=4003)  # Forbidden
            return
        
        self.group_name = f'execution_{self.submission_id}'

        # Join submission execution group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave submission execution group
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def pipeline_update(self, event):
        """
        Receives pipeline status updates from Celery tasks.
        
        Event structure:
        {
            'type': 'pipeline_update',
            'step': int,
            'step_name': str,
            'status': 'running'|'completed'|'failed',
            'timestamp': str,
            'data': dict (optional)
        }
        """
        message = {
            'type': 'pipeline_update',
            'step': event.get('step'),
            'step_name': event.get('step_name'),
            'status': event.get('status'),
            'timestamp': event.get('timestamp'),
        }
        
        if 'data' in event:
            message['data'] = event['data']
        
        await self.send(text_data=json.dumps(message))

    async def execution_update(self, event):
        """
        Legacy: Receives updates from Celery tasks via channel_layer.group_send
        Kept for backward compatibility.
        """
        status = event['status']
        output = event.get('output', '')

        # Send status update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'execution_status',
            'status': status,
            'output': output
        }))

    async def leaderboard_update(self, event):
        """
        Receives leaderboard rank updates.
        """
        await self.send(text_data=json.dumps({
            'type': 'leaderboard_update',
            'rank': event.get('rank'),
            'score': event.get('score'),
            'timestamp': event.get('timestamp'),
        }))

    async def skill_unlock(self, event):
        """
        Receives skill unlock notifications.
        """
        await self.send(text_data=json.dumps({
            'type': 'skill_unlock',
            'skill_completed': event.get('skill_completed'),
            'skill_title': event.get('skill_title'),
            'unlocked_skills': event.get('unlocked_skills', []),
            'timestamp': event.get('timestamp'),
        }))
