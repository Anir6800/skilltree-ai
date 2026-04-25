"""
Curriculum API Views
Endpoints for fetching and regenerating user curriculum.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from skills.models import UserCurriculum
from skills.tasks import build_curriculum
from quests.models import QuestSubmission


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_curriculum(request):
    """
    Get current user's learning curriculum.
    
    GET /api/curriculum/my-curriculum/
    
    Returns: {
        "weeks": [
            {
                "week": 1,
                "focus": "Master Python fundamentals...",
                "quests": [
                    {
                        "quest_id": 1,
                        "title": "Variables and Types",
                        "skill_title": "Python Basics",
                        "est_minutes": 30,
                        "xp_reward": 100,
                        "completed": false
                    }
                ],
                "total_minutes": 180,
                "completed_count": 0,
                "total_count": 5,
                "progress_percentage": 0
            }
        ],
        "target_completion_date": "2026-06-01T00:00:00Z",
        "weekly_hours": 10,
        "total_quests": 25,
        "overall_progress": 12
    }
    """
    user = request.user
    
    try:
        curriculum = user.curriculum
    except UserCurriculum.DoesNotExist:
        # No curriculum yet, trigger generation
        try:
            build_curriculum.delay(user.id)
            return Response({
                'status': 'generating',
                'message': 'Your curriculum is being generated. Please check back in a moment.'
            }, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response({
                'error': 'Failed to generate curriculum',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Get user's completed quests
    completed_quest_ids = set(
        QuestSubmission.objects.filter(
            user=user,
            status='passed'
        ).values_list('quest_id', flat=True)
    )
    
    # Enrich weeks with completion status
    enriched_weeks = []
    total_completed = 0
    
    for week in curriculum.weeks:
        completed_count = 0
        enriched_quests = []
        
        for quest in week['quests']:
            is_completed = quest['quest_id'] in completed_quest_ids
            if is_completed:
                completed_count += 1
                total_completed += 1
            
            enriched_quests.append({
                **quest,
                'completed': is_completed
            })
        
        total_count = len(week['quests'])
        progress_percentage = (completed_count / total_count * 100) if total_count > 0 else 0
        
        enriched_weeks.append({
            'week': week['week'],
            'focus': week['focus'],
            'quests': enriched_quests,
            'total_minutes': week.get('total_minutes', 0),
            'completed_count': completed_count,
            'total_count': total_count,
            'progress_percentage': round(progress_percentage, 1)
        })
    
    overall_progress = (total_completed / curriculum.total_quests * 100) if curriculum.total_quests > 0 else 0
    
    return Response({
        'weeks': enriched_weeks,
        'target_completion_date': curriculum.target_completion_date,
        'weekly_hours': curriculum.weekly_hours,
        'total_quests': curriculum.total_quests,
        'overall_progress': round(overall_progress, 1),
        'created_at': curriculum.created_at,
        'updated_at': curriculum.updated_at
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def regenerate_curriculum(request):
    """
    Regenerate user's curriculum (e.g., after changing weekly hours).
    
    POST /api/curriculum/regenerate/
    
    Returns: {
        "status": "processing",
        "message": "Your curriculum is being regenerated..."
    }
    """
    user = request.user
    
    try:
        # Delete existing curriculum
        try:
            user.curriculum.delete()
        except UserCurriculum.DoesNotExist:
            pass
        
        # Trigger regeneration
        build_curriculum.delay(user.id)
        
        return Response({
            'status': 'processing',
            'message': 'Your curriculum is being regenerated. Refresh in a moment to see the updated plan.'
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        return Response({
            'error': 'Failed to regenerate curriculum',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
