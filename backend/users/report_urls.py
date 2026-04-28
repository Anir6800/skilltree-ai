"""
SkillTree AI - Report URLs
URL routing for weekly report endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.report_views import (
    WeeklyReportViewSet,
    get_latest_report,
    generate_report_now,
    get_report_stats
)

app_name = 'reports'

router = DefaultRouter()
router.register(r'', WeeklyReportViewSet, basename='weekly-report')

urlpatterns = [
    path('latest/', get_latest_report, name='latest-report'),
    path('generate/', generate_report_now, name='generate-report'),
    path('stats/', get_report_stats, name='report-stats'),
    path('', include(router.urls)),
]
