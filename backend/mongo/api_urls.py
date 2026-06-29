"""
LIVE MongoDB-backed API routes, mounted at /api/mongo/ (see core/urls.py).
Runs alongside the legacy Django-ORM API. Frontend can be pointed here per-app
during the staged cutover; response shapes mirror the existing contract.
"""

from django.urls import path
from mongo import views

urlpatterns = [
    # Auth
    path("auth/register/", views.RegisterView.as_view(), name="mongo_register"),
    path("auth/login/", views.LoginView.as_view(), name="mongo_login"),
    path("auth/token/refresh/", views.TokenRefreshView.as_view(), name="mongo_token_refresh"),
    path("auth/logout/", views.LogoutView.as_view(), name="mongo_logout"),
    path("auth/me/", views.MeView.as_view(), name="mongo_me"),

    # Core reads
    path("skills/", views.SkillListView.as_view(), name="mongo_skills"),
    path("quests/", views.QuestListView.as_view(), name="mongo_quests"),
    path("leaderboard/", views.LeaderboardView.as_view(), name="mongo_leaderboard"),
]
