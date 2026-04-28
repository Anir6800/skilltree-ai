"""
SkillTree AI - Study Group URLs
URL routing for study group API endpoints.
"""

from django.urls import path
from .groups_views import (
    CreateGroupView,
    JoinGroupView,
    MyGroupView,
    GroupLeaderboardView,
    GroupGoalsView,
    GroupMessagesView,
    LeaveGroupView,
)

app_name = 'groups'

urlpatterns = [
    path('create/', CreateGroupView.as_view(), name='create_group'),
    path('join/', JoinGroupView.as_view(), name='join_group'),
    path('my-group/', MyGroupView.as_view(), name='my_group'),
    path('<int:group_id>/leaderboard/', GroupLeaderboardView.as_view(), name='group_leaderboard'),
    path('<int:group_id>/goals/', GroupGoalsView.as_view(), name='group_goals'),
    path('<int:group_id>/messages/', GroupMessagesView.as_view(), name='group_messages'),
    path('<int:group_id>/leave/', LeaveGroupView.as_view(), name='leave_group'),
]
