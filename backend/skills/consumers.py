"""
SkillTree AI - Skills WebSocket Consumers
Real-time notifications for skill tree generation and updates.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class SkillTreeGenerationConsumer(AsyncWebsocketConsumer):
    """
    Consumer for real-time skill tree generation notifications.
    Connects to: ws/skills/generation/
    Receives tree_generated events from SkillTreeGeneratorService.
    """
    
    async def connect(self):
        # SECURITY: Check authentication
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4001)  # Unauthorized
            return
        
        self.user = user
        self.group_name = f"tree_generation_{user.id}"
        
        # Join user's tree generation group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave tree generation group
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def tree_generated(self, event):
        """
        Receives tree generation completion event.
        
        Event structure:
        {
            'type': 'tree_generated',
            'tree_id': str,
            'skill_count': int,
            'topic': str,
            'timestamp': str,
        }
        """
        message = {
            'type': 'tree_generated',
            'tree_id': event.get('tree_id'),
            'skill_count': event.get('skill_count'),
            'topic': event.get('topic'),
            'timestamp': event.get('timestamp'),
        }
        
        await self.send(text_data=json.dumps(message))


class QuestAutoFillConsumer(AsyncWebsocketConsumer):
    """
    Consumer for real-time quest auto-fill progress notifications.
    Connects to: ws/skills/autofill/{tree_id}/
    Receives quest_filled events from QuestAutoFillService.
    """
    
    async def connect(self):
        # SECURITY: Check authentication
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4001)  # Unauthorized
            return
        
        self.user = user
        self.tree_id = self.scope['url_route']['kwargs'].get('tree_id')
        
        if not self.tree_id:
            await self.close(code=4000)  # Bad request
            return
        
        self.group_name = f"quest_autofill_{self.tree_id}"
        
        # Join tree's quest autofill group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave quest autofill group
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def quest_filled(self, event):
        """
        Receives quest filled event.
        
        Event structure:
        {
            'type': 'quest_filled',
            'quest_id': int,
            'quest_title': str,
            'skill_title': str,
            'timestamp': str,
        }
        """
        message = {
            'type': 'quest_filled',
            'quest_id': event.get('quest_id'),
            'quest_title': event.get('quest_title'),
            'skill_title': event.get('skill_title'),
            'timestamp': event.get('timestamp'),
        }
        
        await self.send(text_data=json.dumps(message))
