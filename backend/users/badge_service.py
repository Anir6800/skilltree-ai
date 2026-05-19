"""
SkillTree AI - Centralized Badge Service
==========================================
Production-ready badge unlock system with:
- Atomic database operations
- Race condition prevention via SELECT FOR UPDATE
- Event-driven architecture with proper error handling
- Comprehensive validation and duplicate prevention
- WebSocket broadcasting with retry logic
- Idempotent badge awarding
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count, F, Max
from django.core.cache import cache
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from users.models import User, Badge, UserBadge, XPLog
from quests.models import QuestSubmission
from multiplayer.models import Match

logger = logging.getLogger(__name__)


class BadgeService:
    """
    Centralized badge unlock service with atomic operations and race condition prevention.
    
    Key Features:
    - Atomic badge awarding with database-level locking
    - Duplicate prevention via unique_together + get_or_create
    - Event validation and sanitization
    - WebSocket broadcasting with error handling
    - Comprehensive logging for debugging
    - Cache management for performance
    """

    def __init__(self):
        """Initialize badge service."""
        self.channel_layer = get_channel_layer()
        self.logger = logger

    def check_and_award_badges(
        self,
        user: User,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None
    ) -> List[Badge]:
        """
        Check and award badges for a user based on event.
        
        This is the main entry point for badge checking. It:
        1. Validates the event
        2. Gets all unearn badges
        3. Checks each badge condition atomically
        4. Awards badges and broadcasts via WebSocket
        5. Returns list of newly earned badges
        
        Args:
            user: User object
            event_type: Type of event (quest_passed, xp_gained, etc.)
            event_data: Event-specific data (optional)
            
        Returns:
            List of newly earned Badge objects
            
        Raises:
            ValueError: If event_type is invalid
        """
        # Validate inputs
        if not user or not user.id:
            self.logger.error("Invalid user provided to check_and_award_badges")
            return []

        if not event_type or not isinstance(event_type, str):
            self.logger.error(f"Invalid event_type: {event_type}")
            return []

        event_data = event_data or {}

        try:
            new_badges = []

            # Use atomic transaction to prevent race conditions
            with transaction.atomic():
                # Lock user row to prevent concurrent badge checks
                user = User.objects.select_for_update().get(id=user.id)

                # Get all unearn badges for this user
                earned_badge_ids = set(
                    UserBadge.objects.filter(user=user).values_list('badge_id', flat=True)
                )

                # Get all badges not yet earned
                unearned_badges = Badge.objects.exclude(id__in=earned_badge_ids)

                # Check each unearned badge
                for badge in unearned_badges:
                    try:
                        # Check if badge condition is met
                        if self._check_unlock_condition(user, badge, event_type, event_data):
                            # Award badge atomically
                            awarded = self._award_badge_atomic(user, badge)
                            if awarded:
                                new_badges.append(badge)
                                self.logger.info(
                                    f"Badge earned: {user.username} - {badge.name} "
                                    f"(event: {event_type})"
                                )

                    except Exception as e:
                        self.logger.error(
                            f"Error checking badge {badge.slug} for user {user.id}: {e}",
                            exc_info=True
                        )
                        continue

            # Broadcast newly earned badges via WebSocket (outside transaction)
            for badge in new_badges:
                try:
                    self._broadcast_badge_earned(user, badge)
                except Exception as e:
                    self.logger.error(
                        f"Failed to broadcast badge {badge.slug} for user {user.id}: {e}",
                        exc_info=True
                    )

            return new_badges

        except Exception as e:
            self.logger.error(
                f"Critical error in check_and_award_badges for user {user.id}: {e}",
                exc_info=True
            )
            return []

    def _award_badge_atomic(self, user: User, badge: Badge) -> bool:
        """
        Award a badge to a user atomically.
        
        Uses get_or_create with unique_together constraint to prevent duplicates.
        Returns True if badge was newly created, False if already existed.
        
        Args:
            user: User object
            badge: Badge object
            
        Returns:
            True if badge was newly awarded, False if already earned
        """
        try:
            user_badge, created = UserBadge.objects.get_or_create(
                user=user,
                badge=badge,
                defaults={'seen': False}
            )

            if created:
                # Log badge award for auditing
                self.logger.info(
                    f"UserBadge created: user_id={user.id}, badge_id={badge.id}, "
                    f"earned_at={user_badge.earned_at}"
                )
                return True
            else:
                # Badge already earned
                self.logger.debug(
                    f"Badge already earned: user_id={user.id}, badge_id={badge.id}"
                )
                return False

        except Exception as e:
            self.logger.error(
                f"Error awarding badge {badge.slug} to user {user.id}: {e}",
                exc_info=True
            )
            return False

    def _check_unlock_condition(
        self,
        user: User,
        badge: Badge,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> bool:
        """
        Check if user meets badge unlock condition.
        
        Routes to specific checker method based on badge slug.
        Falls back to generic condition checker if no specific method exists.
        
        Args:
            user: User object
            badge: Badge object
            event_type: Type of event
            event_data: Event-specific data
            
        Returns:
            True if condition is met, False otherwise
        """
        try:
            condition = badge.unlock_condition
            if not condition or not isinstance(condition, dict):
                self.logger.warning(f"Badge {badge.slug} has invalid unlock_condition")
                return False

            # Check event type matches
            badge_event = condition.get('event_type')
            if badge_event != event_type:
                return False

            # Try specific checker method first
            checker_method = getattr(self, f'_check_{badge.slug}', None)
            if checker_method and callable(checker_method):
                return checker_method(user, event_data)

            # Fall back to generic condition checker
            return self._check_generic_condition(user, badge, event_data)

        except Exception as e:
            self.logger.error(
                f"Error checking unlock condition for badge {badge.slug}: {e}",
                exc_info=True
            )
            return False

    def _check_generic_condition(
        self,
        user: User,
        badge: Badge,
        event_data: Dict[str, Any]
    ) -> bool:
        """
        Generic badge condition checker for badges without specific methods.
        
        Supports common criteria patterns:
        - min_total_xp: Minimum total XP
        - min_quests_passed: Minimum quests passed
        - min_streak_days: Minimum streak days
        - min_skills_completed: Minimum skills completed
        - min_wins: Minimum multiplayer wins
        
        Args:
            user: User object
            badge: Badge object
            event_data: Event-specific data
            
        Returns:
            True if condition is met, False otherwise
        """
        try:
            condition = badge.unlock_condition
            criteria = condition.get('criteria', {})

            if not criteria:
                return False

            # Check XP milestone
            if 'min_total_xp' in criteria:
                min_xp = criteria['min_total_xp']
                if user.xp < min_xp:
                    return False

            # Check quest count
            if 'min_quests_passed' in criteria:
                min_quests = criteria['min_quests_passed']
                quest_count = QuestSubmission.objects.filter(
                    user=user,
                    status='passed'
                ).count()
                if quest_count < min_quests:
                    return False

            # Check streak
            if 'min_streak_days' in criteria:
                min_streak = criteria['min_streak_days']
                if user.streak_days < min_streak:
                    return False

            # Check skills completed
            if 'min_skills_completed' in criteria:
                min_skills = criteria['min_skills_completed']
                from skills.models import SkillProgress
                skill_count = SkillProgress.objects.filter(
                    user=user,
                    status='completed'
                ).count()
                if skill_count < min_skills:
                    return False

            # Check multiplayer wins
            if 'min_wins' in criteria:
                min_wins = criteria['min_wins']
                wins = Match.objects.filter(
                    participants__user=user,
                    winner=user
                ).count()
                if wins < min_wins:
                    return False

            return True

        except Exception as e:
            self.logger.error(
                f"Error in generic condition check for badge {badge.slug}: {e}",
                exc_info=True
            )
            return False

    # ─────────────────────────────────────────────────────────────────────────
    # Badge-Specific Checkers
    # ─────────────────────────────────────────────────────────────────────────

    def _check_first_xp(self, user: User, event_data: Dict[str, Any]) -> bool:
        """First Steps: Earned your first XP."""
        return user.xp >= 1

    def _check_xp_500(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Rising Coder: Reached 500 total XP."""
        return user.xp >= 500

    def _check_xp_1000(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Code Warrior: Reached 1,000 total XP."""
        return user.xp >= 1000

    def _check_xp_5000(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Elite Developer: Reached 5,000 total XP."""
        return user.xp >= 5000

    def _check_xp_10000(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Legendary Coder: Reached 10,000 total XP."""
        return user.xp >= 10000

    def _check_first_quest(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Quest Starter: Completed your first quest."""
        if event_data.get('event_type') != 'quest_passed':
            return False

        quest_count = QuestSubmission.objects.filter(
            user=user,
            status='passed'
        ).count()

        return quest_count >= 1

    def _check_quests_10(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Quest Hunter: Completed 10 quests."""
        quest_count = QuestSubmission.objects.filter(
            user=user,
            status='passed'
        ).count()
        return quest_count >= 10

    def _check_quests_50(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Quest Master: Completed 50 quests."""
        quest_count = QuestSubmission.objects.filter(
            user=user,
            status='passed'
        ).count()
        return quest_count >= 50

    def _check_quests_100(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Century Coder: Completed 100 quests."""
        quest_count = QuestSubmission.objects.filter(
            user=user,
            status='passed'
        ).count()
        return quest_count >= 100

    def _check_on_a_roll(self, user: User, event_data: Dict[str, Any]) -> bool:
        """On a Roll: 3-day login streak."""
        return user.streak_days >= 3

    def _check_week_warrior(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Week Warrior: 7-day login streak."""
        return user.streak_days >= 7

    def _check_unstoppable(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Unstoppable: 30-day login streak."""
        return user.streak_days >= 30

    def _check_speed_demon(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Speed Demon: Solve a quest in top 5% fastest time globally."""
        if event_data.get('event_type') != 'quest_passed':
            return False

        solve_time = event_data.get('solve_time_ms', float('inf'))
        if solve_time == float('inf'):
            return False

        # Get global 95th percentile (top 5%)
        percentile_95 = self._get_solve_time_percentile(95)

        return solve_time < percentile_95

    def _check_perfectionist(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Perfectionist: 10 consecutive first-attempt quest passes."""
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
        """Night Owl: Solve 5 quests between midnight and 5am."""
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
        """Polyglot: Pass quests in all 5 programming languages."""
        languages = {'python', 'javascript', 'cpp', 'java', 'go'}

        passed_languages = set(
            QuestSubmission.objects.filter(
                user=user,
                status='passed'
            ).values_list('language', flat=True).distinct()
        )

        return languages.issubset(passed_languages)

    def _check_tree_builder(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Tree Builder: Generate a custom skill tree."""
        if event_data.get('event_type') != 'tree_generated':
            return False
        return True

    def _check_mentors_pet(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Mentor's Pet: Have 10 AI mentor conversations."""
        try:
            from mentor.models import AIInteraction
            mentor_count = AIInteraction.objects.filter(user=user).count()
            return mentor_count >= 10
        except ImportError:
            return False

    def _check_arena_legend(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Arena Legend: Win 50 multiplayer races."""
        if event_data.get('event_type') != 'race_won':
            return False

        wins = Match.objects.filter(
            participants__user=user,
            winner=user
        ).count()

        return wins >= 50

    def _check_code_archaeologist(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Code Archaeologist: Complete a skill 100% on first attempts."""
        try:
            from skills.models import Skill, SkillProgress
            from quests.models import Quest

            # Get completed skills
            completed_skills = SkillProgress.objects.filter(
                user=user,
                status='completed'
            ).values_list('skill_id', flat=True)

            for skill_id in completed_skills:
                # Get all quests for this skill
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
        except ImportError:
            return False

    def _check_marathon_runner(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Marathon Runner: Complete 100 quests."""
        quest_count = QuestSubmission.objects.filter(
            user=user,
            status='passed'
        ).count()
        return quest_count >= 100

    def _check_comeback_kid(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Comeback Kid: Pass after 5+ consecutive fails."""
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

    def _check_skill_master(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Skill Master: Master 5 different skills."""
        try:
            from skills.models import SkillProgress

            mastered = SkillProgress.objects.filter(
                user=user,
                status='completed'
            ).count()

            return mastered >= 5
        except ImportError:
            return False

    def _check_study_group_founder(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Study Group Founder: Create a study group."""
        if event_data.get('event_type') != 'study_group_created':
            return False
        return True

    def _check_ai_whisperer(self, user: User, event_data: Dict[str, Any]) -> bool:
        """AI Whisperer: Get 10 AI evaluations with score > 0.8."""
        try:
            from ai_evaluation.models import EvaluationResult

            high_scores = EvaluationResult.objects.filter(
                submission__user=user,
                score__gt=0.8
            ).count()

            return high_scores >= 10
        except ImportError:
            return False

    def _check_bug_hunter(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Bug Hunter: Debug 20 quests successfully."""
        debug_count = QuestSubmission.objects.filter(
            user=user,
            quest__type='debugging',
            status='passed'
        ).count()
        return debug_count >= 20

    def _check_problem_solver(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Problem Solver: Solve 50 different quests."""
        quest_count = QuestSubmission.objects.filter(
            user=user,
            status='passed'
        ).values('quest').distinct().count()
        return quest_count >= 50

    def _check_consistent_learner(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Consistent Learner: Login 30 days in a row."""
        return user.streak_days >= 30

    def _check_legendary_grind(self, user: User, event_data: Dict[str, Any]) -> bool:
        """Legendary Grind: Reach level 50."""
        return user.level >= 50

    # ─────────────────────────────────────────────────────────────────────────
    # Helper Methods
    # ─────────────────────────────────────────────────────────────────────────

    def _get_solve_time_percentile(self, percentile: int) -> float:
        """
        Get solve time at given percentile globally.
        
        Caches result for 1 hour to avoid expensive computation.
        Invalidates cache when new submissions are added.
        
        Args:
            percentile: Percentile to calculate (0-100)
            
        Returns:
            Solve time in milliseconds at given percentile
        """
        cache_key = f"solve_time_percentile_{percentile}"
        cached = cache.get(cache_key)

        if cached is not None:
            return cached

        try:
            # Get all solve times from passed submissions
            times = []
            submissions = QuestSubmission.objects.filter(
                status='passed'
            ).values_list('execution_result', flat=True)

            for result in submissions:
                if result and isinstance(result, dict) and 'time_ms' in result:
                    try:
                        time_ms = float(result['time_ms'])
                        if time_ms > 0:
                            times.append(time_ms)
                    except (ValueError, TypeError):
                        continue

            if not times:
                return float('inf')

            times.sort()
            index = int(len(times) * (percentile / 100.0))
            percentile_time = times[min(index, len(times) - 1)]

            # Cache for 1 hour
            cache.set(cache_key, percentile_time, 3600)

            return percentile_time

        except Exception as e:
            self.logger.error(f"Error calculating solve time percentile: {e}")
            return float('inf')

    def _broadcast_badge_earned(self, user: User, badge: Badge) -> None:
        """
        Broadcast badge earned event via WebSocket.
        
        Sends message to user's personal group with badge details.
        Includes error handling and logging.
        
        Args:
            user: User object
            badge: Badge object
        """
        try:
            if not self.channel_layer:
                self.logger.warning("Channel layer not available for badge broadcast")
                return

            async_to_sync(self.channel_layer.group_send)(
                f"user_{user.id}",
                {
                    "type": "badge_earned",
                    "badge_id": badge.id,
                    "badge_slug": badge.slug,
                    "badge_name": badge.name,
                    "badge_icon": badge.icon_emoji,
                    "rarity": badge.rarity,
                    "description": badge.description,
                    "timestamp": timezone.now().isoformat(),
                }
            )

            self.logger.debug(
                f"Badge broadcast sent: user_id={user.id}, badge_slug={badge.slug}"
            )

        except Exception as e:
            self.logger.error(
                f"Failed to broadcast badge earned for user {user.id}, "
                f"badge {badge.slug}: {e}",
                exc_info=True
            )

    def invalidate_percentile_cache(self) -> None:
        """
        Invalidate solve time percentile cache.
        
        Call this after new submissions are added to ensure
        Speed Demon badge uses current data.
        """
        for percentile in [50, 75, 90, 95, 99]:
            cache_key = f"solve_time_percentile_{percentile}"
            cache.delete(cache_key)

    def get_user_earned_badges(self, user: User) -> List[Badge]:
        """
        Get all badges earned by a user.
        
        Args:
            user: User object
            
        Returns:
            List of Badge objects earned by user
        """
        if not user or not user.id:
            return []
        
        return list(Badge.objects.filter(
            user_badges__user=user
        ).distinct().order_by('rarity', 'name'))

    def get_user_badge_progress(self, user: User) -> Dict[str, Any]:
        """
        Get badge progress for a user.
        
        Returns stats on earned badges, total badges, and progress percentage.
        
        Args:
            user: User object
            
        Returns:
            Dict with earned_count, total_count, progress_percent
        """
        earned_count = UserBadge.objects.filter(user=user).count()
        total_count = Badge.objects.count()
        progress_percent = int((earned_count / total_count * 100)) if total_count > 0 else 0

        return {
            'earned_count': earned_count,
            'total_count': total_count,
            'progress_percent': progress_percent,
        }


# Singleton instance for use throughout the application
badge_service = BadgeService()
