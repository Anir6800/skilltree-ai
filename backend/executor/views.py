"""
Code execution API views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.cache import cache

from .serializers import ExecuteCodeSerializer, RunTestsSerializer
from .services import executor
from .ai_executor import ai_executor


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
    
    # SECURITY: Rate limiting and validation constants
    MAX_CODE_LENGTH = 50000  # 50KB
    MAX_EXECUTIONS_PER_MINUTE = 10
    MAX_EXECUTIONS_PER_HOUR = 100

    def post(self, request):
        user = request.user
        
        # SECURITY: Rate limiting (per minute)
        cache_key_minute = f'exec_rate_minute_{user.id}'
        executions_minute = cache.get(cache_key_minute, 0)
        
        if executions_minute >= self.MAX_EXECUTIONS_PER_MINUTE:
            return Response({
                'error': 'Rate limit exceeded',
                'message': f'You can only execute {self.MAX_EXECUTIONS_PER_MINUTE} times per minute.',
                'retry_after': 60
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # SECURITY: Rate limiting (per hour)
        cache_key_hour = f'exec_rate_hour_{user.id}'
        executions_hour = cache.get(cache_key_hour, 0)
        
        if executions_hour >= self.MAX_EXECUTIONS_PER_HOUR:
            return Response({
                'error': 'Rate limit exceeded',
                'message': f'You can only execute {self.MAX_EXECUTIONS_PER_HOUR} times per hour.',
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
        if len(code) > self.MAX_CODE_LENGTH:
            return Response({
                'error': 'Code too long',
                'message': f'Maximum code length is {self.MAX_CODE_LENGTH} characters.',
                'max_length': self.MAX_CODE_LENGTH
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Increment rate limit counters
        cache.set(cache_key_minute, executions_minute + 1, 60)  # 1 minute TTL
        cache.set(cache_key_hour, executions_hour + 1, 3600)  # 1 hour TTL
        
        # Execute code
        result = executor.execute(code, language, stdin_input)
        
        return Response(result, status=status.HTTP_200_OK)


class RunTestsView(APIView):
    """
    Run code against test cases
    POST /api/execute/test/
    Supports both real execution and AI simulation
    """
    permission_classes = [IsAuthenticated]
    
    # SECURITY: Rate limiting and validation constants
    MAX_CODE_LENGTH = 50000  # 50KB
    MAX_TEST_CASES = 20
    MAX_EXECUTIONS_PER_MINUTE = 10
    MAX_EXECUTIONS_PER_HOUR = 100

    def post(self, request):
        user = request.user
        
        # SECURITY: Rate limiting (per minute)
        cache_key_minute = f'test_rate_minute_{user.id}'
        executions_minute = cache.get(cache_key_minute, 0)
        
        if executions_minute >= self.MAX_EXECUTIONS_PER_MINUTE:
            return Response({
                'error': 'Rate limit exceeded',
                'message': f'You can only run tests {self.MAX_EXECUTIONS_PER_MINUTE} times per minute.',
                'retry_after': 60
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # SECURITY: Rate limiting (per hour)
        cache_key_hour = f'test_rate_hour_{user.id}'
        executions_hour = cache.get(cache_key_hour, 0)
        
        if executions_hour >= self.MAX_EXECUTIONS_PER_HOUR:
            return Response({
                'error': 'Rate limit exceeded',
                'message': f'You can only run tests {self.MAX_EXECUTIONS_PER_HOUR} times per hour.',
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
        if len(code) > self.MAX_CODE_LENGTH:
            return Response({
                'error': 'Code too long',
                'message': f'Maximum code length is {self.MAX_CODE_LENGTH} characters.',
                'max_length': self.MAX_CODE_LENGTH
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # SECURITY: Validate test case count
        if len(test_cases) > self.MAX_TEST_CASES:
            return Response({
                'error': 'Too many test cases',
                'message': f'Maximum {self.MAX_TEST_CASES} test cases allowed.',
                'max_test_cases': self.MAX_TEST_CASES
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Increment rate limit counters
        cache.set(cache_key_minute, executions_minute + 1, 60)  # 1 minute TTL
        cache.set(cache_key_hour, executions_hour + 1, 3600)  # 1 hour TTL
        
        # Choose execution method
        if use_ai_simulation:
            # Use AI simulation
            result = ai_executor.simulate_execution(code, language, test_cases)
        else:
            # Use real Docker execution
            result = executor.run_test_cases(code, language, test_cases)
            # Add is_simulated flag for consistency
            result['is_simulated'] = False
        
        return Response(result, status=status.HTTP_200_OK)
