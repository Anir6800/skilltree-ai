#!/usr/bin/env python
"""
Script to mark admin user as onboarded
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import User
from users.onboarding_models import OnboardingProfile

username = "Anshi2007"

try:
    user = User.objects.get(username=username)
    
    # Create or update onboarding profile
    profile, created = OnboardingProfile.objects.get_or_create(
        user=user,
        defaults={
            'experience_level': 'intermediate',
            'learning_goals': ['Full Stack Development', 'System Design'],
            'preferred_languages': ['python', 'javascript'],
            'weekly_hours': 10,
            'completed': True
        }
    )
    
    if not created:
        profile.completed = True
        profile.save()
    
    print(f"✅ Admin user '{username}' marked as onboarded!")
    print(f"   - Onboarding completed: {profile.completed}")
    print(f"   - Can now access dashboard and admin panel directly")
    
except User.DoesNotExist:
    print(f"❌ User '{username}' not found!")
