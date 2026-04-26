"""
WebSocket routing for admin_panel app.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/assessments/(?P<submission_id>\d+)/$', consumers.AssessmentResultConsumer.as_asgi()),
]
