#!/usr/bin/env python
"""
Script to create an admin user for SkillTree AI
Reads credentials from environment variables (.env file)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import User
from users.onboarding_models import OnboardingProfile

# Read from environment variables
username = os.getenv('ADMIN_USERNAME', 'Anshi2007')
email = os.getenv('ADMIN_EMAIL', 'Anshi2007@gmail.com')
password = os.getenv('ADMIN_PASSWORD', '@Anshi2007@')

# Check if user already exists
if User.objects.filter(username=username).exists():
    print(f"User '{username}' already exists!")
    user = User.objects.get(username=username)
else:
    # Create superuser
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    print(f"✅ Admin user created successfully!")

# Ensure user has staff and superuser privileges
user.is_staff = True
user.is_superuser = True
user.save()

# Mark admin as onboarded (skip onboarding flow)
profile, created = OnboardingProfile.objects.get_or_create(
    user=user,
    defaults={
        'experience_level': 'advanced',
        'learning_goals': ['System Administration', 'Content Management'],
        'preferred_languages': ['python', 'javascript'],
        'weekly_hours': 10,
        'completed': True
    }
)
if not created:
    profile.completed = True
    profile.save()

print(f"""
╔════════════════════════════════════════════════════════════╗
║           SkillTree AI - Admin Account Created            ║
╠════════════════════════════════════════════════════════════╣
║  Username: {username:<47} ║
║  Email:    {email:<47} ║
║  Password: {'*' * len(password):<47} ║
╠════════════════════════════════════════════════════════════╣
║  Access Admin Panel:                                       ║
║  1. Start backend: python manage.py runserver             ║
║  2. Start frontend: npm run dev                            ║
║  3. Login at: http://localhost:3000/login                  ║
║  4. Navigate to: http://localhost:3000/admin               ║
╚════════════════════════════════════════════════════════════╝
""")
