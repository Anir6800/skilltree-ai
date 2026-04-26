import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class ExecutionStatusConsumer(AsyncWebsocketConsumer):
    """
    Consumer for tracking code execution status.
    Provides real-time feedback on AI-generated code runs.
    """
    async def connect(self):
        # SECURITY: Check authentication
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4001)  # Unauthorized
            return
        
        self.user = user
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.group_name = f'execution_{self.task_id}'

        # Join task execution group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave task execution group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def execution_update(self, event):
        """
        Receives updates from Celery tasks via channel_layer.group_send
        """
        status = event['status']
        output = event.get('output', '')

        # Send status update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'execution_status',
            'status': status,
            'output': output
        }))
