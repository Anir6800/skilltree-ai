"""
Onboarding URL Configuration
"""

from django.urls import path
from . import onboarding_views

app_name = 'onboarding'

urlpatterns = [
    path('submit/', onboarding_views.submit_onboarding, name='submit'),
    path('status/', onboarding_views.onboarding_status, name='status'),
    path('skip/', onboarding_views.skip_onboarding, name='skip'),
]
