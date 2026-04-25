"""
Curriculum URL Configuration
"""

from django.urls import path
from skills import curriculum_views

app_name = 'curriculum'

urlpatterns = [
    path('my-curriculum/', curriculum_views.get_my_curriculum, name='my-curriculum'),
    path('regenerate/', curriculum_views.regenerate_curriculum, name='regenerate'),
]
