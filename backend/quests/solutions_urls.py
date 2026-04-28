"""
SkillTree AI - Solutions URLs
URL routing for peer code review API endpoints.
"""

from django.urls import path
from .solutions_views import (
    ShareSolutionView,
    SolutionsListView,
    SolutionDetailView,
    SolutionDiffView,
    UpvoteSolutionView,
    AddCommentView,
    CommentsListView,
    DeleteCommentView,
    UserSolutionsView,
)

app_name = 'solutions'

urlpatterns = [
    path('', SolutionsListView.as_view(), name='solutions_list'),
    path('<int:submission_id>/share/', ShareSolutionView.as_view(), name='share_solution'),
    path('<int:solution_id>/', SolutionDetailView.as_view(), name='solution_detail'),
    path('<int:solution_id>/diff/', SolutionDiffView.as_view(), name='solution_diff'),
    path('<int:solution_id>/upvote/', UpvoteSolutionView.as_view(), name='upvote_solution'),
    path('<int:solution_id>/comments/', AddCommentView.as_view(), name='add_comment'),
    path('<int:solution_id>/comments/list/', CommentsListView.as_view(), name='comments_list'),
    path('comments/<int:comment_id>/delete/', DeleteCommentView.as_view(), name='delete_comment'),
    path('user/', UserSolutionsView.as_view(), name='user_solutions'),
]
