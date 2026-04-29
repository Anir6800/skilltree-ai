from django.urls import path
from .views import DashboardView, MeView, BadgeListView

app_name = 'users'

urlpatterns = [
    path('me/', MeView.as_view(), name='users_me'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('badges/', BadgeListView.as_view(), name='badges'),
]
