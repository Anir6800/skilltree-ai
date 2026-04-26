from django.urls import path
from leaderboard.views import LeaderboardView, MyRankView

app_name = 'leaderboard'

urlpatterns = [
    path('', LeaderboardView.as_view(), name='leaderboard'),
    path('my-rank/', MyRankView.as_view(), name='my-rank'),
]
