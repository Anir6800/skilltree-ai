"""
AI Mentor URL Configuration
"""

from django.urls import path
from . import views

app_name = 'mentor'

urlpatterns = [
    path('chat/', views.chat, name='mentor-chat'),
    path('suggest-path/', views.suggest_path, name='mentor-suggest-path'),
    path('history/', views.history, name='mentor-history'),
    path('hint/', views.get_hint, name='mentor-hint'),
    path('hint/unlock-status/<int:quest_id>/', views.get_hint_unlock_status, name='mentor-hint-unlock-status'),
]
