"""
SkillTree AI - Quest Completion Badge Hooks
=============================================
Integrates badge checking with quest completion flow.
Ensures badges are checked after XP is awarded and streak is updated.
"""

import logging
from django.db import transaction
from django.utils import timezone

from users.badge_service import badge_service
from quests.models import QuestSubmission

logger = logging.getLogger(__name__)


def check_badges_on_quest_completion(submission: QuestSubmission) -> list:
    """
    Check and award badges after quest completion.
    
    Called from quest completion flow after:
    - XP has been awarded
    - Streak has been updated
    - Submission status is set to 'passed'
    
    Args:
        submission: QuestSubmission object with status='passed'
        
    Returns:
        List of newly earned Badge objects
    """
    if not submission or submission.status != 'passed':
        logger.warning(f"check_badges_on_quest_completion called with invalid submission")
        return []

    try:
        user = submission.user
        quest = submission.quest

        # Prepare event data with complete information
        event_data = {
            'event_type': 'quest_passed',
            'quest_id': quest.id,
            'quest_title': quest.title,
            'submission_id': submission.id,
            'language': submission.language,
            'solve_time_ms': submission.execution_result.get('time_ms', 0) if submission.execution_result else 0,
            'created_at': submission.created_at.isoformat(),
        }

        # Check and award badges
        new_badges = badge_service.check_and_award_badges(
            user=user,
            event_type='quest_passed',
            event_data=event_data
        )

        # Invalidate percentile cache for Speed Demon badge
        if new_badges:
            badge_service.invalidate_percentile_cache()

        return new_badges

    except Exception as e:
        logger.error(
            f"Error checking badges for quest submission {submission.id}: {e}",
            exc_info=True
        )
        return []


def check_badges_on_xp_gained(user, xp_gained: int) -> list:
    """
    Check and award XP-based badges.
    
    Called after XP is awarded to user.
    
    Args:
        user: User object
        xp_gained: Amount of XP gained
        
    Returns:
        List of newly earned Badge objects
    """
    if not user or xp_gained <= 0:
        return []

    try:
        event_data = {
            'event_type': 'xp_gained',
            'xp_gained': xp_gained,
            'total_xp': user.xp,
            'new_level': user.level,
        }

        new_badges = badge_service.check_and_award_badges(
            user=user,
            event_type='xp_gained',
            event_data=event_data
        )

        return new_badges

    except Exception as e:
        logger.error(
            f"Error checking XP badges for user {user.id}: {e}",
            exc_info=True
        )
        return []


def check_badges_on_streak_update(user, streak_days: int) -> list:
    """
    Check and award streak-based badges.
    
    Called after user's streak is updated.
    
    Args:
        user: User object
        streak_days: Current streak days
        
    Returns:
        List of newly earned Badge objects
    """
    if not user or streak_days <= 0:
        return []

    try:
        event_data = {
            'event_type': 'streak_updated',
            'streak_days': streak_days,
        }

        new_badges = badge_service.check_and_award_badges(
            user=user,
            event_type='streak_updated',
            event_data=event_data
        )

        return new_badges

    except Exception as e:
        logger.error(
            f"Error checking streak badges for user {user.id}: {e}",
            exc_info=True
        )
        return []


def check_badges_on_skill_completed(user, skill) -> list:
    """
    Check and award skill completion badges.
    
    Called after user completes a skill.
    
    Args:
        user: User object
        skill: Skill object
        
    Returns:
        List of newly earned Badge objects
    """
    if not user or not skill:
        return []

    try:
        event_data = {
            'event_type': 'skill_completed',
            'skill_id': skill.id,
            'skill_title': skill.title,
        }

        new_badges = badge_service.check_and_award_badges(
            user=user,
            event_type='skill_completed',
            event_data=event_data
        )

        return new_badges

    except Exception as e:
        logger.error(
            f"Error checking skill completion badges for user {user.id}: {e}",
            exc_info=True
        )
        return []


def check_badges_on_match_won(user, match) -> list:
    """
    Check and award multiplayer match badges.
    
    Called after user wins a multiplayer match.
    
    Args:
        user: User object
        match: Match object
        
    Returns:
        List of newly earned Badge objects
    """
    if not user or not match:
        return []

    try:
        event_data = {
            'event_type': 'race_won',
            'match_id': match.id,
            'opponent_count': match.participants.count() - 1,
        }

        new_badges = badge_service.check_and_award_badges(
            user=user,
            event_type='race_won',
            event_data=event_data
        )

        return new_badges

    except Exception as e:
        logger.error(
            f"Error checking match win badges for user {user.id}: {e}",
            exc_info=True
        )
        return []
