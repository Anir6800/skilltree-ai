from django.urls import path
from .views import SkillTreeView, StartSkillView

app_name = 'skills'

urlpatterns = [
    path('tree/', SkillTreeView.as_view(), name='skill_tree'),
    path('<int:pk>/start/', StartSkillView.as_view(), name='skill_start'),
]
