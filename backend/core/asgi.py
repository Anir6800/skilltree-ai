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

# Import SkillTree AI consumers
# These imports must happen after get_asgi_application()
from multiplayer.consumers import MatchConsumer
from executor.consumers import ExecutionStatusConsumer
from admin_panel.consumers import AssessmentResultConsumer
from skills.consumers import SkillTreeGenerationConsumer, QuestAutoFillConsumer

application = ProtocolTypeRouter({
    # Standard HTTP requests handled by Django
    "http": django_asgi_app,
    
    # WebSocket requests handled by Django Channels
    "websocket": AuthMiddlewareStack(
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
        ])
    ),
})
