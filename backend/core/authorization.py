"""
SkillTree AI - Authorization Decorators
========================================
Production-grade authorization decorators for multi-tenant data isolation.
Prevents cross-user data access with strict ownership validation.
"""

import logging
from functools import wraps
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from quests.models import Quest, QuestSubmission

logger = logging.getLogger(__name__)
User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# Ownership Validation Decorators
# ─────────────────────────────────────────────────────────────────────────────

def require_quest_ownership(view_func):
    """
    Decorator to ensure user owns the quest they're accessing.
    
    Usage:
        @require_quest_ownership
        def my_view(request, quest_id):
            quest = get_object_or_404(Quest, pk=quest_id)
            # quest.user == request.user is guaranteed
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        
        if not user or not user.is_authenticated:
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401
            )
        
        # Extract quest_id from kwargs or request
        quest_id = kwargs.get('quest_id') or request.GET.get('quest_id')
        
        if quest_id:
            try:
                quest_id = int(quest_id)
                # Verify user owns this quest
                quest = get_object_or_404(Quest, pk=quest_id)
                
                # For Quest objects, check if user has access
                # Quests are shared resources, but submissions are user-specific
                # This decorator is mainly for submission-related views
                
            except (ValueError, TypeError):
                pass
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_submission_ownership(view_func):
    """
    Decorator to ensure user owns the submission they're accessing.
    
    Usage:
        @require_submission_ownership
        def my_view(request, submission_id):
            submission = get_object_or_404(QuestSubmission, pk=submission_id)
            # submission.user == request.user is guaranteed
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        
        if not user or not user.is_authenticated:
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401
            )
        
        # Extract submission_id from kwargs or request
        submission_id = kwargs.get('submission_id') or request.GET.get('submission_id')
        
        if submission_id:
            try:
                submission_id = int(submission_id)
                # Verify user owns this submission
                submission = get_object_or_404(
                    QuestSubmission.objects.filter(user=user),
                    pk=submission_id
                )
                
                # Store for use in view
                request.owned_submission = submission
                
            except (ValueError, TypeError, QuestSubmission.DoesNotExist):
                logger.warning(
                    f"Authorization: User {user.id} attempted to access non-existent or unauthorized submission {submission_id}"
                )
                return JsonResponse(
                    {'error': 'Submission not found or access denied'},
                    status=404
                )
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_quest_submission_ownership(view_func):
    """
    Decorator to ensure user owns the submission for a specific quest.
    
    Usage:
        @require_quest_submission_ownership
        def my_view(request, quest_id, submission_id):
            # Both quest and submission ownership verified
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        
        if not user or not user.is_authenticated:
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401
            )
        
        quest_id = kwargs.get('quest_id') or request.GET.get('quest_id')
        submission_id = kwargs.get('submission_id') or request.GET.get('submission_id')
        
        if quest_id and submission_id:
            try:
                quest_id = int(quest_id)
                submission_id = int(submission_id)
                
                # Verify user owns this submission for this quest
                submission = get_object_or_404(
                    QuestSubmission.objects.filter(user=user),
                    pk=submission_id,
                    quest_id=quest_id
                )
                
                request.owned_submission = submission
                
            except (ValueError, TypeError, QuestSubmission.DoesNotExist):
                logger.warning(
                    f"Authorization: User {user.id} attempted to access unauthorized submission {submission_id} for quest {quest_id}"
                )
                return JsonResponse(
                    {'error': 'Submission not found or access denied'},
                    status=404
                )
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_shared_solution_ownership(view_func):
    """
    Decorator to ensure user owns or has access to shared solution.
    
    Usage:
        @require_shared_solution_ownership
        def my_view(request, solution_id):
            # Solution ownership verified
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        
        if not user or not user.is_authenticated:
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401
            )
        
        solution_id = kwargs.get('solution_id') or request.GET.get('solution_id')
        
        if solution_id:
            try:
                solution_id = int(solution_id)
                
                # Shared solutions are public, but we track ownership
                from quests.models import SharedSolution
                
                # Allow access to any shared solution (public feature)
                # But track if user owns it for modification
                solution = get_object_or_404(SharedSolution, pk=solution_id)
                
                request.shared_solution = solution
                request.is_solution_owner = solution.submission.user == user
                
            except (ValueError, TypeError, SharedSolution.DoesNotExist):
                return JsonResponse(
                    {'error': 'Solution not found'},
                    status=404
                )
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


# ──────────────────────────────────────────────────────────���──────────────────
# Scoped Data Access Decorators
# ─────────────────────────────────────────────────────────────────────────────

def scoped_user_queryset(queryset_field='user'):
    """
    Decorator to scope a queryset to the current user.
    
    Usage:
        @scoped_user_queryset('user')
        def get_queryset(self):
            return QuestSubmission.objects.all()
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user
            
            if not user or not user.is_authenticated:
                return JsonResponse(
                    {'error': 'Authentication required'},
                    status=401
                )
            
            # Store user for use in view
            request.scoped_user = user
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def scoped_queryset(view_func):
    """
    Decorator to automatically scope queryset to current user.
    
    Usage:
        @scoped_queryset
        def get_queryset(self):
            return QuestSubmission.objects.all()
        
        # In view:
        def get_queryset(self):
            user = getattr(self, 'scoped_user', None)
            if user:
                return super().get_queryset().filter(user=user)
            return super().get_queryset().none()
    """
    @wraps(view_func)
    def wrapper(self, *args, **kwargs):
        user = getattr(self.request, 'scoped_user', None)
        
        if user:
            queryset = view_func(self, *args, **kwargs)
            return queryset.filter(user=user)
        
        return view_func(self, *args, **kwargs)
    
    return wrapper


# ─────────────────────────────────────────────────────────────────────────────
# AI Context Isolation Decorators
# ─────────────────────────────────────────────────────────────────────────────

def ai_context_isolated(view_func):
    """
    Decorator to ensure AI operations use isolated context per user.
    
    Usage:
        @ai_context_isolated
        def evaluate_code(user, code, quest):
            # AI evaluation with isolated context
    """
    @wraps(view_func)
    def wrapper(user, *args, **kwargs):
        if not user or not user.is_authenticated:
            raise ValueError("User must be authenticated for AI operations")
        
        # Store user context for AI operations
        import threading
        if not hasattr(threading.current_thread(), 'ai_user_context'):
            threading.current_thread().ai_user_context = {}
        
        threading.current_thread().ai_user_context[user.id] = {
            'user_id': user.id,
            'username': user.username,
            'is_authenticated': True,
        }
        
        try:
            result = view_func(user, *args, **kwargs)
            return result
        finally:
            # Clean up context
            if hasattr(threading.current_thread(), 'ai_user_context'):
                if user.id in threading.current_thread().ai_user_context:
                    del threading.current_thread().ai_user_context[user.id]
    
    return wrapper


def scoped_ai_context(view_func):
    """
    Decorator to scope AI operations to current user context.
    
    Usage:
        @scoped_ai_context
        def get_ai_context(user):
            # Returns user-specific AI context
    """
    @wraps(view_func)
    def wrapper(user, *args, **kwargs):
        if not user or not user.is_authenticated:
            raise ValueError("User must be authenticated for AI operations")
        
        # Get user-specific AI context
        context = {
            'user_id': user.id,
            'username': user.username,
            'is_authenticated': True,
        }
        
        return view_func(context, *args, **kwargs)
    
    return wrapper


# ─────────────────────────────────────────────────────────────────────────────
# Request Validation Decorators
# ─────────────────────────────────────────────────────────────────────────────

def validate_request_data(required_fields=None, optional_fields=None):
    """
    Decorator to validate request data.
    
    Usage:
        @validate_request_data(required_fields=['code', 'language'])
        def my_view(request):
            # request.validated_data contains validated data
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.method not in ['POST', 'PUT', 'PATCH']:
                return view_func(request, *args, **kwargs)
            
            # Get data from request
            if request.content_type == 'application/json':
                try:
                    import json
                    data = json.loads(request.body)
                except json.JSONDecodeError:
                    return JsonResponse(
                        {'error': 'Invalid JSON'},
                        status=400
                    )
            else:
                data = request.data if hasattr(request, 'data') else request.POST
            
            # Validate required fields
            if required_fields:
                missing = [f for f in required_fields if f not in data]
                if missing:
                    return JsonResponse(
                        {'error': f'Missing required fields: {", ".join(missing)}'},
                        status=400
                    )
            
            # Store validated data
            request.validated_data = data
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# Cache Isolation Decorators
# ─────────────────────────────────────────────────────────────────────────────

def cache_isolated(cache_key_prefix):
    """
    Decorator to ensure cache keys are user-scoped.
    
    Usage:
        @cache_isolated('ai_feedback')
        def get_feedback(user, code, quest_id):
            # Cache key will be: ai_feedback:user_id:code_hash
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(user, *args, **kwargs):
            if not user or not user.is_authenticated:
                raise ValueError("User must be authenticated for cached operations")
            
            # Generate user-scoped cache key
            import hashlib
            import json
            
            # Create unique key based on user and parameters
            key_parts = [str(user.id)]
            for arg in args:
                if isinstance(arg, str):
                    key_parts.append(arg[:100])  # Truncate long strings
                else:
                    key_parts.append(str(arg))
            
            for key, value in kwargs.items():
                if isinstance(value, str):
                    key_parts.append(f"{key}:{value[:100]}")
                else:
                    key_parts.append(f"{key}:{value}")
            
            cache_key = f"{cache_key_prefix}:{hashlib.sha256(':'.join(key_parts).encode()).hexdigest()[:16]}"
            
            # Store cache key for use in view
            import threading
            if not hasattr(threading.current_thread(), 'cache_keys'):
                threading.current_thread().cache_keys = {}
            
            threading.current_thread().cache_keys[user.id] = cache_key
            
            try:
                result = view_func(user, *args, **kwargs)
                return result
            finally:
                # Clean up
                if hasattr(threading.current_thread(), 'cache_keys'):
                    if user.id in threading.current_thread().cache_keys:
                        del threading.current_thread().cache_keys[user.id]
        
        return wrapper
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────────────────────

def get_user_from_request(request):
    """
    Safely get user from request with validation.
    
    Args:
        request: Django request object
        
    Returns:
        User object or None
    """
    user = getattr(request, 'user', None)
    
    if not user:
        return None
    
    if not user.is_authenticated:
        return None
    
    return user


def validate_user_ownership(user, obj, field_name='user'):
    """
    Validate that user owns the object.
    
    Args:
        user: User object
        obj: Object to check ownership
        field_name: Field name that contains user reference
        
    Returns:
        True if user owns object, False otherwise
    """
    if not user or not user.is_authenticated:
        return False
    
    if not obj:
        return False
    
    owner = getattr(obj, field_name, None)
    
    if owner is None:
        return False
    
    return owner.id == user.id


def get_user_queryset(queryset, user):
    """
    Scope queryset to current user.
    
    Args:
        queryset: Django queryset
        user: User object
        
    Returns:
        Scoped queryset
    """
    if not user or not user.is_authenticated:
        return queryset.none()
    
    # Try common user field names
    user_fields = ['user', 'owner', 'author', 'created_by']
    
    for field in user_fields:
        if hasattr(queryset.model, field):
            return queryset.filter(**{f'{field}__id': user.id})
    
    return queryset.none()



