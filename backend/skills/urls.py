from django.urls import path, include
from .views import (
    SkillTreeView, StartSkillView,
    GenerateSkillTreeView, GeneratedSkillTreeListView,
    GeneratedSkillTreeDetailView, PublishSkillTreeView,
    AutoFillQuestsView, SkillRadarView,
    TreeGenerationStatusView, ResumeTreeGenerationView,
)

app_name = 'skills'

urlpatterns = [
    path('tree/', SkillTreeView.as_view(), name='skill_tree'),
    path('<int:pk>/start/', StartSkillView.as_view(), name='skill_start'),
    path('radar/', SkillRadarView.as_view(), name='skill_radar'),
    
    # AI Tree Generation APIs
    path('generate/', GenerateSkillTreeView.as_view(), name='generate_tree'),
    path('generated/', GeneratedSkillTreeListView.as_view(), name='generated_trees_list'),
    path('generated/<uuid:tree_id>/', GeneratedSkillTreeDetailView.as_view(), name='generated_tree_detail'),
    path('generated/<uuid:tree_id>/status/', TreeGenerationStatusView.as_view(), name='tree_generation_status'),
    path('generated/<uuid:tree_id>/resume/', ResumeTreeGenerationView.as_view(), name='resume_tree_generation'),
    path('generated/<uuid:tree_id>/publish/', PublishSkillTreeView.as_view(), name='publish_tree'),
    path('generated/<uuid:tree_id>/autofill-quests/', AutoFillQuestsView.as_view(), name='autofill_quests'),
    
    # Adaptive Profile APIs
    path('adaptive-profile/', include('skills.adaptive_urls')),
]
