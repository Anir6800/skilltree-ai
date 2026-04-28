"""
SkillTree AI - Adaptive Profile URL Configuration
REST API endpoints for adaptive learning.
"""

from django.urls import path
from skills.adaptive_views import (
    get_adaptive_profile,
    get_skill_flags,
    get_skill_flags_by_type,
    trigger_tree_adaptation,
    get_performance_signals,
    clear_skill_flag,
)

app_name = 'adaptive'

urlpatterns = [
    # Main adaptive profile endpoint
    path('', get_adaptive_profile, name='get_adaptive_profile'),

    # Performance signals
    path('signals/', get_performance_signals, name='get_performance_signals'),

    # Skill flags
    path('flags/', get_skill_flags, name='get_skill_flags'),
    path('flags/<str:flag_type>/', get_skill_flags_by_type, name='get_skill_flags_by_type'),
    path('flags/<int:skill_id>/<str:flag_type>/clear/', clear_skill_flag, name='clear_skill_flag'),

    # Trigger adaptation
    path('adapt/', trigger_tree_adaptation, name='trigger_tree_adaptation'),
]
