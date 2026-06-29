"""
Lightweight serializers for the MongoEngine-backed API.

DRF's ModelSerializer is bound to the Django ORM, so we serialize MongoEngine
documents to plain dicts here. Output shapes mirror the existing REST contract
so the frontend needs no changes.

`id` is exposed as the legacy integer id when available (so existing int-based
frontend routes keep working during the transition); new documents fall back to
the Mongo ObjectId string.
"""


def _pub_id(doc):
    legacy = getattr(doc, "legacy_id", None)
    return legacy if legacy is not None else str(doc.id)


def serialize_user(u):
    return {
        "id": _pub_id(u),
        "username": u.username,
        "email": u.email or "",
        "xp": u.xp,
        "level": u.level,
        "streak_days": u.streak_days,
        "role": u.role,
        "avatar_url": u.avatar_url or "",
        "is_staff": u.is_staff,
    }


def serialize_skill(s):
    return {
        "id": _pub_id(s),
        "title": s.title,
        "description": s.description,
        "category": s.category,
        "difficulty": s.difficulty,
        "tree_depth": s.tree_depth,
        "xp_required_to_unlock": s.xp_required_to_unlock,
    }


def serialize_quest(q):
    return {
        "id": _pub_id(q),
        "skill_id": _pub_id(q.skill) if q.skill else None,
        "type": q.type,
        "title": q.title,
        "description": q.description,
        "xp_reward": q.xp_reward,
        "estimated_minutes": q.estimated_minutes,
        "difficulty_multiplier": q.difficulty_multiplier,
        "is_stub": q.is_stub,
    }


def serialize_leaderboard_entry(u, rank):
    return {
        "rank": rank,
        "user_id": _pub_id(u),
        "username": u.username,
        "xp": u.xp,
        "level": u.level,
        "streak_days": u.streak_days,
        "avatar_url": u.avatar_url or "",
    }
