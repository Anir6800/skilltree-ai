"""
SkillTree AI - Style Coach URLs
URL routing for style analysis endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ai_evaluation.style_views import (
    StyleReportViewSet,
    generate_style_report,
    get_submission_style_report,
    check_style_coach_availability
)

app_name = 'style'

router = DefaultRouter()
router.register(r'reports', StyleReportViewSet, basename='style-report')

urlpatterns = [
    path('', include(router.urls)),
    path('submissions/<int:submission_id>/analyze/', generate_style_report, name='generate-style-report'),
    path('submissions/<int:submission_id>/report/', get_submission_style_report, name='get-style-report'),
    # Consistent with quote service pattern: /api/style/service/status/
    path('service/status/', check_style_coach_availability, name='style-availability'),
]
