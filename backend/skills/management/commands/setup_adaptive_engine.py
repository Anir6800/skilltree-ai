"""
Django management command to set up the adaptive engine.
Creates AdaptiveProfile for existing users.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models_adaptive import AdaptiveProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up adaptive engine: create AdaptiveProfile for all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all adaptive profiles to defaults',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Create profile for specific user ID',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.reset_profiles()
        elif options['user_id']:
            self.create_for_user(options['user_id'])
        else:
            self.create_for_all_users()

    def create_for_all_users(self):
        """Create AdaptiveProfile for all users without one."""
        users = User.objects.all()
        created_count = 0

        for user in users:
            profile, created = AdaptiveProfile.objects.get_or_create(user=user)
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created profile for {user.username}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'- Profile already exists for {user.username}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Created {created_count} new profiles')
        )

    def create_for_user(self, user_id):
        """Create AdaptiveProfile for specific user."""
        try:
            user = User.objects.get(id=user_id)
            profile, created = AdaptiveProfile.objects.get_or_create(user=user)

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created profile for {user.username}')
                )
                self.print_profile_info(profile)
            else:
                self.stdout.write(
                    self.style.WARNING(f'Profile already exists for {user.username}')
                )
                self.print_profile_info(profile)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'✗ User with ID {user_id} not found')
            )

    def reset_profiles(self):
        """Reset all adaptive profiles to defaults."""
        profiles = AdaptiveProfile.objects.all()
        count = profiles.count()

        for profile in profiles:
            profile.ability_score = 0.5
            profile.preferred_difficulty = 3
            profile.adjustment_history = []
            profile.save()

        self.stdout.write(
            self.style.SUCCESS(f'✓ Reset {count} profiles to defaults')
        )

    def print_profile_info(self, profile):
        """Print profile information."""
        self.stdout.write(f'  Ability Score: {profile.ability_score:.2f}')
        self.stdout.write(f'  Preferred Difficulty: {profile.preferred_difficulty}')
        self.stdout.write(f'  Adjustments: {len(profile.adjustment_history)}')
