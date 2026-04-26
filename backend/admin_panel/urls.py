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
    path('', include(router.urls)),
]
