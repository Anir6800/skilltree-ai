"""
SkillTree AI – Skills Celery Tasks
All async task definitions for the skills app live here so Celery's
autodiscover_tasks() finds them in one place.

Bug fix: generate_tree_task now correctly accepts and forwards user_id.
"""

import logging
from celery import shared_task
from django.contrib.auth import get_user_model

# Re-export so Celery can discover the resolve_unlocks task
from skills.services import resolve_unlocks_for_user  # noqa: F401

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=2)
def generate_tree_task(self, tree_id: str, topic: str, depth: int, user_id: int):
    """
    Async Celery task for generating an AI-powered skill tree.

    Args:
        tree_id: GeneratedSkillTree UUID (string)
        topic: Learning topic
        depth: Tree depth 1-5
        user_id: ID of the requesting user (required by execute_generation)
    """
    try:
        from skills.ai_tree_generator import SkillTreeGeneratorService

        service = SkillTreeGeneratorService()
        result = service.execute_generation(tree_id, topic, depth, user_id)
        logger.info(f"[TASK] Tree generation complete for tree={tree_id}: {result}")
        return result

    except Exception as exc:
        logger.error(
            f"[TASK] Tree generation failed for tree={tree_id}: {exc}",
            exc_info=True,
        )
        # Exponential back-off: 60s, 120s
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=2)
def autofill_quests_task(self, tree_id: str):
    """
    Async Celery task for auto-filling stub quests with AI-generated content.

    Args:
        tree_id: GeneratedSkillTree UUID (string)
    """
    try:
        from skills.quest_autofill import QuestAutoFillService

        service = QuestAutoFillService()
        result = service.execute_autofill(tree_id)
        logger.info(f"[TASK] Quest autofill complete for tree={tree_id}: {result}")
        return result

    except Exception as exc:
        logger.error(
            f"[TASK] Quest autofill failed for tree={tree_id}: {exc}",
            exc_info=True,
        )
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def build_curriculum(user_id: int):
    """Wrapper for curriculum generation."""
    from skills.curriculum import build_curriculum as _impl
    return _impl(user_id)


@shared_task(bind=True, max_retries=2)
def generate_personalized_path(self, user_id: int, profile_id: int):
    """
    Generate personalized learning path based on onboarding profile.
    """
    try:
        from users.onboarding_models import OnboardingProfile
        from skills.models import Skill, SkillProgress

        user = User.objects.get(id=user_id)
        profile = OnboardingProfile.objects.get(id=profile_id)

        category_levels = profile.category_levels

        # Unlock beginner skills matching user interests
        beginner_skills = Skill.objects.filter(
            category__in=category_levels.keys(),
            difficulty__lte=2,
        )[:10]

        for skill in beginner_skills:
            SkillProgress.objects.get_or_create(
                user=user,
                skill=skill,
                defaults={'status': 'available'},
            )

        profile.path_generated = True
        profile.save(update_fields=['path_generated'])

        build_curriculum.delay(user.id)

        return {'status': 'success', 'skills_unlocked': beginner_skills.count()}

    except Exception as exc:
        logger.error(f"[TASK] Path generation failed for user={user_id}: {exc}", exc_info=True)
        # Mark as generated to unblock the user even on failure
        try:
            from users.onboarding_models import OnboardingProfile
            OnboardingProfile.objects.filter(id=profile_id).update(path_generated=True)
        except Exception:
            pass
        return {'status': 'error', 'error': str(exc)}
