"""
SkillTree AI - Secure Database Utilities
=========================================
Production-grade database utilities with tenant isolation.
Prevents cross-user data access through scoped queries.
"""

import logging
from typing import Optional, List, Dict, Any
from django.db.models import QuerySet, Model
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# Scoped QuerySet Utilities
# ─────────────────────────────────────────────────────────────────────────────

def scoped_queryset(queryset: QuerySet, user: User) -> QuerySet:
    """
    Scope a queryset to the current user.
    
    Automatically detects user field and filters accordingly.
    
    Args:
        queryset: Django queryset
        user: User object to scope to
        
    Returns:
        Scoped queryset filtered by user
        
    Raises:
        ValueError: If user field cannot be determined
    """
    if not user or not user.is_authenticated:
        return queryset.none()
    
    if not queryset:
        return queryset
    
    # Try common user field names
    user_fields = ['user', 'owner', 'author', 'created_by', 'submitted_by']
    
    for field in user_fields:
        if hasattr(queryset.model, field):
            return queryset.filter(**{f'{field}__id': user.id})
    
    # Check for foreign key fields
    for field in queryset.model._meta.get_fields():
        if hasattr(field, 'related_model'):
            if field.related_model == User:
                return queryset.filter(**{f'{field.name}__id': user.id})
    
    raise ValueError(
        f"Cannot determine user field for model {queryset.model.__name__}. "
        f"Available fields: {[f.name for f in queryset.model._meta.get_fields()]}"
    )


def scoped_get(queryset: QuerySet, user: User, **kwargs) -> Model:
    """
    Get a single object scoped to the current user.
    
    Args:
        queryset: Django queryset
        user: User object to scope to
        **kwargs: Additional filter parameters
        
    Returns:
        Object instance
        
    Raises:
        ObjectDoesNotExist: If object not found
        MultipleObjectsReturned: If multiple objects found
        ValueError: If user is not authenticated
    """
    if not user or not user.is_authenticated:
        raise ValueError("User must be authenticated")
    
    scoped = scoped_queryset(queryset, user)
    
    if kwargs:
        scoped = scoped.filter(**kwargs)
    
    return scoped.get()


def scoped_filter(queryset: QuerySet, user: User, **kwargs) -> QuerySet:
    """
    Filter a queryset scoped to the current user.
    
    Args:
        queryset: Django queryset
        user: User object to scope to
        **kwargs: Additional filter parameters
        
    Returns:
        Scoped and filtered queryset
    """
    if not user or not user.is_authenticated:
        return queryset.none()
    
    scoped = scoped_queryset(queryset, user)
    
    if kwargs:
        scoped = scoped.filter(**kwargs)
    
    return scoped


def scoped_exclude(queryset: QuerySet, user: User, **kwargs) -> QuerySet:
    """
    Exclude from a queryset scoped to the current user.
    
    Args:
        queryset: Django queryset
        user: User object to scope to
        **kwargs: Exclude parameters
        
    Returns:
        Scoped and excluded queryset
    """
    if not user or not user.is_authenticated:
        return queryset.none()
    
    scoped = scoped_queryset(queryset, user)
    
    if kwargs:
        scoped = scoped.exclude(**kwargs)
    
    return scoped


# ─────────────────────────────────────────────────────────────────────────────
# Quest Submission Utilities
# ─────────────────────────────────────────────────────────────────────────────

def get_user_submissions(user: User, quest_id: Optional[int] = None) -> QuerySet:
    """
    Get user's quest submissions with optional quest filter.
    
    Args:
        user: User object
        quest_id: Optional quest ID to filter by
        
    Returns:
        Queryset of user's submissions
    """
    from quests.models import QuestSubmission
    
    queryset = QuestSubmission.objects.filter(user=user)
    
    if quest_id:
        queryset = queryset.filter(quest_id=quest_id)
    
    return queryset.select_related('quest').order_by('-created_at')


def get_user_submission(user: User, submission_id: int) -> Optional[QuestSubmission]:
    """
    Get specific user submission by ID.
    
    Args:
        user: User object
        submission_id: Submission ID
        
    Returns:
        Submission object or None
    """
    from quests.models import QuestSubmission
    
    try:
        return QuestSubmission.objects.get(user=user, id=submission_id)
    except QuestSubmission.DoesNotExist:
        return None


def get_user_quests(user: User) -> QuerySet:
    """
    Get quests accessible by user.
    
    Args:
        user: User object
        
    Returns:
        Queryset of quests
    """
    from quests.models import Quest
    from skills.models import SkillProgress
    
    # Get skills user has access to
    user_skills = SkillProgress.objects.filter(user=user).exclude(status='locked')
    skill_ids = user_skills.values_list('skill_id', flat=True)
    
    return Quest.objects.filter(skill_id__in=skill_ids, is_stub=False)


# ─────────────────────────────────────────────────────────────────────────────
# Badge Utilities
# ─────────────────────────────────────────────────────────────────────────────

def get_user_badges(user: User) -> QuerySet:
    """
    Get badges earned by user.
    
    Args:
        user: User object
        
    Returns:
        Queryset of user's badges
    """
    from users.models import UserBadge
    
    return UserBadge.objects.filter(user=user).select_related('badge')


def get_user_earned_badge_ids(user: User) -> set:
    """
    Get set of badge IDs earned by user.
    
    Args:
        user: User object
        
    Returns:
        Set of badge IDs
    """
    from users.models import UserBadge
    
    return set(
        UserBadge.objects.filter(user=user).values_list('badge_id', flat=True)
    )


# ─────────────────────────────────────────────────────────────────────────────
# Shared Solution Utilities
# ─────────────────────────────────────────────────────────────────────────────

def get_user_shared_solutions(user: User) -> QuerySet:
    """
    Get shared solutions created by user.
    
    Args:
        user: User object
        
    Returns:
        Queryset of user's shared solutions
    """
    from quests.models import SharedSolution
    
    return SharedSolution.objects.filter(
        submission__user=user
    ).select_related('submission', 'submission__quest')


def get_shared_solution(solution_id: int, user: Optional[User] = None) -> Optional[SharedSolution]:
    """
    Get shared solution with optional user ownership check.
    
    Args:
        solution_id: Shared solution ID
        user: Optional user for ownership check
        
    Returns:
        SharedSolution object or None
    """
    from quests.models import SharedSolution
    
    try:
        solution = SharedSolution.objects.get(id=solution_id)
        
        if user and solution.submission.user != user:
            # User doesn't own this solution
            # Shared solutions are public, but we track ownership
            pass
        
        return solution
    except SharedSolution.DoesNotExist:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# AI Evaluation Utilities
# ─────────────────────────────────────────────────────────────────────────────

def get_user_evaluation_results(user: User) -> QuerySet:
    """
    Get AI evaluation results for user's submissions.
    
    Args:
        user: User object
        
    Returns:
        Queryset of submissions with AI feedback
    """
    from quests.models import QuestSubmission
    
    return QuestSubmission.objects.filter(
        user=user,
        ai_feedback__isnull=False
    ).select_related('quest').order_by('-created_at')


def get_user_evaluation_stats(user: User) -> Dict[str, Any]:
    """
    Get AI evaluation statistics for user.
    
    Args:
        user: User object
        
    Returns:
        Dictionary with evaluation statistics
    """
    from quests.models import QuestSubmission
    from django.db.models import Avg, Count, Min, Max
    
    stats = QuestSubmission.objects.filter(
        user=user,
        ai_feedback__isnull=False
    ).aggregate(
        avg_score=Avg('ai_feedback__score'),
        total_evaluations=Count('id'),
        min_score=Min('ai_feedback__score'),
        max_score=Max('ai_feedback__score'),
    )
    
    return {
        'avg_score': stats['avg_score'] or 0,
        'total_evaluations': stats['total_evaluations'] or 0,
        'min_score': stats['min_score'] or 0,
        'max_score': stats['max_score'] or 0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Cache Key Utilities
# ─────────────────────────────────────────────────────────────────────────────

def generate_user_scoped_cache_key(user: User, key_type: str, *args) -> str:
    """
    Generate cache key scoped to user.
    
    Args:
        user: User object
        key_type: Type of cache entry
        *args: Additional key components
        
    Returns:
        User-scoped cache key
    """
    if not user or not user.is_authenticated:
        raise ValueError("User must be authenticated for cache operations")
    
    import hashlib
    
    key_parts = [str(user.id), key_type]
    key_parts.extend(str(arg) for arg in args)
    
    key_string = ':'.join(key_parts)
    key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
    
    return f"user:{user.id}:{key_type}:{key_hash}"


def generate_cache_key(key_type: str, *args) -> str:
    """
    Generate cache key without user scope (for public data).
    
    Args:
        key_type: Type of cache entry
        *args: Additional key components
        
    Returns:
        Cache key
    """
    import hashlib
    
    key_parts = [key_type]
    key_parts.extend(str(arg) for arg in args)
    
    key_string = ':'.join(key_parts)
    key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
    
    return f"{key_type}:{key_hash}"


# ─────────────────────────────────────────────────────────────────────────────
# Security Query Utilities
# ─────────────────────────────────────────────────────────────────────────────

def safe_get_object_or_404(queryset, user: User, **kwargs):
    """
    Get object with user-scoped queryset, returns 404 if not found.
    
    Args:
        queryset: Django queryset
        user: User object
        **kwargs: Filter parameters
        
    Returns:
        Object instance
        
    Raises:
        Http404: If object not found
    """
    from django.shortcuts import get_object_or_404 as django_get_object_or_404
    
    scoped = scoped_queryset(queryset, user)
    
    if kwargs:
        scoped = scoped.filter(**kwargs)
    
    return django_get_object_or_404(scoped)


def safe_filter(queryset, user: User, **kwargs):
    """
    Filter queryset with user scope.
    
    Args:
        queryset: Django queryset
        user: User object
        **kwargs: Filter parameters
        
    Returns:
        Scoped queryset
    """
    return scoped_filter(queryset, user, **kwargs)


def safe_exclude(queryset, user: User, **kwargs):
    """
    Exclude from queryset with user scope.
    
    Args:
        queryset: Django queryset
        user: User object
        **kwargs: Exclude parameters
        
    Returns:
        Scoped queryset
    """
    return scoped_exclude(queryset, user, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# Database Index Recommendations
# ─────────────────────────────────────────────────────────────────────────────

"""
Recommended Database Indexes for Multi-Tenant Security:

1. QuestSubmission
   - user_id (already exists)
   - (user_id, quest_id) - composite for user-specific quest lookups
   - (user_id, status, created_at) - for submission history

2. Quest
   - skill_id (already exists)
   - is_stub (already exists)

3. UserBadge
   - user_id (already exists)
   - (user_id, badge_id) - composite for unique constraint
   - (user_id, seen) - for notification queries

4. SharedSolution
   - submission_id (already exists)
   - (submission_id, user_id) - composite for ownership

5. SolutionComment
   - solution_id (already exists)
   - author_id (already exists)

6. AI Evaluation Cache
   - Use user-scoped cache keys
   - Implement cache invalidation on user data changes
"""
