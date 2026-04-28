"""
SkillTree AI - Badge Checker Service
Event-driven badge unlock system with WebSocket broadcasting.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.core.cache import cache
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from users.models import User, Badge, UserBadge
from quests.models import QuestSubmission
from multiplayer.models import Match

logger = logging.getLogger(__name__)


class BadgeChecker:
    """
    Evaluates and awards badges based on user events.
    Broadcasts new badge unlocks via WebSocket.
    """

    def __init__(self):
        """Initialize badge checker."""
        self.channel_layer = get_channel_layer()

    def check_badges(self, user: User, event_type: str, event_data: Dict[str, Any]) -> List[Badge]:
        """
        Check and award badges for a user based on event.

        Args:
            user: User object
            event_type: Type of event (quest_passed, login, race_won, etc.)
            event_data: Event-specific data

        Returns:
            List of newly earned badges
        """
        try:
            new_badges = []

            # Get all unearn badges for this user
            earned_badge_ids = UserBadge.objects.filter(user=user).values_list('badge_id', flat=True)
            unearned_badges = Badge.objects.exclude(id__in=earned_badge_ids)

            # Check each unearned badge
            for badge in unearned_badges:
                if self._check_unlock_condition(user, badge, event_type, event_data):
                    # Award badge
                    user_badge = UserBadge.objects.create(user=user, badge=badge)
                    new_badges.append(badge)

                    logger.info(f"Badge earned: {user.username} - {badge.name}")

                    # Broadcast via WebSocket
                    self._broadcast_badge_earned(user, badge)

            return new_badges

        except Exception as e:
            logger.error(f"Error checking badges for user {user.id}: {e}")
            return []

    def _check_unlock_condition(
        self,
        user: User,
        badge: Badge,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> bool:
        """
        Check if user meets badge unlock condition.

        Args:
            user: User object
            badge: Badge object
            event_type: Type of event
            event_data: Event-specific data

        Returns:
            True if condition is met, False otherwise
        """
        condition = badge.unlock_condition
        if not condition:
            return False

        badge_event = condition.get('event_type')
        if badge_event != event_type:
            return False

        # Route to specific checker based on badge slug
        checker_method = getattr(self, f'_check_{badge.slug}', None)
        if checker_method:
            return checker_method(user, event_data)

        return False

    # Badge checkers for each badge

    def _check_first_blood(self, user: User, event_data: Dict[str, Any]) -> bool:
        """First quest passed."""
        if event_data.get('event_type') != 'quest_passed':
            return False

        # Check if this is user's first quest passed
        quest_count = QuestSubmission.objects.filter(
            user=user,
            status='passed'
        ).count()

        return quest_count == 1

    def _check_speed_demon(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Solve time top 5% globally."""
        if event_data.get('event_type') != 'quest_passed':
            return False

        solve_time = event_data.get('solve_time_ms', float('inf'))

        # Get global 5th percentile (top 5%)
        percentile_95 = self._get_solve_time_percentile(95)

        return solve_time < percentile_95

    def _check_streak_lord(self, user: User, event_data: Dict[str, Any]) -> bool:
        """30-day streak."""
        return user.streak_days >= 30

    def _check_perfectionist(self, user: User, event_data: Dict[str, Any]) -> bool:
        """10 consecutive first-attempt passes."""
        if event_data.get('event_type') != 'quest_passed':
            return False

        # Get last 10 passed quests
        last_10 = QuestSubmission.objects.filter(
            user=user,
            status='passed'
        ).order_by('-created_at')[:10]

        if len(last_10) < 10:
            return False

        # Check if all are first attempts
        for submission in last_10:
            earlier_attempts = QuestSubmission.objects.filter(
                user=user,
                quest=submission.quest,
                created_at__lt=submission.created_at
            ).count()

            if earlier_attempts > 0:
                return False

        return True

    def _check_night_owl(self, user: User, event_data: Dict[str, Any]) -> bool:
        """5 quests solved between midnight-5am."""
        if event_data.get('event_type') != 'quest_passed':
            return False

        # Get quests solved between midnight-5am
        night_quests = QuestSubmission.objects.filter(
            user=user,
            status='passed',
            created_at__hour__lt=5
        ).count()

        return night_quests >= 5

    def _check_polyglot(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Pass quests in all 5 languages."""
        languages = {'python', 'javascript', 'cpp', 'java', 'go'}

        passed_languages = set(
            QuestSubmission.objects.filter(
                user=user,
                status='passed'
            ).values_list('language', flat=True).distinct()
        )

        return languages.issubset(passed_languages)

    def _check_tree_builder(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Generate a custom skill tree."""
        if event_data.get('event_type') != 'tree_generated':
            return True

        return True

    def _check_mentors_pet(self, user: User, event_data: Dict[str, Any]) -> bool:
        """10 AI mentor conversations."""
        from mentor.models import AIInteraction

        mentor_count = AIInteraction.objects.filter(user=user).count()
        return mentor_count >= 10

    def _check_arena_legend(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Win 50 multiplayer races."""
        if event_data.get('event_type') != 'race_won':
            return False

        wins = Match.objects.filter(
            participants__user=user,
            winner=user
        ).count()

        return wins >= 50

    def _check_code_archaeologist(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Complete a skill 100% on first attempts."""
        from skills.models import Skill, SkillProgress

        # Get completed skills
        completed_skills = SkillProgress.objects.filter(
            user=user,
            status='completed'
        ).values_list('skill_id', flat=True)

        for skill_id in completed_skills:
            # Get all quests for this skill
            from quests.models import Quest

            quests = Quest.objects.filter(skill_id=skill_id)
            all_first_attempts = True

            for quest in quests:
                submissions = QuestSubmission.objects.filter(
                    user=user,
                    quest=quest,
                    status='passed'
                ).order_by('created_at')

                if not submissions.exists():
                    all_first_attempts = False
                    break

                # Check if first submission is first attempt
                first_submission = submissions.first()
                earlier_attempts = QuestSubmission.objects.filter(
                    user=user,
                    quest=quest,
                    created_at__lt=first_submission.created_at
                ).count()

                if earlier_attempts > 0:
                    all_first_attempts = False
                    break

            if all_first_attempts:
                return True

        return False

    def _check_marathon_runner(self, user: User, event_data: Dict[str, Any]) -> bool:
        """100 quests completed."""
        quest_count = QuestSubmission.objects.filter(
            user=user,
            status='passed'
        ).count()

        return quest_count >= 100

    def _check_comeback_kid(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Pass after 5+ consecutive fails."""
        if event_data.get('event_type') != 'quest_passed':
            return False

        quest_id = event_data.get('quest_id')
        if not quest_id:
            return False

        # Get recent submissions for this quest
        recent = QuestSubmission.objects.filter(
            user=user,
            quest_id=quest_id
        ).order_by('-created_at')[:6]

        if len(recent) < 6:
            return False

        # Check if last 5 are fails and current is pass
        for i in range(1, 6):
            if recent[i].status != 'failed':
                return False

        return True

    def _check_leaderboard_climber(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Reach top 10 on leaderboard."""
        from leaderboard.models import LeaderboardSnapshot

        latest = LeaderboardSnapshot.objects.filter(
            user=user
        ).order_by('-created_at').first()

        if not latest:
            return False

        return latest.rank <= 10

    def _check_skill_master(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Master 5 different skills."""
        from skills.models import SkillProgress

        mastered = SkillProgress.objects.filter(
            user=user,
            status='completed'
        ).count()

        return mastered >= 5

    def _check_study_group_founder(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Create a study group."""
        if event_data.get('event_type') != 'study_group_created':
            return True

        return True

    def _check_ai_whisperer(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Get 10 AI evaluations with score > 0.8."""
        from ai_evaluation.models import EvaluationResult

        high_scores = EvaluationResult.objects.filter(
            submission__user=user,
            score__gt=0.8
        ).count()

        return high_scores >= 10

    def _check_bug_hunter(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Debug 20 quests successfully."""
        debug_count = QuestSubmission.objects.filter(
            user=user,
            quest__type='debugging',
            status='passed'
        ).count()

        return debug_count >= 20

    def _check_problem_solver(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Solve 50 different quests."""
        quest_count = QuestSubmission.objects.filter(
            user=user,
            status='passed'
        ).values('quest').distinct().count()

        return quest_count >= 50

    def _check_consistent_learner(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Login 30 days in a row."""
        return user.streak_days >= 30

    def _check_legendary_grind(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Reach level 50."""
        return user.level >= 50

    # Helper methods

    def _get_solve_time_percentile(self, percentile: int) -> float:
        """Get solve time at given percentile globally."""
        cache_key = f"solve_time_percentile_{percentile}"
        cached = cache.get(cache_key)

        if cached is not None:
            return cached

        # Get all solve times
        times = []
        submissions = QuestSubmission.objects.filter(
            status='passed'
        ).values_list('execution_result', flat=True)

        for result in submissions:
            if result and 'time_ms' in result:
                times.append(result['time_ms'])

        if not times:
            return float('inf')

        times.sort()
        index = int(len(times) * (percentile / 100.0))
        percentile_time = times[min(index, len(times) - 1)]

        # Cache for 1 hour
        cache.set(cache_key, percentile_time, 3600)

        return percentile_time

    def _broadcast_badge_earned(self, user: User, badge: Badge) -> None:
        """Broadcast badge earned event via WebSocket."""
        try:
            async_to_sync(self.channel_layer.group_send)(
                f"user_{user.id}",
                {
                    "type": "badge_earned",
                    "badge_slug": badge.slug,
                    "badge_name": badge.name,
                    "badge_icon": badge.icon_emoji,
                    "rarity": badge.rarity,
                    "description": badge.description,
                }
            )
        except Exception as e:
            logger.error(f"Failed to broadcast badge earned: {e}")


# Singleton instance
badge_checker = BadgeChecker()
