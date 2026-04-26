"""
SkillTree AI - Leaderboard Views
REST endpoints for global, weekly, and friends leaderboards plus user rank.
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from leaderboard.services import (
    get_global_rankings,
    get_weekly_rankings,
    get_friends_rankings,
    get_user_rank,
    update_leaderboard,
)

logger = logging.getLogger(__name__)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _parse_pagination(request):
    """Parse and validate page/limit query params."""
    try:
        page = max(1, int(request.query_params.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        limit = min(100, max(1, int(request.query_params.get('limit', 50))))
    except (ValueError, TypeError):
        limit = 50
    return page, limit


# ─── Views ────────────────────────────────────────────────────────────────────

class LeaderboardView(APIView):
    """
    GET /api/leaderboard/?scope=global&page=1&limit=50
    GET /api/leaderboard/?scope=weekly
    GET /api/leaderboard/?scope=friends&user_id={id}

    scope defaults to 'global'.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        scope = request.query_params.get('scope', 'global').lower().strip()
        page, limit = _parse_pagination(request)

        if scope not in ('global', 'weekly', 'friends'):
            return Response(
                {'error': "scope must be one of: global, weekly, friends"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if scope == 'global':
                data = get_global_rankings(page=page, limit=limit)

            elif scope == 'weekly':
                data = get_weekly_rankings(page=page, limit=limit)

            else:  # friends
                # Allow fetching friends for a specific user_id (admin use),
                # otherwise default to the authenticated user.
                raw_uid = request.query_params.get('user_id')
                if raw_uid is not None:
                    try:
                        target_user_id = int(raw_uid)
                    except (ValueError, TypeError):
                        return Response(
                            {'error': 'user_id must be an integer'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                else:
                    target_user_id = request.user.id

                data = get_friends_rankings(
                    user_id=target_user_id,
                    page=page,
                    limit=limit,
                )

        except Exception as exc:
            logger.error(f"LeaderboardView error scope={scope}: {exc}", exc_info=True)
            return Response(
                {'error': 'Failed to fetch leaderboard. Please try again.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(data, status=status.HTTP_200_OK)


class MyRankView(APIView):
    """
    GET /api/leaderboard/my-rank/

    Returns the authenticated user's current rank, score, and percentile.
    Triggers a score refresh if the user is not yet in Redis.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = request.user.id

        try:
            rank_data = get_user_rank(user_id)
        except Exception as exc:
            logger.error(f"MyRankView error user={user_id}: {exc}", exc_info=True)
            return Response(
                {'error': 'Failed to fetch your rank. Please try again.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if rank_data is None:
            # User has no score yet — compute and return
            try:
                update_leaderboard(user_id)
                rank_data = get_user_rank(user_id)
            except Exception as exc:
                logger.error(f"MyRankView update failed user={user_id}: {exc}", exc_info=True)

        if rank_data is None:
            return Response(
                {'rank': None, 'score': 0, 'percentile': 0, 'user_id': user_id},
                status=status.HTTP_200_OK,
            )

        return Response(rank_data, status=status.HTTP_200_OK)
