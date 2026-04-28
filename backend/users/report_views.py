"""
SkillTree AI - Report Views
API endpoints for weekly reports.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from pathlib import Path

from users.models import WeeklyReport
from users.serializers import WeeklyReportSerializer
from users.tasks import generate_report_for_user

logger = logging.getLogger(__name__)


class WeeklyReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing weekly reports.
    Users can only see their own reports.
    """
    serializer_class = WeeklyReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only reports for the authenticated user."""
        return WeeklyReport.objects.filter(user=self.request.user).order_by('-generated_at')

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download PDF for a specific report.

        Returns the PDF file for download.
        """
        report = self.get_object()

        if report.user != request.user:
            return Response(
                {'error': 'You do not have permission to download this report'},
                status=status.HTTP_403_FORBIDDEN
            )

        pdf_path = Path(report.pdf_path)
        if not pdf_path.exists():
            return Response(
                {'error': 'PDF file not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        report.mark_viewed()

        try:
            return FileResponse(
                open(pdf_path, 'rb'),
                as_attachment=True,
                filename=f"weekly_report_week_{report.week_number}.pdf"
            )
        except Exception as e:
            logger.error(f"Failed to download report {pk}: {e}")
            return Response(
                {'error': 'Failed to download report'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def mark_viewed(self, request, pk=None):
        """Mark a report as viewed."""
        report = self.get_object()

        if report.user != request.user:
            return Response(
                {'error': 'You do not have permission to view this report'},
                status=status.HTTP_403_FORBIDDEN
            )

        report.mark_viewed()

        serializer = self.get_serializer(report)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_latest_report(request):
    """
    Get the latest weekly report for the authenticated user.

    Returns the most recent report or 404 if none exists.
    """
    report = WeeklyReport.objects.filter(user=request.user).first()

    if not report:
        return Response(
            {'error': 'No reports available yet'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = WeeklyReportSerializer(report)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_report_now(request):
    """
    Manually trigger report generation for the authenticated user.

    Returns task ID for tracking.
    """
    try:
        task = generate_report_for_user.delay(request.user.id)

        return Response({
            'task_id': task.id,
            'status': 'generating',
            'message': 'Report generation started. Check back in a few moments.'
        }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        logger.error(f"Failed to trigger report generation: {e}")
        return Response(
            {'error': 'Failed to start report generation'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_report_stats(request):
    """
    Get summary stats for user's reports.

    Returns count of reports, latest report date, etc.
    """
    reports = WeeklyReport.objects.filter(user=request.user)
    total_reports = reports.count()
    latest_report = reports.first()

    stats = {
        'total_reports': total_reports,
        'latest_report': None,
        'unviewed_count': reports.filter(viewed_at__isnull=True).count()
    }

    if latest_report:
        stats['latest_report'] = {
            'week_number': latest_report.week_number,
            'generated_at': latest_report.generated_at,
            'viewed_at': latest_report.viewed_at,
            'xp_earned': latest_report.data.get('xp_earned', 0),
            'quests_passed': latest_report.data.get('quests_passed', 0),
            'win_rate': latest_report.data.get('win_rate', 0)
        }

    return Response(stats)
