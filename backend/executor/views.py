"""
Code execution API views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

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

    def post(self, request):
        serializer = ExecuteCodeSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        code = serializer.validated_data['code']
        language = serializer.validated_data['language']
        stdin_input = serializer.validated_data.get('stdin', '')
        
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

    def post(self, request):
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
