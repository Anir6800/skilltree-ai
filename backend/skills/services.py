from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from datetime import timedelta
from quests.models import QuestSubmission
from .models import SkillProgress, Skill

User = get_user_model()

def award_xp(user, quest):
    """
    Core logic for awarding XP, updating level, and tracking streaks.
    Also checks if the associated skill should be marked as completed.
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
        
        # 3. Update Level: level = xp // 500 + 1
        # The User model's save method already handles this calculation, 
        # but we can do it explicitly for the return value.
        user.save()
        
        # 4. Check Skill Completion
        skill = quest.skill
        total_quests = skill.quests.count()
        completed_quests = QuestSubmission.objects.filter(
            user=user, 
            quest__skill=skill, 
            status='passed'
        ).values('quest').distinct().count()
        
        if total_quests > 0 and completed_quests >= total_quests:
            progress, created = SkillProgress.objects.get_or_create(
                user=user, 
                skill=skill
            )
            if progress.status != 'completed':
                progress.status = 'completed'
                progress.completed_at = timezone.now()
                progress.save()

        return {
            "xp_gained": xp_gained,
            "new_total_xp": user.xp,
            "new_level": user.level,
            "streak_days": user.streak_days
        }
