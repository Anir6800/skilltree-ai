import os
from django.core.asgi import get_asgi_application
from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Set the default settings module for the 'django' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Bootstrap MongoEngine connection if USE_MONGODB=True (see mongo/bootstrap.py).
# Safe no-op when disabled; logs and continues if Mongo is unreachable.
from mongo.bootstrap import init_mongo_if_enabled
init_mongo_if_enabled()

from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from urllib.parse import parse_qs

User = get_user_model()

@database_sync_to_async
def get_user_from_token(token):
    try:
        validated_token = AccessToken(token)
        user_id = validated_token["user_id"]
        return User.objects.get(id=user_id)
    except Exception:
        return AnonymousUser()

class JWTAuthMiddleware:
    """
    Custom middleware that authenticates users from a query parameter 'token' containing a JWT.
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]
        
        if token:
            scope["user"] = await get_user_from_token(token)
        else:
            scope["user"] = AnonymousUser()
            
        return await self.inner(scope, receive, send)

from multiplayer.consumers import MatchConsumer
from executor.consumers import ExecutionStatusConsumer
from admin_panel.consumers import AssessmentResultConsumer
from skills.consumers import SkillTreeGenerationConsumer, QuestAutoFillConsumer
from users.group_consumers import GroupChatConsumer

application = ProtocolTypeRouter({
    # Standard HTTP requests handled by Django
    "http": django_asgi_app,
    
    # WebSocket requests handled by Django Channels
    "websocket": JWTAuthMiddleware(
        AuthMiddlewareStack(
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
            ])
        )
    ),
})
