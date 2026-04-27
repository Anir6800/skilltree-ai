"""
SkillTree AI - Skills Tasks
Re-exports Celery tasks from services so autodiscover_tasks() can find them.
"""

from celery import shared_task
from django.contrib.auth import get_user_model

# Import the shared_task so Celery registers it under 'skills.tasks'
from skills.services import resolve_unlocks_for_user  # noqa: F401

User = get_user_model()


@shared_task
def build_curriculum(user_id):
    """
    Wrapper task for curriculum generation.
    Calls the actual implementation in skills.curriculum module.
    """
    from skills.curriculum import build_curriculum as _build_curriculum_impl
    return _build_curriculum_impl(user_id)


@shared_task
def generate_personalized_path(user_id, profile_id):
    """
    Generate personalized learning path based on onboarding profile.
    """
    try:
        from users.onboarding_models import OnboardingProfile
        from skills.models import Skill, SkillProgress
        
        user = User.objects.get(id=user_id)
        profile = OnboardingProfile.objects.get(id=profile_id)
        
        category_levels = profile.category_levels
        
        # Create initial skill progress for beginner skills matching user interests
        beginner_skills = Skill.objects.filter(
            category__in=category_levels.keys(),
            difficulty__lte=2
        )[:10]
        
        for skill in beginner_skills:
            SkillProgress.objects.get_or_create(
                user=user,
                skill=skill,
                defaults={'status': 'available'}
            )
        
        profile.path_generated = True
        profile.save(update_fields=['path_generated'])
        
        # Trigger curriculum generation
        build_curriculum.delay(user.id)
        
        return {
            'status': 'success',
            'skills_unlocked': beginner_skills.count()
        }
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Path generation failed for user {user_id}: {e}", exc_info=True)
        # Mark as generated to unblock user even on failure
        try:
            from users.onboarding_models import OnboardingProfile
            OnboardingProfile.objects.filter(id=profile_id).update(path_generated=True)
        except Exception:
            pass
        return {'status': 'error', 'error': str(e)}

