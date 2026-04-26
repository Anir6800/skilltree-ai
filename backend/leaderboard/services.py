"""
SkillTree AI - Leaderboard Services
Redis-backed leaderboard with XP scoring formula, ranking, and snapshot persistence.
"""

import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)

User = get_user_model()

# Redis key constants
LEADERBOARD_GLOBAL_KEY = 'leaderboard:global'
LEADERBOARD_WEEKLY_KEY = 'leaderboard:weekly'

# ─── Redis client helper ──────────────────────────────────────────────────────

def _get_redis():
    """
    Return a raw Redis connection from django-redis cache backend.
    Falls back gracefully if Redis is unavailable.
    """
    try:
        from django_redis import get_redis_connection
        return get_redis_connection('default')
    except Exception as e:
        logger.warning(f"Redis unavailable: {e}")
        return None


# ─── Scoring formula ──────────────────────────────────────────────────────────

def compute_user_score(user_id):
    """
    Compute leaderboard score for a user.

    Formula:
        total_score = base_xp
                    + (streak_days * 50)
                    + sum(xp_reward * difficulty_multiplier for passed submissions)

    Returns:
        float: computed score, or 0 on error.
    """
    from quests.models import QuestSubmission

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.warning(f"compute_user_score: user {user_id} not found")
        return 0

    base_xp = max(0, user.xp)
    streak_bonus = max(0, user.streak_days) * 50

    passed_submissions = QuestSubmission.objects.filter(
        user_id=user_id,
        status='passed',
    ).select_related('quest')

    submission_bonus = sum(
        float(sub.quest.xp_reward) * float(sub.quest.difficulty_multiplier)
        for sub in passed_submissions
        if sub.quest is not None
    )

    total = base_xp + streak_bonus + submission_bonus
    return round(total, 2)


# ─── Redis write ──────────────────────────────────────────────────────────────

def update_leaderboard(user_id):
    """
    Compute score for user and write to Redis sorted sets (global + weekly).

    Uses ZADD with the computed score. Safe to call repeatedly — Redis ZADD
    updates the score if the member already exists.

    Returns:
        float: the score that was written, or None on failure.
    """
    score = compute_user_score(user_id)
    redis = _get_redis()

    if redis is None:
        logger.error("update_leaderboard: Redis unavailable, skipping ZADD")
        return None

    try:
        redis.zadd(LEADERBOARD_GLOBAL_KEY, {str(user_id): score})
        redis.zadd(LEADERBOARD_WEEKLY_KEY, {str(user_id): score})
        logger.debug(f"Leaderboard updated: user={user_id} score={score}")
        return score
    except Exception as e:
        logger.error(f"update_leaderboard ZADD failed for user {user_id}: {e}")
        return None


# ─── Redis read helpers ───────────────────────────────────────────────────────

def _enrich_rankings(raw_entries, offset=0):
    """
    Given a list of (user_id_bytes, score_float) tuples from Redis ZREVRANGE,
    fetch User rows from PostgreSQL and return enriched dicts.

    Args:
        raw_entries: list of (member, score) from redis-py WITHSCORES
        offset: rank offset for pagination (0-indexed start rank)

    Returns:
        list[dict]: enriched ranking entries
    """
    if not raw_entries:
        return []

    user_ids = []
    for member, _ in raw_entries:
        try:
            user_ids.append(int(member))
        except (ValueError, TypeError):
            pass

    users_by_id = {
        u.id: u
        for u in User.objects.filter(id__in=user_ids).only(
            'id', 'username', 'xp', 'level', 'streak_days', 'avatar_url'
        )
    }

    results = []
    for idx, (member, score) in enumerate(raw_entries):
        try:
            uid = int(member)
        except (ValueError, TypeError):
            continue

        user = users_by_id.get(uid)
        if user is None:
            continue

        results.append({
            'rank': offset + idx + 1,
            'user_id': uid,
            'username': user.username,
            'xp': user.xp,
            'level': user.level,
            'streak_days': user.streak_days,
            'avatar_url': user.avatar_url or '',
            'score': score,
        })

    return results


def _get_previous_rank(user_id, redis_key):
    """
    Look up the user's rank from the most recent LeaderboardSnapshot.
    Returns None if no snapshot exists.
    """
    from leaderboard.models import LeaderboardSnapshot
    try:
        snap = LeaderboardSnapshot.objects.filter(user_id=user_id).latest()
        return snap.rank
    except LeaderboardSnapshot.DoesNotExist:
        return None


def _attach_rank_changes(entries, redis_key):
    """
    Attach a 'rank_change' field to each entry by comparing current rank
    against the latest snapshot rank.

    Positive = moved up, negative = moved down, 0 = no change, None = new entry.
    """
    for entry in entries:
        prev = _get_previous_rank(entry['user_id'], redis_key)
        if prev is None:
            entry['rank_change'] = None
        else:
            entry['rank_change'] = prev - entry['rank']  # positive = improved
    return entries


# ─── Public ranking queries ───────────────────────────────────────────────────

def get_global_rankings(page=1, limit=50):
    """
    Fetch paginated global leaderboard from Redis.

    Args:
        page (int): 1-indexed page number
        limit (int): entries per page (max 100)

    Returns:
        dict: {results, total, page, limit}
    """
    limit = min(int(limit), 100)
    page = max(1, int(page))
    offset = (page - 1) * limit
    start = offset
    end = offset + limit - 1

    redis = _get_redis()
    if redis is None:
        return _fallback_db_rankings(page, limit)

    try:
        raw = redis.zrevrange(LEADERBOARD_GLOBAL_KEY, start, end, withscores=True)
        total = redis.zcard(LEADERBOARD_GLOBAL_KEY)
    except Exception as e:
        logger.error(f"get_global_rankings Redis error: {e}")
        return _fallback_db_rankings(page, limit)

    entries = _enrich_rankings(raw, offset=offset)
    entries = _attach_rank_changes(entries, LEADERBOARD_GLOBAL_KEY)

    return {
        'results': entries,
        'total': int(total),
        'page': page,
        'limit': limit,
    }


def get_weekly_rankings(page=1, limit=50):
    """
    Fetch paginated weekly leaderboard from Redis.
    Weekly key is reset every Monday via Celery beat.
    """
    limit = min(int(limit), 100)
    page = max(1, int(page))
    offset = (page - 1) * limit
    start = offset
    end = offset + limit - 1

    redis = _get_redis()
    if redis is None:
        return _fallback_db_rankings(page, limit)

    try:
        raw = redis.zrevrange(LEADERBOARD_WEEKLY_KEY, start, end, withscores=True)
        total = redis.zcard(LEADERBOARD_WEEKLY_KEY)
    except Exception as e:
        logger.error(f"get_weekly_rankings Redis error: {e}")
        return _fallback_db_rankings(page, limit)

    entries = _enrich_rankings(raw, offset=offset)
    entries = _attach_rank_changes(entries, LEADERBOARD_WEEKLY_KEY)

    return {
        'results': entries,
        'total': int(total),
        'page': page,
        'limit': limit,
    }


def get_friends_rankings(user_id, page=1, limit=50):
    """
    Rank the user among their followed users.
    Fetches followed user IDs, pulls their scores from Redis, sorts, paginates.
    """
    limit = min(int(limit), 100)
    page = max(1, int(page))

    # Collect friend IDs — use followers/following if the model exists,
    # otherwise fall back to all users for a graceful degradation.
    friend_ids = _get_friend_ids(user_id)
    if user_id not in friend_ids:
        friend_ids.append(user_id)

    redis = _get_redis()
    if redis is None:
        return {'results': [], 'total': 0, 'page': page, 'limit': limit}

    try:
        # Fetch scores for all friends in one pipeline
        pipe = redis.pipeline()
        for fid in friend_ids:
            pipe.zscore(LEADERBOARD_GLOBAL_KEY, str(fid))
        scores = pipe.execute()
    except Exception as e:
        logger.error(f"get_friends_rankings pipeline error: {e}")
        return {'results': [], 'total': 0, 'page': page, 'limit': limit}

    # Build (user_id, score) pairs, filter out None scores
    pairs = [
        (fid, float(score) if score is not None else 0.0)
        for fid, score in zip(friend_ids, scores)
    ]
    pairs.sort(key=lambda x: x[1], reverse=True)

    total = len(pairs)
    offset = (page - 1) * limit
    page_pairs = pairs[offset: offset + limit]

    # Enrich with user data
    uid_list = [p[0] for p in page_pairs]
    users_by_id = {
        u.id: u
        for u in User.objects.filter(id__in=uid_list).only(
            'id', 'username', 'xp', 'level', 'streak_days', 'avatar_url'
        )
    }

    results = []
    for idx, (uid, score) in enumerate(page_pairs):
        user = users_by_id.get(uid)
        if user is None:
            continue
        results.append({
            'rank': offset + idx + 1,
            'user_id': uid,
            'username': user.username,
            'xp': user.xp,
            'level': user.level,
            'streak_days': user.streak_days,
            'avatar_url': user.avatar_url or '',
            'score': score,
            'rank_change': None,
        })

    return {'results': results, 'total': total, 'page': page, 'limit': limit}


def get_user_rank(user_id):
    """
    Return rank, score, and percentile for a single user.

    Returns:
        dict: {rank, score, percentile, user_id} or None if not ranked.
    """
    redis = _get_redis()
    if redis is None:
        return _fallback_user_rank(user_id)

    try:
        rank_zero = redis.zrevrank(LEADERBOARD_GLOBAL_KEY, str(user_id))
        score = redis.zscore(LEADERBOARD_GLOBAL_KEY, str(user_id))
        total = redis.zcard(LEADERBOARD_GLOBAL_KEY)
    except Exception as e:
        logger.error(f"get_user_rank Redis error: {e}")
        return _fallback_user_rank(user_id)

    if rank_zero is None:
        # User not in Redis yet — compute and insert
        computed = update_leaderboard(user_id)
        if computed is None:
            return None
        return get_user_rank(user_id)

    rank = int(rank_zero) + 1
    total = int(total)
    percentile = round(((total - rank) / max(total, 1)) * 100, 1)

    return {
        'user_id': user_id,
        'rank': rank,
        'score': float(score) if score is not None else 0.0,
        'percentile': percentile,
    }


# ─── Snapshot persistence ─────────────────────────────────────────────────────

def snapshot_rankings():
    """
    Persist current Redis global rankings to LeaderboardSnapshot table.
    Called every 5 minutes by Celery beat.
    Bulk-creates snapshots for all ranked users.
    """
    from leaderboard.models import LeaderboardSnapshot

    redis = _get_redis()
    if redis is None:
        logger.warning("snapshot_rankings: Redis unavailable, skipping snapshot")
        return 0

    try:
        raw = redis.zrevrange(LEADERBOARD_GLOBAL_KEY, 0, -1, withscores=True)
    except Exception as e:
        logger.error(f"snapshot_rankings ZREVRANGE failed: {e}")
        return 0

    if not raw:
        return 0

    user_ids = []
    for member, _ in raw:
        try:
            user_ids.append(int(member))
        except (ValueError, TypeError):
            pass

    users_by_id = {
        u.id: u
        for u in User.objects.filter(id__in=user_ids).only('id', 'xp', 'streak_days')
    }

    snapshots = []
    for idx, (member, score) in enumerate(raw):
        try:
            uid = int(member)
        except (ValueError, TypeError):
            continue
        user = users_by_id.get(uid)
        if user is None:
            continue
        snapshots.append(LeaderboardSnapshot(
            user_id=uid,
            total_xp=user.xp,
            rank=idx + 1,
            streak_days=user.streak_days,
        ))

    LeaderboardSnapshot.objects.bulk_create(snapshots, batch_size=500)
    logger.info(f"snapshot_rankings: saved {len(snapshots)} entries")
    return len(snapshots)


def reset_weekly_leaderboard():
    """
    Delete the weekly Redis key to start a fresh weekly competition.
    Called every Monday at midnight via Celery beat.
    """
    redis = _get_redis()
    if redis is None:
        logger.warning("reset_weekly_leaderboard: Redis unavailable")
        return False
    try:
        redis.delete(LEADERBOARD_WEEKLY_KEY)
        logger.info("Weekly leaderboard reset")
        return True
    except Exception as e:
        logger.error(f"reset_weekly_leaderboard failed: {e}")
        return False


# ─── Fallback (no Redis) ──────────────────────────────────────────────────────

def _fallback_db_rankings(page, limit):
    """
    Fallback: rank users by XP directly from PostgreSQL when Redis is down.
    """
    offset = (page - 1) * limit
    users = User.objects.order_by('-xp')[offset: offset + limit]
    total = User.objects.count()

    results = []
    for idx, user in enumerate(users):
        results.append({
            'rank': offset + idx + 1,
            'user_id': user.id,
            'username': user.username,
            'xp': user.xp,
            'level': user.level,
            'streak_days': user.streak_days,
            'avatar_url': user.avatar_url or '',
            'score': float(user.xp),
            'rank_change': None,
        })

    return {'results': results, 'total': total, 'page': page, 'limit': limit}


def _fallback_user_rank(user_id):
    """
    Fallback: compute rank from PostgreSQL when Redis is down.
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None

    rank = User.objects.filter(xp__gt=user.xp).count() + 1
    total = User.objects.count()
    percentile = round(((total - rank) / max(total, 1)) * 100, 1)

    return {
        'user_id': user_id,
        'rank': rank,
        'score': float(user.xp),
        'percentile': percentile,
    }


def _get_friend_ids(user_id):
    """
    Return list of user IDs that the given user follows.
    Gracefully returns empty list if no follow model exists.
    """
    try:
        from users.models import UserFollow
        return list(
            UserFollow.objects.filter(follower_id=user_id)
            .values_list('following_id', flat=True)
        )
    except Exception:
        return []
