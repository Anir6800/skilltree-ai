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
    path('update-profile/', onboarding_views.update_profile, name='update_profile'),
    path('profile/', onboarding_views.get_profile, name='get_profile'),
]
