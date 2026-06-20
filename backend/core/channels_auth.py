"""
Channels JWT authentication middleware.

The SkillTree AI frontend is a JWT SPA — it stores the access token in
localStorage and has no Django session cookie. Channels' AuthMiddlewareStack
only authenticates from the session, so consumers that rely on scope["user"]
(e.g. users.user_consumers.UserConsumer for global notifications, group chat)
would always see AnonymousUser and close the connection.

This middleware reads a `?token=<access JWT>` query-string parameter, validates
it with SimpleJWT, and populates scope["user"]. It is intended to wrap the
URLRouter *inside* AuthMiddlewareStack so a valid JWT takes precedence over the
(usually anonymous) session user, while session auth still works when present.
"""

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def _get_user(user_id):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """Populate scope["user"] from a `?token=` JWT access token."""

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        token = parse_qs(query_string).get("token", [None])[0]

        if token:
            user = await self._authenticate(token)
            if user is not None:
                scope["user"] = user

        return await super().__call__(scope, receive, send)

    async def _authenticate(self, token):
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import TokenError

        try:
            access = AccessToken(token)
            return await _get_user(access["user_id"])
        except (TokenError, KeyError):
            return None
