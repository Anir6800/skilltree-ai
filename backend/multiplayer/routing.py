from django.urls import path
from multiplayer.consumers import MatchConsumer

websocket_urlpatterns = [
    path('ws/match/<str:room_id>/', MatchConsumer.as_asgi()),
]
