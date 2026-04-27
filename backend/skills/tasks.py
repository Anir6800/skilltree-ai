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


@shared_task(bind=True, max_retries=2)
def generate_tree_task(self, tree_id, topic, depth):
    """
    Celery task for generating AI-powered skill trees.
    Runs asynchronously to avoid blocking the API.
    
    Args:
        tree_id: GeneratedSkillTree UUID
        topic: Learning topic
        depth: Tree depth (1-5)
    """
    try:
        from skills.ai_tree_generator import SkillTreeGeneratorService
        
        service = SkillTreeGeneratorService()
        result = service.execute_generation(tree_id, topic, depth)
        
        return result
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Tree generation task failed for tree {tree_id}: {str(e)}", exc_info=True)
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))



@shared_task(bind=True, max_retries=2)
def autofill_quests_task(self, tree_id):
    """
    Celery task for auto-filling stub quests with complete content.
    Runs asynchronously to avoid blocking the API.
    
    Args:
        tree_id: GeneratedSkillTree UUID
    """
    try:
        from skills.quest_autofill import QuestAutoFillService
        
        service = QuestAutoFillService()
        result = service.execute_autofill(tree_id)
        
        return result
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Quest auto-fill task failed for tree {tree_id}: {str(e)}", exc_info=True)
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
