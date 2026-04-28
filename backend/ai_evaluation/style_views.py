"""
SkillTree AI - Style Coach Views
API endpoints for code style analysis and reports.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from quests.models import QuestSubmission
from ai_evaluation.models import StyleReport
from ai_evaluation.serializers import StyleReportSerializer
from ai_evaluation.style_coach import style_coach
from core.lm_client import ExecutionServiceUnavailable

logger = logging.getLogger(__name__)


class StyleReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing style reports.
    Users can only see reports for their own submissions.
    """
    serializer_class = StyleReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only reports for the authenticated user's submissions."""
        return StyleReport.objects.filter(
            submission__user=self.request.user
        ).select_related('submission', 'submission__quest').order_by('-generated_at')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_style_report(request, submission_id: int):
    """
    Generate a style report for a passed quest submission.

    Only works if submission status is 'passed'.

    Request body:
    {
        "code": "source code",
        "language": "python|javascript|cpp|java|go"
    }

    Returns:
    {
        "report_id": int,
        "readability_score": 0-10,
        "naming_quality": str,
        "idiomatic_patterns": str,
        "style_issues": [...],
        "positive_patterns": [...]
    }
    """
    try:
        submission = get_object_or_404(QuestSubmission, id=submission_id)

        if submission.user != request.user:
            return Response(
                {'error': 'You do not have permission to analyze this submission'},
                status=status.HTTP_403_FORBIDDEN
            )

        if submission.status != 'passed':
            return Response(
                {'error': 'Style analysis only available for passed submissions'},
                status=status.HTTP_400_BAD_REQUEST
            )

        existing_report = StyleReport.objects.filter(submission=submission).first()
        if existing_report:
            serializer = StyleReportSerializer(existing_report)
            return Response(serializer.data, status=status.HTTP_200_OK)

        code = request.data.get('code', submission.code)
        language = request.data.get('language', submission.language)

        if not code or not language:
            return Response(
                {'error': 'Code and language are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        analysis = style_coach.analyse_style(code, language, submission.quest)

        report = StyleReport.objects.create(
            submission=submission,
            readability_score=analysis['readability_score'],
            naming_quality=analysis['naming_quality'],
            idiomatic_patterns=analysis['idiomatic_patterns'],
            style_issues=analysis['style_issues'],
            positive_patterns=analysis['positive_patterns']
        )

        serializer = StyleReportSerializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except ExecutionServiceUnavailable as e:
        return Response(
            {'error': f'Style analysis service unavailable: {str(e)}'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        logger.error(f"Failed to generate style report: {e}")
        return Response(
            {'error': 'Failed to generate style report'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_submission_style_report(request, submission_id: int):
    """
    Get style report for a specific submission.

    Returns the report if it exists, or 404 if not found.
    """
    try:
        submission = get_object_or_404(QuestSubmission, id=submission_id)

        if submission.user != request.user:
            return Response(
                {'error': 'You do not have permission to view this report'},
                status=status.HTTP_403_FORBIDDEN
            )

        report = get_object_or_404(StyleReport, submission=submission)
        serializer = StyleReportSerializer(report)
        return Response(serializer.data)

    except Exception as e:
        logger.error(f"Failed to retrieve style report: {e}")
        return Response(
            {'error': 'Failed to retrieve style report'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_style_coach_availability(request):
    """
    Check if style coach service is available.

    Returns:
    {
        "available": bool,
        "status": "ready" | "unavailable"
    }
    """
    available = style_coach.is_available()

    return Response({
        'available': available,
        'status': 'ready' if available else 'unavailable'
    }, status=status.HTTP_200_OK)
