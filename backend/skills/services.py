"""
SkillTree AI - Skill Services
Core business logic for skill progression, unlocking, and completion tracking.
"""

from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models import Q, Prefetch
from datetime import timedelta
from celery import shared_task
from quests.models import QuestSubmission
from users.models import XPLog
from .models import SkillProgress, Skill

User = get_user_model()


class SkillUnlockService:
    """
    Service for managing skill unlocks based on prerequisites and XP requirements.
    """

    @staticmethod
    def get_unlockable_skills(user):
        """
        Get all skills that should be unlocked for a user based on:
        1. All prerequisite skills are completed
        2. User has sufficient XP
        
        Args:
            user: User instance
            
        Returns:
            list[Skill]: List of skills that can be unlocked
        """
        if not user or not user.id:
            return []

        # Get all skills with their prerequisites
        all_skills = Skill.objects.prefetch_related(
            'prerequisites',
            Prefetch(
                'user_progress',
                queryset=SkillProgress.objects.filter(user=user),
                to_attr='user_progress_list'
            )
        ).all()

        # Get user's completed skills for quick lookup
        completed_skill_ids = set(
            SkillProgress.objects.filter(
                user=user,
                status='completed'
            ).values_list('skill_id', flat=True)
        )

        # Get user's current progress records
        existing_progress = {
            sp.skill_id: sp.status
            for sp in SkillProgress.objects.filter(user=user).select_related('skill')
        }

        unlockable_skills = []

        for skill in all_skills:
            # Skip if already available, in progress, or completed
            current_status = existing_progress.get(skill.id, 'locked')
            if current_status in ['available', 'in_progress', 'completed']:
                continue

            # Check XP requirement
            if user.xp < skill.xp_required_to_unlock:
                continue

            # Check prerequisites
            prerequisites = skill.prerequisites.all()
            if not prerequisites.exists():
                # No prerequisites, can unlock
                unlockable_skills.append(skill)
                continue

            # Check if all prerequisites are completed
            prerequisite_ids = set(prereq.id for prereq in prerequisites)
            if prerequisite_ids.issubset(completed_skill_ids):
                unlockable_skills.append(skill)

        return unlockable_skills

    @staticmethod
    def check_skill_completion(user, skill):
        """
        Check if all quests for a skill are completed and update skill status.
        
        Args:
            user: User instance
            skill: Skill instance
            
        Returns:
            bool: True if skill was marked as completed, False otherwise
        """
        if not user or not skill:
            return False

        # Get total quests for this skill
        total_quests = skill.quests.count()
        
        if total_quests == 0:
            # No quests, cannot complete
            return False

        # Count distinct quests with passed submissions
        completed_quests = QuestSubmission.objects.filter(
            user=user,
            quest__skill=skill,
            status='passed'
        ).values('quest').distinct().count()

        # Check if all quests are completed
        if completed_quests >= total_quests:
            with transaction.atomic():
                progress, created = SkillProgress.objects.get_or_create(
                    user=user,
                    skill=skill
                )
                
                if progress.status != 'completed':
                    progress.status = 'completed'
                    progress.completed_at = timezone.now()
                    progress.save()
                    
                    # Trigger unlock resolution for dependent skills
                    resolve_unlocks_for_user.delay(user.id)
                    
                    return True

        return False


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def resolve_unlocks_for_user(self, user_id):
    """
    Celery task to resolve and unlock skills for a user.
    
    This task:
    1. Finds all skills that should be unlocked based on prerequisites and XP
    2. Creates or updates SkillProgress records to 'available' status
    3. Returns count of newly unlocked skills
    
    Args:
        user_id: ID of the user to process
        
    Returns:
        dict: {
            'user_id': int,
            'unlocked_count': int,
            'unlocked_skills': list[str]
        }
    """
    try:
        # Get user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return {
                'error': 'User not found',
                'user_id': user_id,
                'unlocked_count': 0,
                'unlocked_skills': []
            }

        # Get unlockable skills
        unlockable_skills = SkillUnlockService.get_unlockable_skills(user)

        if not unlockable_skills:
            return {
                'user_id': user_id,
                'unlocked_count': 0,
                'unlocked_skills': []
            }

        # Prepare bulk operations
        skills_to_create = []
        skills_to_update = []
        unlocked_skill_names = []

        # Get existing progress records for these skills
        existing_progress = {
            sp.skill_id: sp
            for sp in SkillProgress.objects.filter(
                user=user,
                skill__in=unlockable_skills
            ).select_related('skill')
        }

        with transaction.atomic():
            for skill in unlockable_skills:
                if skill.id in existing_progress:
                    # Update existing record
                    progress = existing_progress[skill.id]
                    if progress.status == 'locked':
                        progress.status = 'available'
                        skills_to_update.append(progress)
                        unlocked_skill_names.append(skill.title)
                else:
                    # Create new record
                    skills_to_create.append(
                        SkillProgress(
                            user=user,
                            skill=skill,
                            status='available'
                        )
                    )
                    unlocked_skill_names.append(skill.title)

            # Bulk create new progress records (ignore conflicts for safety)
            if skills_to_create:
                SkillProgress.objects.bulk_create(
                    skills_to_create,
                    ignore_conflicts=True
                )

            # Bulk update existing records
            if skills_to_update:
                SkillProgress.objects.bulk_update(
                    skills_to_update,
                    ['status']
                )

        unlocked_count = len(skills_to_create) + len(skills_to_update)

        return {
            'user_id': user_id,
            'unlocked_count': unlocked_count,
            'unlocked_skills': unlocked_skill_names
        }

    except Exception as exc:
        # Retry on failure
        raise self.retry(exc=exc)


def award_xp(user, quest):
    """
    Core logic for awarding XP, updating level, and tracking streaks.
    Also checks if the associated skill should be marked as completed.
    Triggers skill unlock resolution after XP is awarded.
    
    Args:
        user: User instance
        quest: Quest instance
        
    Returns:
        dict: {
            'xp_gained': int,
            'new_total_xp': int,
            'new_level': int,
            'streak_days': int
        }
    """
    with transaction.atomic():
        # 1. Calculate XP Gained
        xp_gained = int(quest.xp_reward * quest.difficulty_multiplier)
        user.xp += xp_gained
        
        # 2. Update Streak
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        if user.last_active == yesterday:
            user.streak_days += 1
        elif user.last_active != today:
            user.streak_days = 1
            
        user.last_active = today
        
        # 3. Create XP Log
        XPLog.objects.create(
            user=user,
            amount=xp_gained,
            source=f"Quest: {quest.title}"
        )
        
        # 4. Update Level (User model's save method handles this)
        user.save()
        
        # 5. Check Skill Completion
        skill = quest.skill
        SkillUnlockService.check_skill_completion(user, skill)
        
        # 6. Trigger unlock resolution (async)
        resolve_unlocks_for_user.delay(user.id)

        return {
            "xp_gained": xp_gained,
            "new_total_xp": user.xp,
            "new_level": user.level,
            "streak_days": user.streak_days
        }

