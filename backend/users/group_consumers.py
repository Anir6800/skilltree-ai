"""
SkillTree AI - Study Group WebSocket Consumer
Real-time group chat with typing indicators and system messages.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class GroupChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for study group chat.
    Handles real-time messaging, typing indicators, and system events.

    Connects to: ws/group/{group_id}/
    """

    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.user = user
        self.group_id = self.scope['url_route']['kwargs'].get('group_id')

        if not self.group_id:
            await self.close(code=4000)
            return

        from users.models import StudyGroup, StudyGroupMembership

        try:
            group = await database_sync_to_async(
                StudyGroup.objects.get
            )(id=self.group_id)

            membership = await database_sync_to_async(
                lambda: StudyGroupMembership.objects.filter(group=group, user=user).first()
            )()

            if not membership:
                await self.close(code=4003)
                return

        except StudyGroup.DoesNotExist:
            await self.close(code=4004)
            return

        self.group_name = f'group_{self.group_id}'
        self.typing_timeout = {}

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'user_joined',
                'username': self.user.username,
                'user_id': self.user.id,
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'user_left',
                    'username': self.user.username,
                    'user_id': self.user.id,
                }
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
            return

        message_type = data.get('type')

        if message_type == 'message':
            await self.handle_message(data)
        elif message_type == 'typing':
            await self.handle_typing(data)
        else:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Unknown message type: {message_type}'
            }))

    async def handle_message(self, data):
        text = data.get('text', '').strip()

        if not text:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Message cannot be empty'
            }))
            return

        if len(text) > 1000:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Message is too long (max 1000 characters)'
            }))
            return

        from users.models import StudyGroupMessage

        message = await database_sync_to_async(
            StudyGroupMessage.objects.create
        )(
            group_id=self.group_id,
            sender=self.user,
            text=text
        )

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat_message',
                'id': message.id,
                'sender_id': self.user.id,
                'sender_username': self.user.username,
                'sender_avatar': self.user.avatar_url,
                'text': text,
                'sent_at': message.sent_at.isoformat(),
            }
        )

        if self.user.id in self.typing_timeout:
            del self.typing_timeout[self.user.id]

    async def handle_typing(self, data):
        username = data.get('username', self.user.username)

        self.typing_timeout[self.user.id] = timezone.now() + timedelta(seconds=3)

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'username': username,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'id': event['id'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'sender_avatar': event['sender_avatar'],
            'text': event['text'],
            'sent_at': event['sent_at'],
        }))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
        }))

    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'system',
            'message': f"{event['username']} joined the group",
            'user_id': event['user_id'],
            'username': event['username'],
            'event': 'user_joined',
        }))

    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'system',
            'message': f"{event['username']} left the group",
            'user_id': event['user_id'],
            'username': event['username'],
            'event': 'user_left',
        }))

    async def skill_completed(self, event):
        await self.send(text_data=json.dumps({
            'type': 'system',
            'message': f"{event['username']} completed {event['skill_title']}!",
            'user_id': event['user_id'],
            'username': event['username'],
            'skill_title': event['skill_title'],
            'event': 'skill_completed',
        }))
