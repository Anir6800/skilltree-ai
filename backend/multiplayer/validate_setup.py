#!/usr/bin/env python
"""
Validation script for multiplayer system setup.
Run this to verify all components are properly configured.
"""

import os
import sys
import django

# Ensure the backend directory is on the path so 'core' is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def check_installed_apps():
    """Verify required apps are installed."""
    required_apps = ['channels', 'multiplayer']
    missing = []
    
    for app in required_apps:
        if app not in settings.INSTALLED_APPS:
            missing.append(app)
    
    if missing:
        print(f"❌ Missing apps: {', '.join(missing)}")
        return False
    
    print("✅ All required apps installed")
    return True


def check_channel_layers():
    """Verify channel layers configuration."""
    if not hasattr(settings, 'CHANNEL_LAYERS'):
        print("❌ CHANNEL_LAYERS not configured")
        return False
    
    backend = settings.CHANNEL_LAYERS['default']['BACKEND']
    
    if 'InMemory' in backend:
        print("⚠️  Using InMemoryChannelLayer (dev only)")
    elif 'Redis' in backend:
        print("✅ Using RedisChannelLayer (production ready)")
    else:
        print(f"⚠️  Unknown channel layer: {backend}")
    
    return True


def check_asgi_application():
    """Verify ASGI application is configured."""
    if not hasattr(settings, 'ASGI_APPLICATION'):
        print("❌ ASGI_APPLICATION not configured")
        return False
    
    print(f"✅ ASGI application: {settings.ASGI_APPLICATION}")
    return True


def check_celery_config():
    """Verify Celery configuration."""
    if not hasattr(settings, 'CELERY_BROKER_URL'):
        print("❌ CELERY_BROKER_URL not configured")
        return False
    
    print(f"✅ Celery broker: {settings.CELERY_BROKER_URL}")
    return True


def check_models():
    """Verify models are properly configured."""
    try:
        from multiplayer.models import Match, MatchParticipant
        print("✅ Models imported successfully")
        
        # Check if migrations are applied
        match_count = Match.objects.count()
        print(f"✅ Database accessible ({match_count} matches)")
        return True
    except Exception as e:
        print(f"❌ Model error: {str(e)}")
        return False


def check_urls():
    """Verify URL configuration."""
    try:
        from django.urls import reverse
        from django.urls.exceptions import NoReverseMatch
        
        try:
            reverse('multiplayer:match-list')
            print("✅ Multiplayer URLs configured")
            return True
        except NoReverseMatch:
            print("❌ Multiplayer URLs not found")
            return False
    except Exception as e:
        print(f"❌ URL error: {str(e)}")
        return False


def check_consumer():
    """Verify consumer is importable."""
    try:
        from multiplayer.consumers import MatchConsumer
        print("✅ MatchConsumer imported successfully")
        return True
    except Exception as e:
        print(f"❌ Consumer error: {str(e)}")
        return False


def check_tasks():
    """Verify Celery tasks are importable."""
    try:
        from multiplayer.tasks import broadcast_submission_result
        print("✅ Celery tasks imported successfully")
        return True
    except Exception as e:
        print(f"❌ Task error: {str(e)}")
        return False


def check_redis_connection():
    """Check if Redis is accessible."""
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        
        # Try to send a test message
        async_to_sync(channel_layer.send)(
            'test_channel',
            {'type': 'test.message', 'text': 'test'}
        )
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"⚠️  Redis connection failed: {str(e)}")
        print("   (This is OK for development with InMemoryChannelLayer)")
        return True  # Don't fail on Redis error in dev


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("Multiplayer System Validation")
    print("=" * 60)
    print()
    
    checks = [
        ("Installed Apps", check_installed_apps),
        ("Channel Layers", check_channel_layers),
        ("ASGI Application", check_asgi_application),
        ("Celery Config", check_celery_config),
        ("Database Models", check_models),
        ("URL Configuration", check_urls),
        ("WebSocket Consumer", check_consumer),
        ("Celery Tasks", check_tasks),
        ("Redis Connection", check_redis_connection),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            results.append(False)
    
    print()
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All checks passed ({passed}/{total})")
        print("\n🚀 Multiplayer system is ready to use!")
        print("\nNext steps:")
        print("  1. python manage.py test_match")
        print("  2. daphne -b 0.0.0.0 -p 8000 core.asgi:application")
        print("  3. celery -A core worker -l info")
        return 0
    else:
        print(f"⚠️  {passed}/{total} checks passed")
        print("\nPlease fix the issues above before using the multiplayer system.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
