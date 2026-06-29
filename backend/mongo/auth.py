"""
MongoEngine authentication layer
================================
Replaces the Django-auth + SimpleJWT (DB-backed) stack, which depended on
relational tables (auth_user, token_blacklist, contenttypes) that no longer
exist after the ODM migration.

What this provides (preserving the existing API contract):
  - issue_tokens(user)            -> {"access": ..., "refresh": ...}
  - decode_token(token)           -> claims dict (raises AuthTokenError)
  - get_user_from_token(token)    -> mongo.documents.User | None
  - blacklist_refresh(token)      -> revoke a refresh token (logout)
  - MongoJWTAuthentication        -> DRF authentication_class
  - authenticate_credentials(...) -> username/password login helper

Token claims mirror SimpleJWT so the frontend and WebSocket consumers keep
working with only an import swap:
    {"token_type": "access"|"refresh", "user_id": <str>, "exp", "iat", "jti"}

Signing key + lifetimes are read from Django settings (already present), so no
new secret management is required.
"""

import uuid
import logging
from datetime import datetime, timedelta, timezone

import jwt  # PyJWT (already installed via SimpleJWT)
from django.conf import settings
from rest_framework import authentication, exceptions

from .documents import User, BlacklistedToken

logger = logging.getLogger(__name__)


class AuthTokenError(Exception):
    """Raised when a JWT is invalid, expired, or revoked."""


def _now():
    return datetime.now(tz=timezone.utc)


def _lifetimes():
    sj = getattr(settings, "SIMPLE_JWT", {})
    access = sj.get("ACCESS_TOKEN_LIFETIME", timedelta(minutes=60))
    refresh = sj.get("REFRESH_TOKEN_LIFETIME", timedelta(days=7))
    return access, refresh


def _signing_key():
    sj = getattr(settings, "SIMPLE_JWT", {})
    return sj.get("SIGNING_KEY") or settings.SECRET_KEY


def _algorithm():
    sj = getattr(settings, "SIMPLE_JWT", {})
    return sj.get("ALGORITHM", "HS256")


def _encode(payload: dict) -> str:
    token = jwt.encode(payload, _signing_key(), algorithm=_algorithm())
    # PyJWT >= 2 returns str already.
    return token if isinstance(token, str) else token.decode("utf-8")


def issue_tokens(user: User) -> dict:
    """Mint an access+refresh pair for a MongoEngine User."""
    access_life, refresh_life = _lifetimes()
    now = _now()
    uid = str(user.id)

    access_payload = {
        "token_type": "access",
        "user_id": uid,
        "username": user.username,
        "role": user.role,
        "iat": int(now.timestamp()),
        "exp": int((now + access_life).timestamp()),
        "jti": uuid.uuid4().hex,
    }
    refresh_payload = {
        "token_type": "refresh",
        "user_id": uid,
        "iat": int(now.timestamp()),
        "exp": int((now + refresh_life).timestamp()),
        "jti": uuid.uuid4().hex,
    }
    return {"access": _encode(access_payload), "refresh": _encode(refresh_payload)}


def refresh_access_token(refresh_token: str) -> dict:
    """
    Exchange a valid (non-blacklisted) refresh token for a new access token.
    Rotates the refresh token (blacklists the old one) to match the existing
    ROTATE_REFRESH_TOKENS + BLACKLIST_AFTER_ROTATION behaviour.
    """
    claims = decode_token(refresh_token, expected_type="refresh")
    user = User.objects(id=claims["user_id"]).first()
    if not user or not user.is_active:
        raise AuthTokenError("User inactive or missing")

    # Rotate: revoke the presented refresh token.
    blacklist_refresh(refresh_token)
    return issue_tokens(user)


def decode_token(token: str, expected_type: str = None) -> dict:
    """Decode + validate a JWT. Raises AuthTokenError on any problem."""
    try:
        claims = jwt.decode(token, _signing_key(), algorithms=[_algorithm()])
    except jwt.ExpiredSignatureError:
        raise AuthTokenError("Token has expired")
    except jwt.InvalidTokenError as exc:
        raise AuthTokenError(f"Invalid token: {exc}")

    if expected_type and claims.get("token_type") != expected_type:
        raise AuthTokenError(f"Expected {expected_type} token")

    # Refresh tokens may be revoked.
    if claims.get("token_type") == "refresh":
        if BlacklistedToken.objects(jti=claims.get("jti")).first():
            raise AuthTokenError("Token has been revoked")

    return claims


def get_user_from_token(token: str):
    """Return the User for a valid access token, or None. Used by WS consumers."""
    try:
        claims = decode_token(token, expected_type="access")
    except AuthTokenError:
        return None
    return User.objects(id=claims.get("user_id")).first()


def blacklist_refresh(refresh_token: str):
    """Revoke a refresh token (logout). Idempotent."""
    try:
        claims = jwt.decode(
            refresh_token, _signing_key(), algorithms=[_algorithm()],
            options={"verify_exp": False},
        )
    except jwt.InvalidTokenError:
        return
    jti = claims.get("jti")
    if not jti:
        return
    exp = claims.get("exp")
    BlacklistedToken.objects(jti=jti).update_one(
        upsert=True,
        set__jti=jti,
        set__user_id=claims.get("user_id"),
        set__blacklisted_at=_now(),
        set__expires_at=datetime.fromtimestamp(exp, tz=timezone.utc) if exp else None,
    )


def authenticate_credentials(username: str, password: str):
    """Username/password login. Returns User or None."""
    user = User.objects(username=username).first()
    if user and user.is_active and user.check_password(password):
        return user
    return None


# ---------------------------------------------------------------------------
# DRF integration — drop-in replacement for SimpleJWT's JWTAuthentication
# ---------------------------------------------------------------------------

class MongoJWTAuthentication(authentication.BaseAuthentication):
    """
    DRF authentication class. Wire it via REST_FRAMEWORK
    DEFAULT_AUTHENTICATION_CLASSES = ('mongo.auth.MongoJWTAuthentication',).

    Reads `Authorization: Bearer <access>`; returns (User, claims).
    """
    keyword = "Bearer"

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).split()
        if not header or header[0].lower() != self.keyword.lower().encode():
            return None
        if len(header) != 2:
            raise exceptions.AuthenticationFailed("Invalid Authorization header")

        token = header[1].decode("utf-8")
        try:
            claims = decode_token(token, expected_type="access")
        except AuthTokenError as exc:
            raise exceptions.AuthenticationFailed(str(exc))

        user = User.objects(id=claims.get("user_id")).first()
        if not user or not user.is_active:
            raise exceptions.AuthenticationFailed("User not found or inactive")
        return (user, claims)

    def authenticate_header(self, request):
        return self.keyword
