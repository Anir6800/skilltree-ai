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
            'primary_goal': 'upskill',
            'target_role': 'Developer',
            'experience_years': 3,
            'category_levels': {
                'algorithms': 'intermediate',
                'ds': 'intermediate',
                'systems': 'intermediate',
                'webdev': 'intermediate',
                'aiml': 'beginner',
            },
            'selected_interests': ['full_stack', 'system_design'],
            'weekly_hours': 10,
            'path_generated': True,
        }
    )
    
    if not created:
        profile.path_generated = True
        profile.save(update_fields=['path_generated'])

    user.role = 'admin'
    user.is_staff = True
    user.is_superuser = True
    user.save()
    
    print(f"✅ Admin user '{username}' marked as onboarded!")
    print(f"   - Path generated: {profile.path_generated}")
    print(f"   - Can now access dashboard and admin panel directly")
    
except User.DoesNotExist:
    print(f"❌ User '{username}' not found!")
