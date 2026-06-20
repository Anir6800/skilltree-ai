import os
from django.core.asgi import get_asgi_application

# Set the default settings module for the 'django' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

from core.channels_auth import JWTAuthMiddleware

# Import SkillTree AI consumers
# These imports must happen after get_asgi_application()
from multiplayer.consumers import MatchConsumer
from executor.consumers import ExecutionStatusConsumer
from admin_panel.consumers import AssessmentResultConsumer
from skills.consumers import SkillTreeGenerationConsumer, QuestAutoFillConsumer
from users.group_consumers import GroupChatConsumer
from users.user_consumers import UserConsumer

application = ProtocolTypeRouter({
    # Standard HTTP requests handled by Django
    "http": django_asgi_app,
    
    # WebSocket requests handled by Django Channels.
    # JWTAuthMiddleware (inner) overrides scope["user"] from a ?token= access
    # token when present; AuthMiddlewareStack (outer) keeps session auth working.
    "websocket": AuthMiddlewareStack(
        JWTAuthMiddleware(
        URLRouter([
            # Multiplayer Match Routing: ws/match/<room_id>/
            path("ws/match/<str:room_id>/", MatchConsumer.as_asgi()),
            
            # Code Execution Status Routing: ws/execution/<task_id>/
            path("ws/execution/<str:task_id>/", ExecutionStatusConsumer.as_asgi()),
            
            # Assessment Result Routing: ws/assessments/<submission_id>/
            path("ws/assessments/<int:submission_id>/", AssessmentResultConsumer.as_asgi()),
            
            # Skill Tree Generation Routing: ws/skills/generation/
            path("ws/skills/generation/", SkillTreeGenerationConsumer.as_asgi()),
            
            # Quest AutoFill Progress Routing: ws/skills/autofill/<tree_id>/
            path("ws/skills/autofill/<uuid:tree_id>/", QuestAutoFillConsumer.as_asgi()),
            
            # Study Group Chat Routing: ws/group/<group_id>/
            path("ws/group/<int:group_id>/", GroupChatConsumer.as_asgi()),

            # Global User Notifications: ws/user/
            path("ws/user/", UserConsumer.as_asgi()),
        ])
        )
    ),
})
