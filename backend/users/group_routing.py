"""
SkillTree AI - Study Group WebSocket Routing
WebSocket URL routing for group chat.
"""

from django.urls import re_path
from .group_consumers import GroupChatConsumer

websocket_urlpatterns = [
    re_path(r'ws/group/(?P<group_id>\d+)/$', GroupChatConsumer.as_asgi()),
]
