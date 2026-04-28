from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # SimpleJWT token endpoints (referenced by frontend constants as /api/token/)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Custom App APIs
    path('api/auth/', include('auth_app.urls', namespace='auth_app')),
    path('api/users/', include('users.urls', namespace='users')),
    path('api/onboarding/', include('users.onboarding_urls', namespace='onboarding')),
    path('api/skills/', include('skills.urls', namespace='skills')),
    path('api/curriculum/', include('skills.curriculum_urls', namespace='curriculum')),
    path('api/quests/', include('quests.urls', namespace='quests')),
    path('api/leaderboard/', include('leaderboard.urls', namespace='leaderboard')),
    path('api/execute/', include('executor.urls', namespace='executor')),
    path('api/mentor/', include('mentor.urls', namespace='mentor')),
    path('api/admin/', include('admin_panel.urls', namespace='admin_panel')),
    path('api/ai-detection/', include('ai_detection.urls', namespace='ai_detection')),
    path('api/ai-evaluation/', include('ai_evaluation.quote_urls', namespace='quotes')),
    path('api/', include('multiplayer.urls', namespace='multiplayer')),
]

# Serve media and static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
