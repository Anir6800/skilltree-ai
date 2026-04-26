from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from functools import wraps

from skills.models import Skill, SkillProgress
from quests.models import Quest
from .models import AdminContent, AssessmentQuestion, AssessmentSubmission
from .serializers import (
    AdminSkillSerializer,
    AdminQuestSerializer,
    AdminContentSerializer,
    AssessmentQuestionSerializer,
    AssessmentQuestionCreateSerializer,
    AssessmentSubmissionSerializer,
    AssessmentSubmissionCreateSerializer
)
from .tasks import evaluate_assessment_submission
from core.lm_client import lm_client


def staff_required(view_func):
    """Decorator to ensure user is staff/admin."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        return view_func(request, *args, **kwargs)
    return wrapper


class AdminSkillViewSet(viewsets.ModelViewSet):
    """Admin CRUD for skills."""
    queryset = Skill.objects.all().prefetch_related('prerequisites', 'quests')
    serializer_class = AdminSkillSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        category = self.request.query_params.get('category', None)
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset.annotate(
            quests_count=Count('quests'),
            content_count=Count('admin_content', filter=Q(admin_content__status='published'))
        )



class AdminQuestViewSet(viewsets.ModelViewSet):
    """Admin CRUD for quests."""
    queryset = Quest.objects.all().select_related('skill')
    serializer_class = AdminQuestSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        skill_id = self.request.query_params.get('skill', None)
        quest_type = self.request.query_params.get('type', None)
        
        if skill_id:
            queryset = queryset.filter(skill_id=skill_id)
        if quest_type:
            queryset = queryset.filter(type=quest_type)
        
        return queryset.annotate(
            questions_count=Count('assessment_questions')
        )
    
    @action(detail=True, methods=['get', 'post'])
    def questions(self, request, pk=None):
        """List or add assessment questions for a quest."""
        quest = self.get_object()
        
        if request.method == 'GET':
            questions = quest.assessment_questions.all()
            serializer = AssessmentQuestionSerializer(questions, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            serializer = AssessmentQuestionSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(quest=quest)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminContentViewSet(viewsets.ModelViewSet):
    """Admin CRUD for learning content."""
    queryset = AdminContent.objects.all().select_related('skill', 'created_by')
    serializer_class = AdminContentSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        skill_id = self.request.query_params.get('skill', None)
        content_type = self.request.query_params.get('content_type', None)
        content_status = self.request.query_params.get('status', None)
        
        if skill_id:
            queryset = queryset.filter(skill_id=skill_id)
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        if content_status:
            queryset = queryset.filter(status=content_status)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Trigger AI review then publish if approved."""
        content = self.get_object()
        
        try:
            review_prompt = f"""Review this educational content for quality and accuracy:

Title: {content.title}
Type: {content.content_type}
Skill: {content.skill.title}

Content:
{content.body}

{f"Code Example ({content.language}):" if content.code_example else ""}
{content.code_example if content.code_example else ""}

Provide a brief review covering:
1. Technical accuracy
2. Clarity and readability
3. Appropriate difficulty level
4. Any improvements needed

Format: JSON with fields: approved (boolean), score (1-10), notes (string)"""

            response = lm_client.chat_completion(
                messages=[{"role": "user", "content": review_prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            review_text = lm_client.extract_content(response)
            content.ai_review_notes = review_text
            
            if '"approved": true' in review_text.lower() or '"approved":true' in review_text.lower():
                content.status = 'published'
            else:
                content.status = 'ai_reviewed'
            
            content.save()
            
            serializer = self.get_serializer(content)
            return Response({
                'message': 'Content reviewed successfully',
                'content': serializer.data
            })
            
        except Exception as e:
            return Response(
                {'error': f'AI review failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AssessmentQuestionViewSet(viewsets.ModelViewSet):
    """Admin CRUD for assessment questions."""
    queryset = AssessmentQuestion.objects.all().select_related('quest')
    serializer_class = AssessmentQuestionSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        quest_id = self.request.query_params.get('quest', None)
        question_type = self.request.query_params.get('type', None)
        
        if quest_id:
            queryset = queryset.filter(quest_id=quest_id)
        if question_type:
            queryset = queryset.filter(question_type=question_type)
        
        return queryset


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_stats(request):
    """Dashboard statistics for admin panel."""
    
    total_skills = Skill.objects.count()
    total_quests = Quest.objects.count()
    published_content = AdminContent.objects.filter(status='published').count()
    pending_review = AdminContent.objects.filter(status='draft').count()
    
    content_by_category = list(
        AdminContent.objects.filter(status='published')
        .values('skill__category')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    content_by_type = list(
        AdminContent.objects.values('content_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    recent_content = AdminContent.objects.select_related('skill', 'created_by').order_by('-created_at')[:10]
    recent_content_data = AdminContentSerializer(recent_content, many=True).data
    
    return Response({
        'total_skills': total_skills,
        'total_quests': total_quests,
        'published_content': published_content,
        'pending_review': pending_review,
        'content_by_category': content_by_category,
        'content_by_type': content_by_type,
        'recent_content': recent_content_data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_assessment(request, question_id):
    """
    Submit an answer to an assessment question.
    Triggers async evaluation via Celery.
    """
    from django.utils import timezone
    from datetime import timedelta
    
    question = get_object_or_404(AssessmentQuestion, id=question_id)
    
    # SECURITY: Verify user has access to the quest
    quest = question.quest
    skill = quest.skill
    
    # Check if skill is unlocked
    try:
        skill_progress = SkillProgress.objects.get(user=request.user, skill=skill)
        if skill_progress.status == 'locked':
            return Response({
                'error': 'This assessment is locked. Unlock the skill first.',
                'skill_required': skill.title
            }, status=status.HTTP_403_FORBIDDEN)
    except SkillProgress.DoesNotExist:
        return Response({
            'error': 'Skill not started. Start the skill first.',
            'skill_required': skill.title
        }, status=status.HTTP_403_FORBIDDEN)
    
    # SECURITY: Check if user already passed
    existing_passed = AssessmentSubmission.objects.filter(
        user=request.user,
        question=question,
        passed=True
    ).exists()
    
    if existing_passed:
        return Response({
            'error': 'You have already passed this assessment.',
            'message': 'You cannot resubmit a passed assessment.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # SECURITY: Rate limiting (max 5 submissions per hour per question)
    one_hour_ago = timezone.now() - timedelta(hours=1)
    recent_submissions = AssessmentSubmission.objects.filter(
        user=request.user,
        question=question,
        submitted_at__gte=one_hour_ago
    ).count()
    
    if recent_submissions >= 5:
        return Response({
            'error': 'Rate limit exceeded.',
            'message': 'You can only submit 5 times per hour. Please wait before trying again.',
            'retry_after': 3600  # seconds
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    # Validate input
    serializer = AssessmentSubmissionCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Create submission
    submission = AssessmentSubmission.objects.create(
        user=request.user,
        question=question,
        answer=serializer.validated_data['answer'],
        status='pending'
    )
    
    # Trigger async evaluation
    evaluate_assessment_submission.delay(submission.id)
    
    return Response({
        'submission_id': submission.id,
        'status': 'evaluating',
        'message': 'Your submission is being evaluated. You will receive results shortly.'
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_submission_result(request, submission_id):
    """
    Poll for assessment submission result.
    """
    submission = get_object_or_404(
        AssessmentSubmission,
        id=submission_id,
        user=request.user
    )
    
    serializer = AssessmentSubmissionSerializer(submission)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_user_submissions(request):
    """
    List all submissions for the authenticated user.
    """
    question_id = request.query_params.get('question', None)
    
    submissions = AssessmentSubmission.objects.filter(user=request.user)
    
    if question_id:
        submissions = submissions.filter(question_id=question_id)
    
    submissions = submissions.select_related('question', 'question__quest').order_by('-submitted_at')
    
    serializer = AssessmentSubmissionSerializer(submissions, many=True)
    return Response(serializer.data)
