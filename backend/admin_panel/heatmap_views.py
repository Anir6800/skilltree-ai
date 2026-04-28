"""
SkillTree AI - Admin Heatmap API Views
Endpoints for quest difficulty heatmap analytics.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from skills.models import Skill
from .analytics import compute_quest_analytics, get_heatmap_summary


class IsAdminUser(permissions.BasePermission):
    """Permission class for admin users."""

    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class HeatmapAnalyticsView(APIView):
    """
    GET /api/admin/analytics/heatmap/?skill_id=X
    Get quest difficulty analytics for heatmap visualization.
    """

    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def get(self, request):
        skill_id = request.query_params.get('skill_id')

        if skill_id:
            try:
                skill_id = int(skill_id)
                skill = get_object_or_404(Skill, id=skill_id)
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Invalid skill_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        analytics_list = compute_quest_analytics(skill_id=skill_id)
        summary = get_heatmap_summary(analytics_list)

        analytics_data = [a.to_dict() for a in analytics_list]

        return Response({
            'analytics': analytics_data,
            'summary': summary,
            'skill_id': skill_id,
        })


class SkillsListView(APIView):
    """
    GET /api/admin/analytics/skills/
    Get list of all skills for dropdown selector.
    """

    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def get(self, request):
        skills = Skill.objects.all().values('id', 'title').order_by('title')
        return Response(list(skills))
