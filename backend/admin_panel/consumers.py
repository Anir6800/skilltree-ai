"""
WebSocket consumers for assessment real-time updates.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist


class AssessmentResultConsumer(AsyncWebsocketConsumer):
    """
    Consumer for real-time assessment evaluation results.
    Clients subscribe to specific submission updates.
    """
    
    @database_sync_to_async
    def verify_submission_ownership(self, submission_id, user):
        """Verify that the submission belongs to the user."""
        from admin_panel.models import AssessmentSubmission
        try:
            submission = AssessmentSubmission.objects.get(id=submission_id, user=user)
            return True
        except ObjectDoesNotExist:
            return False
    
    async def connect(self):
        """Handle WebSocket connection."""
        # SECURITY: Check authentication
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4001)  # Unauthorized
            return
        
        self.user = user
        self.submission_id = self.scope['url_route']['kwargs']['submission_id']
        
        # SECURITY: Verify submission ownership
        has_access = await self.verify_submission_ownership(self.submission_id, user)
        if not has_access:
            await self.close(code=4004)  # Not found / No access
            return
        
        self.group_name = f'assessment_{self.submission_id}'
        
        # Join assessment group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave assessment group
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def assessment_result(self, event):
        """
        Receive assessment result from Celery task via channel_layer.group_send.
        Broadcast to WebSocket client.
        """
        # Send result to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'assessment_result',
            'submission_id': event['submission_id'],
            'status': event['status'],
            'result': event.get('result'),
            'score': event.get('score'),
            'passed': event.get('passed')
        }))
