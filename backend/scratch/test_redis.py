import os
import sys
import django
from django.conf import settings
from django.core.cache import cache

def test_redis_connection():
    print("--- Redis Connectivity Test ---")
    
    # 1. Test standard Django cache (which should now use django-redis)
    print(f"Testing Django cache ('default' backend: {settings.CACHES['default']['BACKEND']})...")
    try:
        cache.set('redis_test_key', 'SkillTree-AI-Success', timeout=30)
        value = cache.get('redis_test_key')
        if value == 'SkillTree-AI-Success':
            print("✅ Standard Django cache is working correctly with Redis.")
        else:
            print(f"❌ Cache mismatch: Expected 'SkillTree-AI-Success', got '{value}'")
    except Exception as e:
        print(f"❌ Standard Django cache failed: {e}")

    # 2. Test django-redis helper (used in leaderboard services)
    print("\nTesting django-redis connection helper...")
    try:
        from django_redis import get_redis_connection
        con = get_redis_connection('default')
        con.ping()
        print("✅ Raw Redis connection (get_redis_connection) is working.")
        
        # Test basic set/get on raw connection
        con.set('raw_test_key', 'Raw-Success', ex=30)
        raw_val = con.get('raw_test_key').decode('utf-8')
        if raw_val == 'Raw-Success':
            print("✅ Raw Redis set/get successful.")
        else:
             print(f"❌ Raw mismatch: Expected 'Raw-Success', got '{raw_val}'")
             
    except ImportError:
        print("❌ django-redis is not installed.")
    except Exception as e:
        print(f"❌ Raw Redis connection failed: {e}")

    print("\n--- Test Complete ---")

if __name__ == "__main__":
    test_redis_connection()
