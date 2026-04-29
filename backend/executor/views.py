"""
Code execution API views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.cache import cache
from django.conf import settings
from django.shortcuts import get_object_or_404

from .serializers import ExecuteCodeSerializer, RunTestsSerializer
from .services import executor
from .ai_executor import ai_executor
from .pipeline import run_submission_pipeline


class ExecutorHealthView(APIView):
    """
    Check health status of execution services
    GET /api/execute/health/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        docker_available = executor._check_docker_available()
        ai_available = ai_executor.is_available()
        
        return Response({
            "docker_executor": {
                "available": docker_available,
                "status": "healthy" if docker_available else "unavailable"
            },
            "ai_simulator": {
                "available": ai_available,
                "status": "healthy" if ai_available else "unavailable"
            },
            "overall_status": "healthy" if (docker_available or ai_available) else "degraded"
        }, status=status.HTTP_200_OK)


class ExecuteCodeView(APIView):
    """
    Execute code in a sandboxed environment
    POST /api/execute/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        
        # Use settings for limits
        MAX_CODE_LENGTH = settings.EXECUTOR_MAX_CODE_LENGTH
        MAX_EXECUTIONS_PER_MINUTE = settings.EXECUTOR_MAX_EXECUTIONS_PER_MINUTE
        MAX_EXECUTIONS_PER_HOUR = settings.EXECUTOR_MAX_EXECUTIONS_PER_HOUR
        
        # SECURITY: Rate limiting (per minute)
        cache_key_minute = f'exec_rate_minute_{user.id}'
        executions_minute = cache.get(cache_key_minute, 0)
        
        if executions_minute >= MAX_EXECUTIONS_PER_MINUTE:
            return Response({
                'error': 'Rate limit exceeded',
                'message': f'You can only execute {MAX_EXECUTIONS_PER_MINUTE} times per minute.',
                'retry_after': 60
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # SECURITY: Rate limiting (per hour)
        cache_key_hour = f'exec_rate_hour_{user.id}'
        executions_hour = cache.get(cache_key_hour, 0)
        
        if executions_hour >= MAX_EXECUTIONS_PER_HOUR:
            return Response({
                'error': 'Rate limit exceeded',
                'message': f'You can only execute {MAX_EXECUTIONS_PER_HOUR} times per hour.',
                'retry_after': 3600
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        serializer = ExecuteCodeSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        code = serializer.validated_data['code']
        language = serializer.validated_data['language']
        stdin_input = serializer.validated_data.get('stdin', '')
        
        # SECURITY: Validate code length
        if len(code) > MAX_CODE_LENGTH:
            return Response({
                'error': 'Code too long',
                'message': f'Maximum code length is {MAX_CODE_LENGTH} characters.',
                'max_length': MAX_CODE_LENGTH
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Increment rate limit counters
        cache.set(cache_key_minute, executions_minute + 1, 60)  # 1 minute TTL
        cache.set(cache_key_hour, executions_hour + 1, 3600)  # 1 hour TTL
        
        try:
            # Execute code with error handling
            result = executor.execute(code, language, stdin_input)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Code execution error: {e}", exc_info=True)
            
            return Response({
                'error': 'Code execution failed',
                'message': str(e),
                'output': '',
                'stderr': str(e),
                'exit_code': -1
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RunTestsView(APIView):
    """
    Run code against test cases
    POST /api/execute/test/
    Supports both real execution and AI simulation
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        
        # Use settings for limits
        MAX_CODE_LENGTH = settings.EXECUTOR_MAX_CODE_LENGTH
        MAX_TEST_CASES = settings.EXECUTOR_MAX_TEST_CASES
        MAX_EXECUTIONS_PER_MINUTE = settings.EXECUTOR_MAX_EXECUTIONS_PER_MINUTE
        MAX_EXECUTIONS_PER_HOUR = settings.EXECUTOR_MAX_EXECUTIONS_PER_HOUR
        
        # SECURITY: Rate limiting (per minute)
        cache_key_minute = f'test_rate_minute_{user.id}'
        executions_minute = cache.get(cache_key_minute, 0)
        
        if executions_minute >= MAX_EXECUTIONS_PER_MINUTE:
            return Response({
                'error': 'Rate limit exceeded',
                'message': f'You can only run tests {MAX_EXECUTIONS_PER_MINUTE} times per minute.',
                'retry_after': 60
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # SECURITY: Rate limiting (per hour)
        cache_key_hour = f'test_rate_hour_{user.id}'
        executions_hour = cache.get(cache_key_hour, 0)
        
        if executions_hour >= MAX_EXECUTIONS_PER_HOUR:
            return Response({
                'error': 'Rate limit exceeded',
                'message': f'You can only run tests {MAX_EXECUTIONS_PER_HOUR} times per hour.',
                'retry_after': 3600
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        serializer = RunTestsSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        code = serializer.validated_data['code']
        language = serializer.validated_data['language']
        test_cases = serializer.validated_data['test_cases']
        use_ai_simulation = serializer.validated_data.get('use_ai_simulation', False)
        
        # SECURITY: Validate code length
        if len(code) > MAX_CODE_LENGTH:
            return Response({
                'error': 'Code too long',
                'message': f'Maximum code length is {MAX_CODE_LENGTH} characters.',
                'max_length': MAX_CODE_LENGTH
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # SECURITY: Validate test case count
        if len(test_cases) > MAX_TEST_CASES:
            return Response({
                'error': 'Too many test cases',
                'message': f'Maximum {MAX_TEST_CASES} test cases allowed.',
                'max_test_cases': MAX_TEST_CASES
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Increment rate limit counters
        cache.set(cache_key_minute, executions_minute + 1, 60)  # 1 minute TTL
        cache.set(cache_key_hour, executions_hour + 1, 3600)  # 1 hour TTL

        try:
            # Choose execution method with timeout protection
            if use_ai_simulation:
                # Use AI simulation
                result = ai_executor.simulate_execution(code, language, test_cases)
            else:
                # Use real Docker execution with timeout
                try:
                    result = executor.run_test_cases(code, language, test_cases)
                    # Add is_simulated flag for consistency
                    result['is_simulated'] = False
                except Exception as e:
                    # If Docker fails, fall back to AI simulation
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Docker execution failed: {e}, falling back to AI simulation")
                    
                    if ai_executor.is_available():
                        result = ai_executor.simulate_execution(code, language, test_cases)
                        result['is_simulated'] = True
                        result['warning'] = 'Docker unavailable, using AI simulation'
                    else:
                        return Response({
                            'error': 'Execution service unavailable',
                            'message': 'Both Docker and AI simulation are unavailable',
                            'details': str(e)
                        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Test execution error: {e}", exc_info=True)
            
            return Response({
                'error': 'Test execution failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SubmissionStatusView(APIView):
    """
    Poll submission status and results.
    GET /api/execute/status/<submission_id>/
    
    Returns current submission state including:
    - Execution results (output, exit code, test results)
    - AI feedback and evaluation score
    - AI detection score and flagged status
    - Overall submission status
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id):
        from quests.models import QuestSubmission
        submission = get_object_or_404(
            QuestSubmission,
            id=submission_id,
            user=request.user  # Ownership check
        )
        
        # Calculate progress based on status
        progress_map = {
            'pending': 0,
            'running': 25,
            'passed': 100,
            'failed': 100,
            'flagged': 100,
            'explanation_provided': 100,
            'approved': 100,
            'confirmed_ai': 100,
        }
        
        return Response({
            'id': submission.id,
            'status': submission.status,
            'progress_percent': progress_map.get(submission.status, 0),
            'execution_result': submission.execution_result,
            'ai_feedback': submission.ai_feedback,
            'ai_detection_score': submission.ai_detection_score,
            'quest': {
                'id': submission.quest.id,
                'title': submission.quest.title,
                'type': submission.quest.type,
                'xp_reward': submission.quest.xp_reward,
                'difficulty_multiplier': submission.quest.difficulty_multiplier,
                'skill': {
                    'id': submission.quest.skill.id,
                    'title': submission.quest.skill.title,
                },
            },
            'created_at': submission.created_at.isoformat(),
        })


class PipelineStatusView(APIView):
    """
    Check Celery task status for submission pipeline.
    GET /api/execute/pipeline-status/<task_id>/
    
    Returns:
    - Celery task state (PENDING, STARTED, SUCCESS, FAILURE, RETRY)
    - Progress percentage based on current step
    - Current step information
    - Result data if task is complete
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        from celery.result import AsyncResult
        from quests.models import QuestSubmission
        
        # SECURITY: Verify user owns the submission associated with this task
        try:
            submission = QuestSubmission.objects.get(
                celery_task_id=task_id,
                user=request.user
            )
        except QuestSubmission.DoesNotExist:
            return Response(
                {'error': 'Task not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get Celery task result
        task_result = AsyncResult(task_id)
        
        # Map Celery states to progress
        state_progress = {
            'PENDING': 0,
            'STARTED': 15,
            'RETRY': 15,
            'SUCCESS': 100,
            'FAILURE': 100,
        }
        
        response_data = {
            'task_id': task_id,
            'status': task_result.state,
            'progress_percent': state_progress.get(task_result.state, 0),
        }
        
        # Add result if available
        if task_result.state == 'SUCCESS':
            response_data['result'] = task_result.result
        elif task_result.state == 'FAILURE':
            response_data['error'] = str(task_result.info)
        elif task_result.state in ['STARTED', 'RETRY']:
            # Try to get current step info from task info
            if task_result.info and isinstance(task_result.info, dict):
                response_data['current_step'] = task_result.info.get('step')
                response_data['step_name'] = task_result.info.get('step_name')
        
        return Response(response_data)


class StartPipelineView(APIView):
    """
    Start the full 7-step submission pipeline.
    POST /api/execute/start-pipeline/
    
    Request body:
    {
        'submission_id': int
    }
    
    Returns:
    {
        'task_id': str,
        'submission_id': int,
        'status': 'started'
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from quests.models import QuestSubmission
        
        submission_id = request.data.get('submission_id')
        
        if not submission_id:
            return Response(
                {'error': 'submission_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            submission = QuestSubmission.objects.get(
                id=submission_id,
                user=request.user
            )
        except QuestSubmission.DoesNotExist:
            return Response(
                {'error': 'Submission not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # SECURITY: Validate submission state - prevent duplicate starts
        if submission.status == 'running':
            return Response(
                {'error': 'Submission is already being evaluated'},
                status=status.HTTP_409_CONFLICT
            )
        
        if submission.status in ['passed', 'failed', 'flagged']:
            return Response(
                {'error': 'Submission has already been evaluated'},
                status=status.HTTP_409_CONFLICT
            )
        
        # Update submission status to running
        submission.status = 'running'
        submission.save(update_fields=['status'])
        
        # Start the pipeline
        try:
            result = run_submission_pipeline(submission_id)
            
            return Response({
                'task_id': result.id,
                'submission_id': submission_id,
                'status': 'started'
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            submission.status = 'pending'
            submission.save(update_fields=['status'])
            
            return Response(
                {'error': f'Failed to start pipeline: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
