from django.urls import path
from .views import DashboardView, MeView

app_name = 'users'

urlpatterns = [
    path('me/', MeView.as_view(), name='users_me'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]
