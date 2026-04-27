from django.urls import path
from .views import (
    SubmissionExplanationView,
    FlaggedSubmissionsView,
    SubmissionReviewView,
)

app_name = 'ai_detection'

urlpatterns = [
    path('submissions/<int:submission_id>/explain/', SubmissionExplanationView.as_view(), name='submission_explain'),
    path('admin/flagged-submissions/', FlaggedSubmissionsView.as_view(), name='flagged_submissions'),
    path('admin/submissions/<int:submission_id>/review/', SubmissionReviewView.as_view(), name='submission_review'),
]
