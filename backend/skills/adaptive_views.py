"""
SkillTree AI - Adaptive Profile API Views
REST endpoints for adaptive learning profile and skill flags.
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from users.models_adaptive import AdaptiveProfile, UserSkillFlag
from skills.models import Skill
from skills.adaptive_serializers import AdaptiveProfileSerializer, UserSkillFlagSerializer
from skills.adaptive_engine import AdaptiveTreeEngine

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_adaptive_profile(request):
    """
    GET /api/skills/adaptive-profile/
    Returns user's adaptive profile with ability score, preferred difficulty, and flags.
    """
    try:
        profile = AdaptiveProfile.objects.get(user=request.user)
    except AdaptiveProfile.DoesNotExist:
        profile = AdaptiveProfile.objects.create(user=request.user)

    serializer = AdaptiveProfileSerializer(profile)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_skill_flags(request):
    """
    GET /api/skills/adaptive-profile/flags/
    Returns all flags for user's skills.
    """
    flags = UserSkillFlag.objects.filter(user=request.user).select_related('skill')
    serializer = UserSkillFlagSerializer(flags, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_skill_flags_by_type(request, flag_type: str):
    """
    GET /api/skills/adaptive-profile/flags/{flag_type}/
    Returns flags of a specific type (too_easy, struggling, mastered).
    """
    valid_flags = ['too_easy', 'struggling', 'mastered']
    if flag_type not in valid_flags:
        return Response(
            {'error': f'Invalid flag type. Must be one of: {", ".join(valid_flags)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    flags = UserSkillFlag.objects.filter(
        user=request.user,
        flag=flag_type
    ).select_related('skill')
    serializer = UserSkillFlagSerializer(flags, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_tree_adaptation(request):
    """
    POST /api/skills/adaptive-profile/adapt/
    Manually trigger tree adaptation for the current user.
    """
    try:
        engine = AdaptiveTreeEngine(request.user.id)
        changes = engine.adapt_tree_for_user()

        return Response(
            {
                'status': 'success',
                'message': 'Tree adaptation triggered',
                'changes': changes,
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Failed to adapt tree for user {request.user.id}: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_performance_signals(request):
    """
    GET /api/skills/adaptive-profile/signals/
    Returns current performance signals for the user.
    """
    try:
        engine = AdaptiveTreeEngine(request.user.id)
        signals = engine.collect_performance_signals()

        return Response(
            {
                'status': 'success',
                'signals': signals,
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Failed to collect signals for user {request.user.id}: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_skill_flag(request, skill_id: int, flag_type: str):
    """
    POST /api/skills/adaptive-profile/flags/{skill_id}/{flag_type}/clear/
    Clear a specific flag for a skill.
    """
    try:
        skill = get_object_or_404(Skill, id=skill_id)
        flag = get_object_or_404(
            UserSkillFlag,
            user=request.user,
            skill=skill,
            flag=flag_type
        )
        flag.delete()

        return Response(
            {'status': 'success', 'message': f'Flag {flag_type} cleared for skill {skill.title}'},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Failed to clear flag for user {request.user.id}: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
