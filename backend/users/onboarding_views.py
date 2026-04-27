"""
Onboarding Views
Handle user onboarding flow and AI path generation.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from .onboarding_models import OnboardingProfile
from .onboarding_serializers import (
    OnboardingSubmitSerializer,
    OnboardingStatusSerializer,
    OnboardingProfileSerializer
)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_onboarding(request):
    """
    Submit onboarding profile and trigger AI path generation.
    
    POST /api/onboarding/submit/
    Body: {
        "primary_goal": "job_prep",
        "target_role": "Full Stack Developer",
        "experience_years": 2,
        "category_levels": {
            "algorithms": "intermediate",
            "ds": "beginner",
            "systems": "beginner",
            "webdev": "advanced",
            "aiml": "beginner"
        },
        "selected_interests": ["react", "nodejs", "python", "algorithms"],
        "weekly_hours": 10
    }
    
    Returns: {
        "status": "processing",
        "message": "Your personalized path is being generated..."
    }
    """
    user = request.user
    
    # Check if already completed
    if hasattr(user, 'onboarding_profile'):
        return Response({
            'error': 'Onboarding already completed',
            'status': 'completed'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate input
    serializer = OnboardingSubmitSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Create onboarding profile
        profile = OnboardingProfile.objects.create(
            user=user,
            primary_goal=serializer.validated_data['primary_goal'],
            target_role=serializer.validated_data['target_role'],
            experience_years=serializer.validated_data['experience_years'],
            category_levels=serializer.validated_data['category_levels'],
            selected_interests=serializer.validated_data['selected_interests'],
            weekly_hours=serializer.validated_data['weekly_hours'],
            generation_started_at=timezone.now()
        )
        
        # Trigger async AI path generation (Celery task)
        try:
            from skills.tasks import generate_personalized_path
            task = generate_personalized_path.delay(user.id, profile.id)
            
            return Response({
                'status': 'processing',
                'message': 'Your personalized path is being generated...',
                'profile_id': profile.id
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # SECURITY: If Celery fails, return error instead of silently marking as complete
            profile.delete()  # Clean up the profile
            return Response({
                'error': 'Path generation service unavailable',
                'message': 'Unable to generate personalized path. Please try again later.',
                'detail': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
    except Exception as e:
        return Response({
            'error': 'Failed to create onboarding profile',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def onboarding_status(request):
    """
    Get onboarding status for current user.
    
    GET /api/onboarding/status/
    
    Returns: {
        "completed": true,
        "profile": {...},
        "path_generated": true
    }
    """
    user = request.user
    
    try:
        profile = user.onboarding_profile
        profile_data = OnboardingProfileSerializer(profile).data
        
        return Response({
            'completed': True,
            'profile': profile_data,
            'path_generated': profile.path_generated
        }, status=status.HTTP_200_OK)
        
    except OnboardingProfile.DoesNotExist:
        return Response({
            'completed': False,
            'profile': None,
            'path_generated': False
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def skip_onboarding(request):
    """
    Skip onboarding and create default profile.
    
    GET /api/onboarding/skip/
    
    Returns: {
        "status": "skipped",
        "message": "Onboarding skipped"
    }
    """
    user = request.user
    
    # Check if already completed
    if hasattr(user, 'onboarding_profile'):
        return Response({
            'error': 'Onboarding already completed',
            'status': 'completed'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Create default profile
        profile = OnboardingProfile.objects.create(
            user=user,
            primary_goal='upskill',
            target_role='Developer',
            experience_years=0,
            category_levels={
                'algorithms': 'beginner',
                'ds': 'beginner',
                'systems': 'beginner',
                'webdev': 'beginner',
                'aiml': 'beginner'
            },
            selected_interests=['general'],
            weekly_hours=5,
            path_generated=True
        )
        
        return Response({
            'status': 'skipped',
            'message': 'Onboarding skipped with default settings'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': 'Failed to skip onboarding',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Update onboarding profile with generated tree info.
    
    POST /api/onboarding/update-profile/
    Body: {
        "generated_topic": "Python Basics",
        "generated_tree_id": "uuid",
        "path_generated": true
    }
    
    Returns: {
        "status": "updated",
        "profile": {...}
    }
    """
    user = request.user
    
    try:
        profile = user.onboarding_profile
    except OnboardingProfile.DoesNotExist:
        return Response({
            'error': 'Onboarding profile not found',
            'message': 'Complete onboarding first'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        # Update fields if provided
        if 'generated_topic' in request.data:
            profile.generated_topic = request.data['generated_topic']
        
        if 'generated_tree_id' in request.data:
            profile.generated_tree_id = request.data['generated_tree_id']
        
        if 'path_generated' in request.data:
            profile.path_generated = request.data['path_generated']
        
        profile.save()
        
        serializer = OnboardingProfileSerializer(profile)
        return Response({
            'status': 'updated',
            'profile': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Failed to update profile',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    """
    Get current user's onboarding profile.
    
    GET /api/onboarding/profile/
    
    Returns: {
        "id": "...",
        "primary_goal": "...",
        "generated_tree_id": "...",
        ...
    }
    """
    user = request.user
    
    try:
        profile = user.onboarding_profile
        serializer = OnboardingProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except OnboardingProfile.DoesNotExist:
        return Response({
            'error': 'Onboarding profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
