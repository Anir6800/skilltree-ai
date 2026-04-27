"""
URL configuration for executor app
"""

from django.urls import path
from .views import (
    ExecuteCodeView,
    RunTestsView,
    ExecutorHealthView,
    SubmissionStatusView,
    PipelineStatusView,
    StartPipelineView,
)

app_name = 'executor'

urlpatterns = [
    path('', ExecuteCodeView.as_view(), name='execute'),
    path('test/', RunTestsView.as_view(), name='run_tests'),
    path('health/', ExecutorHealthView.as_view(), name='health'),
    path('status/<int:submission_id>/', SubmissionStatusView.as_view(), name='submission_status'),
    path('pipeline-status/<str:task_id>/', PipelineStatusView.as_view(), name='pipeline_status'),
    path('start-pipeline/', StartPipelineView.as_view(), name='start_pipeline'),
]
