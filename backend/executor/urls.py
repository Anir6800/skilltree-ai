"""
URL configuration for executor app
"""

from django.urls import path
from .views import ExecuteCodeView, RunTestsView, ExecutorHealthView

app_name = 'executor'

urlpatterns = [
    path('', ExecuteCodeView.as_view(), name='execute'),
    path('test/', RunTestsView.as_view(), name='run_tests'),
    path('health/', ExecutorHealthView.as_view(), name='health'),
]
