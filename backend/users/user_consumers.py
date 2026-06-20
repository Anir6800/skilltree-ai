"""
SkillTree AI - Global User WebSocket Consumer
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
import logging

logger = logging.getLogger(__name__)

class UserConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for global user notifications.
    Currently handles real-time badge unlock events.
    """
    
    async def connect(self):
        self.user = self.scope.get("user")
        
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
            
        self.group_name = f"user_{self.user.id}"
        
        # Join user's personal notification group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.debug(f"User {self.user.username} connected to global notifications")

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.debug(f"User {self.user.username} disconnected from global notifications")

    async def badge_earned(self, event):
        """
        Handler for badge_earned event sent by BadgeService
        """
        # Send the event dictionary as JSON
        # Event already contains "type": "badge_earned", so useWebSocket will route it correctly
        await self.send(text_data=json.dumps(event))

    async def user_notification(self, event):
        """
        Generic per-user notification handler.
        Sends the inner payload (which carries its own "type") to the client,
        so the frontend's useWebSocket can route it like any other event.
        """
        await self.send(text_data=json.dumps(event.get("payload", {})))
