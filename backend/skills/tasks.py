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


@shared_task(bind=True, max_retries=2, time_limit=360, soft_time_limit=330)
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
    Kick off the fully AI-generated personalized roadmap for a freshly
    onboarded user. Creates the GeneratedSkillTree record (idempotent) and
    dispatches the chunked generation task.
    """
    try:
        from users.onboarding_models import OnboardingProfile
        from skills.personalized_tree import PersonalizedTreeService

        profile = OnboardingProfile.objects.select_related('generated_tree').get(id=profile_id)

        tree = profile.generated_tree
        if tree is None:
            tree = PersonalizedTreeService().create_tree_for_profile(profile)

    except Exception as exc:
        logger.error(f"[TASK] Path generation dispatch failed for user={user_id}: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))

    try:
        generate_personalized_tree_task.delay(str(tree.id))
    except Exception as exc:
        # Generation failure is recorded on the tree itself and recovered by
        # TreeGenerationStatusView auto-resume / the resume endpoint — never
        # fail onboarding over it (also keeps CELERY_TASK_ALWAYS_EAGER tests
        # from bubbling LM errors into the HTTP response).
        logger.error(f"[TASK] Tree generation errored for tree={tree.id}: {exc}", exc_info=True)

    return {'status': 'queued', 'tree_id': str(tree.id)}


@shared_task(bind=True, max_retries=3, time_limit=5400, soft_time_limit=5280)
def generate_personalized_tree_task(self, tree_id: str):
    """
    Chunked, resumable generation of a personalized roadmap.
    Idempotent — safe to re-dispatch after a crash (resume is driven by
    tree.outline['created']). Marks the tree failed only after all retries.
    """
    from celery.exceptions import MaxRetriesExceededError
    from skills.models import GeneratedSkillTree
    from skills.personalized_tree import PersonalizedTreeService

    try:
        return PersonalizedTreeService().run(tree_id)
    except Exception as exc:
        try:
            raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))
        except MaxRetriesExceededError:
            GeneratedSkillTree.objects.filter(id=tree_id).update(
                status='failed', error=str(exc)[:2000],
            )
            raise


@shared_task(bind=True, max_retries=1)
def enrich_skill_courses_task(self, skill_id: int):
    """
    Fetch and save course recommendations for a single skill.
    Used both standalone and as a fan-out worker from enrich_all_skills_courses_task.

    Args:
        skill_id: Primary key of the Skill to enrich
    """
    try:
        from skills.models import Skill
        from skills.course_fetcher import CourseFetcherService

        skill = Skill.objects.get(id=skill_id)
        fetcher = CourseFetcherService()
        courses = fetcher.fetch_courses_for_skill(skill.title, max_results=5)
        skill.courses = courses
        skill.save(update_fields=['courses', 'updated_at'])
        logger.info("[TASK] Courses enriched for skill=%d (%s): %d courses", skill_id, skill.title, len(courses))
        return {'skill_id': skill_id, 'courses_count': len(courses)}

    except Exception as exc:
        logger.error("[TASK] Course enrichment failed for skill=%d: %s", skill_id, exc, exc_info=True)
        raise self.retry(exc=exc, countdown=30)


@shared_task
def enrich_all_skills_courses_task():
    """
    Fan out enrich_skill_courses_task for every skill that has no courses yet.
    Safe to re-run — skips skills that already have courses.
    """
    from skills.models import Skill

    skill_ids = list(
        Skill.objects.filter(courses=[]).values_list('id', flat=True)
    )
    logger.info("[TASK] Enqueuing course enrichment for %d skills", len(skill_ids))
    for skill_id in skill_ids:
        enrich_skill_courses_task.delay(skill_id)
    return {'enqueued': len(skill_ids)}
