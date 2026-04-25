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
]
