"""
SkillTree AI - Quest Views
Quest browsing, filtering, and submission endpoints with security.
"""

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch, Case, When, Value, CharField
from .models import Quest, QuestSubmission
from .serializers import QuestListSerializer, QuestDetailSerializer, QuestSubmissionSerializer
from skills.models import Skill, SkillProgress


class QuestListView(generics.ListAPIView):
    """
    Lists quests with filtering and user status annotation.
    
    Query Parameters:
    - skill_id: Filter by skill ID
    - type: Filter by quest type (coding/debugging/mcq)
    - difficulty: Filter by difficulty (1-5)
    - status: Filter by user status (not_started/in_progress/passed)
    """
    serializer_class = QuestListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Quest.objects.select_related('skill').prefetch_related(
            Prefetch(
                'submissions',
                queryset=QuestSubmission.objects.filter(user=user).order_by('-created_at'),
                to_attr='user_submissions'
            )
        )

        # Filter by skill_id
        skill_id = self.request.query_params.get('skill_id')
        if skill_id:
            try:
                skill_id = int(skill_id)
                queryset = queryset.filter(skill_id=skill_id)
            except (ValueError, TypeError):
                pass

        # Filter by type
        quest_type = self.request.query_params.get('type')
        if quest_type and quest_type in ['coding', 'debugging', 'mcq']:
            queryset = queryset.filter(type=quest_type)

        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            try:
                difficulty = int(difficulty)
                if 1 <= difficulty <= 5:
                    queryset = queryset.filter(difficulty_multiplier=difficulty)
            except (ValueError, TypeError):
                pass

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            if status_filter == 'passed':
                queryset = queryset.filter(
                    submissions__user=user,
                    submissions__status='passed'
                ).distinct()
            elif status_filter == 'in_progress':
                queryset = queryset.filter(
                    submissions__user=user,
                    submissions__status__in=['pending', 'running']
                ).distinct()
            elif status_filter == 'not_started':
                queryset = queryset.exclude(
                    submissions__user=user
                ).distinct()

        return queryset.order_by('-xp_reward', 'id')


class QuestDetailView(generics.RetrieveAPIView):
    """
    Retrieve full quest details.
    Test cases only include input (expected_output is hidden for security).
    """
    queryset = Quest.objects.select_related('skill').all()
    serializer_class = QuestDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class QuestSubmitView(APIView):
    """
    Handles quest code submission.
    Creates a pending submission and returns immediately.
    Execution is handled asynchronously via Celery (Phase 9).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        # Validate quest exists
        quest = get_object_or_404(Quest, pk=pk)
        user = request.user
        
        # SECURITY: Check if skill is unlocked
        # Exception: multiplayer match submissions bypass the skill lock check
        # because the match creator already validated quest access
        is_match_submission = bool(request.data.get('match_id'))
        
        if not is_match_submission:
            skill = quest.skill
            try:
                skill_progress = SkillProgress.objects.get(user=user, skill=skill)
                if skill_progress.status == 'locked':
                    return Response({
                        "error": "Quest is locked",
                        "message": f"You must unlock the '{skill.title}' skill first.",
                        "skill_required": skill.title
                    }, status=status.HTTP_403_FORBIDDEN)
            except SkillProgress.DoesNotExist:
                return Response({
                    "error": "Skill not started",
                    "message": f"You must start the '{skill.title}' skill first.",
                    "skill_required": skill.title
                }, status=status.HTTP_403_FORBIDDEN)
        
        # SECURITY: Check if user already passed this quest
        existing_passed = QuestSubmission.objects.filter(
            user=user,
            quest=quest,
            status='passed'
        ).exists()
        
        if existing_passed:
            return Response({
                "error": "Quest already completed",
                "message": "You have already completed this quest. XP has been awarded."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate input data
        code = request.data.get('code', '').strip()
        language = request.data.get('language', '').strip()

        if not code:
            return Response({
                "error": "Code is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        if not language:
            return Response({
                "error": "Language is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        valid_languages = ['python', 'javascript', 'cpp', 'java', 'go']
        if language not in valid_languages:
            return Response({
                "error": f"Invalid language. Must be one of: {', '.join(valid_languages)}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # SECURITY: Validate code length (max 50KB)
        MAX_CODE_LENGTH = 50000
        if len(code) > MAX_CODE_LENGTH:
            return Response({
                "error": "Code too long",
                "message": f"Maximum code length is {MAX_CODE_LENGTH} characters.",
                "max_length": MAX_CODE_LENGTH
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create submission
        submission = QuestSubmission.objects.create(
            user=user,
            quest=quest,
            code=code,
            language=language,
            status='pending'
        )

        # Try async evaluation via Celery first, fall back to synchronous
        celery_dispatched = False
        try:
            from executor.tasks import evaluate_submission
            task = evaluate_submission.delay(submission.id)
            celery_dispatched = True
        except Exception:
            celery_dispatched = False

        if not celery_dispatched:
            # Celery unavailable — run evaluation synchronously so the user gets a result
            _evaluate_synchronously(submission)

        return Response({
            "submission_id": submission.id,
            "status": submission.status,
            "message": "Submission received and evaluated." if not celery_dispatched else "Submission queued for evaluation.",
        }, status=status.HTTP_201_CREATED)


def _evaluate_synchronously(submission):
    """
    Run code execution synchronously with AI simulation fallback when Docker is unavailable.
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        from executor.services import executor as code_executor
        from executor.ai_executor import ai_executor

        quest = submission.quest
        user = submission.user

        test_cases = [
            {
                'input': tc.get('input', ''),
                'expected': tc.get('expected_output', tc.get('expected', ''))
            }
            for tc in (quest.test_cases or [])
        ]

        submission.status = 'running'
        submission.save(update_fields=['status'])

        if test_cases:
            # Try Docker first
            result = code_executor.run_test_cases(submission.code, submission.language, test_cases)
            tests_passed = result.get('tests_passed', 0)
            tests_total = result.get('tests_total', 0)
            raw_results = result.get('results', [])

            # Detect Docker failure and fall back to AI simulation
            docker_unavailable = (
                'Docker is not available' in str(result.get('stderr', '')) or
                (tests_total > 0 and tests_passed == 0 and all(
                    'Docker is not available' in str(r.get('actual', ''))
                    for r in raw_results
                ) if raw_results else False)
            )

            if docker_unavailable and ai_executor.is_available():
                logger.info(f"Docker unavailable, using AI simulation for submission {submission.id}")
                result = ai_executor.simulate_execution(
                    submission.code, submission.language, test_cases
                )
                tests_passed = result.get('tests_passed', 0)
                tests_total = result.get('tests_total', 0)
                raw_results = result.get('results', [])

            test_results = [
                {
                    'input': r.get('input', ''),
                    'expected': r.get('expected', ''),
                    'actual': r.get('actual', ''),
                    'status': 'passed' if r.get('passed') else 'failed',
                    'time_ms': r.get('time_ms', 0),
                }
                for r in raw_results
            ]
            all_passed = tests_total > 0 and tests_passed == tests_total
        else:
            result = code_executor.execute(submission.code, submission.language)
            all_passed = result.get('status') == 'ok'
            tests_passed = 1 if all_passed else 0
            tests_total = 1
            test_results = []

        submission.execution_result = {
            'output': result.get('output', result.get('overall_assessment', '')),
            'stderr': result.get('stderr', result.get('error', '')),
            'exit_code': result.get('exit_code', 0 if all_passed else 1),
            'time_ms': result.get('execution_time_ms', 0),
            'tests_passed': tests_passed,
            'tests_total': tests_total,
            'test_results': test_results,
            'is_simulated': result.get('is_simulated', False),
        }
        submission.status = 'passed' if all_passed else 'failed'
        submission.save()

        # Award XP if passed (first time only)
        if all_passed:
            already_awarded = QuestSubmission.objects.filter(
                user=user, quest=quest, status='passed'
            ).exclude(id=submission.id).exists()

            if not already_awarded:
                xp_earned = int(quest.xp_reward * quest.difficulty_multiplier)
                user.xp += xp_earned
                user.save(update_fields=['xp', 'level'])

                from users.models import XPLog
                XPLog.objects.create(
                    user=user,
                    amount=xp_earned,
                    source=f"Quest: {quest.title}"
                )

                from django.utils import timezone
                from datetime import timedelta
                today = timezone.now().date()
                if user.last_active is None:
                    user.streak_days = 1
                elif user.last_active == today - timedelta(days=1):
                    user.streak_days += 1
                elif user.last_active != today:
                    user.streak_days = 1
                user.last_active = today
                user.save(update_fields=['streak_days', 'last_active'])

    except Exception as e:
        logger.error(f"Synchronous evaluation failed for submission {submission.id}: {e}", exc_info=True)
        submission.status = 'failed'
        submission.execution_result = {'stderr': str(e), 'test_results': []}
        submission.save()


class QuestSubmissionHistoryView(generics.ListAPIView):
    """
    Returns submission history for a specific quest.
    Only returns submissions from the current user.
    """
    serializer_class = QuestSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        quest_id = self.kwargs.get('pk')
        user = self.request.user
        
        # Validate quest exists
        get_object_or_404(Quest, pk=quest_id)
        
        # Return only user's submissions for this quest
        return QuestSubmission.objects.filter(
            user=user,
            quest_id=quest_id
        ).select_related('quest').order_by('-created_at')

