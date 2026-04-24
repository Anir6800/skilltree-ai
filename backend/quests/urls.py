from django.urls import path
from .views import QuestListView, QuestDetailView, QuestSubmitView

app_name = 'quests'

urlpatterns = [
    path('', QuestListView.as_view(), name='quest_list'),
    path('<int:pk>/', QuestDetailView.as_view(), name='quest_detail'),
    path('<int:pk>/submit/', QuestSubmitView.as_view(), name='quest_submit'),
]
