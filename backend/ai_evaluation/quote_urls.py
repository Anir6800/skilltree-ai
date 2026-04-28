"""
SkillTree AI - Quote Generator URL Configuration
REST API endpoints for motivational quotes.
"""

from django.urls import path
from ai_evaluation.quote_views import get_result_quote, check_quote_service

app_name = 'quotes'

urlpatterns = [
    # Static path must come before dynamic <int:submission_id> to avoid routing conflict
    path('quotes/service/status/', check_quote_service, name='check_quote_service'),
    path('quotes/<int:submission_id>/', get_result_quote, name='get_result_quote'),
]
