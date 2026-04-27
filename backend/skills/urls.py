from django.urls import path
from .views import (
    SkillTreeView, StartSkillView,
    GenerateSkillTreeView, GeneratedSkillTreeListView,
    GeneratedSkillTreeDetailView, PublishSkillTreeView,
    AutoFillQuestsView
)

app_name = 'skills'

urlpatterns = [
    path('tree/', SkillTreeView.as_view(), name='skill_tree'),
    path('<int:pk>/start/', StartSkillView.as_view(), name='skill_start'),
    
    # AI Tree Generation APIs
    path('generate/', GenerateSkillTreeView.as_view(), name='generate_tree'),
    path('generated/', GeneratedSkillTreeListView.as_view(), name='generated_trees_list'),
    path('generated/<uuid:tree_id>/', GeneratedSkillTreeDetailView.as_view(), name='generated_tree_detail'),
    path('generated/<uuid:tree_id>/publish/', PublishSkillTreeView.as_view(), name='publish_tree'),
    path('generated/<uuid:tree_id>/autofill-quests/', AutoFillQuestsView.as_view(), name='autofill_quests'),
]
