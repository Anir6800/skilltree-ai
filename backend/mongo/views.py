"""
MongoEngine-backed DRF views (LIVE).

Mounted under /api/mongo/ (see mongo/api_urls.py) so they run ALONGSIDE the
existing Django-ORM views without disturbing them. These prove the full stack
works on MongoDB: custom JWT auth + reads/writes against migrated documents.

Auth uses MongoJWTAuthentication explicitly per-view (NOT globally) so the
legacy endpoints keep using SimpleJWT until full cutover.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .connection import connect_mongo
from .auth import (
    MongoJWTAuthentication,
    issue_tokens,
    refresh_access_token,
    blacklist_refresh,
    authenticate_credentials,
    AuthTokenError,
)
from . import documents as D
from .serializers import (
    serialize_user,
    serialize_skill,
    serialize_quest,
    serialize_leaderboard_entry,
)

_mongo_ready = False


def _ensure_mongo():
    """Connect on first use (idempotent). Avoids connecting at import time."""
    global _mongo_ready
    if not _mongo_ready:
        connect_mongo()
        _mongo_ready = True


class _MongoView(APIView):
    """Base: ensures the Mongo connection before handling any request."""
    authentication_classes = [MongoJWTAuthentication]

    def initial(self, request, *args, **kwargs):
        _ensure_mongo()
        super().initial(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class RegisterView(_MongoView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""
        email = (data.get("email") or "").strip() or None

        if not username or not password:
            return Response({"error": "username and password are required"},
                            status=status.HTTP_400_BAD_REQUEST)
        if D.User.objects(username=username).first():
            return Response({"error": "username already taken"},
                            status=status.HTTP_400_BAD_REQUEST)

        user = D.User(username=username, email=email, role="student")
        user.set_password(password)
        user.save()  # save() recomputes level from xp

        tokens = issue_tokens(user)
        return Response({"user": serialize_user(user), "tokens": tokens},
                        status=status.HTTP_201_CREATED)


class LoginView(_MongoView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        password = request.data.get("password") or ""
        user = authenticate_credentials(username, password)
        if not user:
            return Response({"detail": "Invalid credentials"},
                            status=status.HTTP_401_UNAUTHORIZED)
        tokens = issue_tokens(user)
        return Response({"user": serialize_user(user), **tokens})


class TokenRefreshView(_MongoView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response({"detail": "refresh token required"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            return Response(refresh_access_token(refresh))
        except AuthTokenError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(_MongoView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if refresh:
            blacklist_refresh(refresh)
        return Response({"detail": "logged out"})


class MeView(_MongoView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(serialize_user(request.user))


# ---------------------------------------------------------------------------
# Core reads (prove references + queries work on Mongo data)
# ---------------------------------------------------------------------------

class SkillListView(_MongoView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = D.Skill.objects.order_by("tree_depth", "difficulty")
        return Response({"results": [serialize_skill(s) for s in qs], "count": qs.count()})


class QuestListView(_MongoView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = D.Quest.objects(is_stub=False)
        skill_id = request.query_params.get("skill_id")
        if skill_id:
            skill = None
            try:
                skill = D.Skill.objects(legacy_id=int(skill_id)).first()
            except (ValueError, TypeError):
                pass
            if skill is None:
                skill = D.Skill.objects(id=skill_id).first()
            qs = qs(skill=skill) if skill else qs.none()
        qs = qs.order_by("-xp_reward")
        return Response({"results": [serialize_quest(q) for q in qs], "count": qs.count()})


class LeaderboardView(_MongoView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        top = D.User.objects.order_by("-xp").limit(20)
        results = [serialize_leaderboard_entry(u, i + 1) for i, u in enumerate(top)]
        return Response({"results": results, "count": len(results)})
