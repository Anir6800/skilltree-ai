"""
WebSocket routing for executor app.
Handles real-time pipeline status updates and execution progress.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/execution/(?P<submission_id>\d+)/$', consumers.ExecutionStatusConsumer.as_asgi()),
]
