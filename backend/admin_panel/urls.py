from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'admin_panel'

router = DefaultRouter()
router.register(r'skills', views.AdminSkillViewSet, basename='admin-skills')
router.register(r'quests', views.AdminQuestViewSet, basename='admin-quests')
router.register(r'content', views.AdminContentViewSet, basename='admin-content')
router.register(r'questions', views.AssessmentQuestionViewSet, basename='admin-questions')

urlpatterns = [
    path('stats/', views.admin_stats, name='admin-stats'),
    path('assessments/<int:question_id>/submit/', views.submit_assessment, name='submit-assessment'),
    path('assessments/submissions/<int:submission_id>/', views.get_submission_result, name='get-submission'),
    path('assessments/submissions/', views.list_user_submissions, name='list-submissions'),
    path('quests/generate/', views.generate_quest, name='generate-quest'),
    path('quests/generate-batch/', views.generate_batch_quests, name='generate-batch-quests'),
    path('quests/save-draft/', views.save_quest_draft, name='save-quest-draft'),
    path('quests/lm-studio-status/', views.check_lm_studio_status, name='lm-studio-status'),
    path('', include(router.urls)),
]
