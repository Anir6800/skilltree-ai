"""
SkillTree AI - Badge Service Simple Tests
==========================================
Core functionality tests for the badge system.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model

from users.models import Badge, UserBadge
from users.badge_service import badge_service

User = get_user_model()


class BadgeServiceSimpleTests(TestCase):
    """Simple badge service functionality tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_badge_service_exists(self):
        """Test badge service is available."""
        self.assertIsNotNone(badge_service)

    def test_check_and_award_badges_returns_list(self):
        """Test check_and_award_badges returns a list."""
        result = badge_service.check_and_award_badges(
            self.user,
            'quest_passed',
            {'event_type': 'quest_passed'}
        )
        self.assertIsInstance(result, list)

    def test_badge_event_type_mismatch(self):
        """Test badge not awarded if event type doesn't match."""
        badge = Badge.objects.create(
            slug='test-badge',
            name='Test Badge',
            description='A test badge',
            icon_emoji='🧪',
            rarity='common',
            unlock_condition={
                'event_type': 'quest_passed',
                'criteria': {'min_quests_passed': 1}
            }
        )
        
        new_badges = badge_service.check_and_award_badges(
            self.user,
            'xp_gained',  # Wrong event type
            {'event_type': 'xp_gained'}
        )
        self.assertEqual(len(new_badges), 0)

    def test_xp_milestone_badge(self):
        """Test XP milestone badge."""
        xp_badge = Badge.objects.create(
            slug='xp-500',
            name='Rising Coder',
            description='Reached 500 XP',
            icon_emoji='⚡',
            rarity='common',
            unlock_condition={
                'event_type': 'xp_gained',
                'criteria': {'min_total_xp': 500}
            }
        )
        
        # Give user 500 XP
        self.user.xp = 500
        self.user.save()
        
        # Award badge
        new_badges = badge_service.check_and_award_badges(
            self.user,
            'xp_gained',
            {'event_type': 'xp_gained', 'total_xp': 500}
        )
        
        self.assertEqual(len(new_badges), 1)
        self.assertEqual(new_badges[0].slug, 'xp-500')

    def test_streak_badge(self):
        """Test streak badge."""
        streak_badge = Badge.objects.create(
            slug='on-a-roll',
            name='On a Roll',
            description='3-day streak',
            icon_emoji='🔥',
            rarity='common',
            unlock_condition={
                'event_type': 'streak_updated',
                'criteria': {'min_streak_days': 3}
            }
        )
        
        # Give user 3-day streak
        self.user.streak_days = 3
        self.user.save()
        
        # Award badge
        new_badges = badge_service.check_and_award_badges(
            self.user,
            'streak_updated',
            {'event_type': 'streak_updated', 'streak_days': 3}
        )
        
        self.assertEqual(len(new_badges), 1)
        self.assertEqual(new_badges[0].slug, 'on-a-roll')

    def test_invalid_user_handling(self):
        """Test handling of invalid user."""
        result = badge_service.check_and_award_badges(
            None,
            'quest_passed',
            {}
        )
        self.assertEqual(result, [])

    def test_invalid_event_type_handling(self):
        """Test handling of invalid event type."""
        result = badge_service.check_and_award_badges(
            self.user,
            None,
            {}
        )
        self.assertEqual(result, [])

    def test_cache_invalidation(self):
        """Test cache invalidation works."""
        # Should not raise exception
        badge_service.invalidate_percentile_cache()
        self.assertTrue(True)

    def test_get_badge_progress(self):
        """Test getting badge progress."""
        # Get progress for user with no badges
        progress = badge_service.get_user_badge_progress(self.user)
        
        self.assertIn('earned_count', progress)
        self.assertIn('total_count', progress)
        self.assertIn('progress_percent', progress)
        self.assertEqual(progress['earned_count'], 0)

    def test_generic_condition_min_total_xp(self):
        """Test generic condition with min_total_xp."""
        badge = Badge.objects.create(
            slug='test-xp',
            name='Test XP',
            description='Test',
            icon_emoji='⚡',
            rarity='common',
            unlock_condition={
                'event_type': 'xp_gained',
                'criteria': {'min_total_xp': 500}
            }
        )
        
        # Not enough XP
        result = badge_service._check_generic_condition(
            self.user,
            badge,
            {}
        )
        self.assertFalse(result)
        
        # Enough XP
        self.user.xp = 500
        self.user.save()
        
        result = badge_service._check_generic_condition(
            self.user,
            badge,
            {}
        )
        self.assertTrue(result)

    def test_generic_condition_min_streak_days(self):
        """Test generic condition with min_streak_days."""
        badge = Badge.objects.create(
            slug='test-streak',
            name='Test Streak',
            description='Test',
            icon_emoji='🔥',
            rarity='common',
            unlock_condition={
                'event_type': 'streak_updated',
                'criteria': {'min_streak_days': 7}
            }
        )
        
        # Not enough streak
        result = badge_service._check_generic_condition(
            self.user,
            badge,
            {}
        )
        self.assertFalse(result)
        
        # Enough streak
        self.user.streak_days = 7
        self.user.save()
        
        result = badge_service._check_generic_condition(
            self.user,
            badge,
            {}
        )
        self.assertTrue(result)


# Run tests with: python manage.py test users.tests.test_badge_service_simple -v 2
