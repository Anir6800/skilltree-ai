"""
SkillTree AI - Badge Service Tests
===================================
Unit and integration tests for the badge system.
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import transaction
from concurrent.futures import ThreadPoolExecutor
import time

from users.models import Badge, UserBadge
from users.badge_service import badge_service
from quests.models import Quest, QuestSubmission
from skills.models import Skill

User = get_user_model()


class BadgeServiceBasicTests(TestCase):
    """Basic badge service functionality tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.badge = Badge.objects.create(
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

    def test_badge_service_initialization(self):
        """Test badge service initializes correctly."""
        self.assertIsNotNone(badge_service)
        self.assertTrue(hasattr(badge_service, 'check_and_award_badges'))

    def test_check_and_award_badges_returns_list(self):
        """Test check_and_award_badges returns a list."""
        result = badge_service.check_and_award_badges(
            self.user,
            'quest_passed',
            {'event_type': 'quest_passed'}
        )
        self.assertIsInstance(result, list)

    def test_badge_award_creates_user_badge(self):
        """Test badge award creates UserBadge record."""
        # Award badge
        new_badges = badge_service.check_and_award_badges(
            self.user,
            'quest_passed',
            {'event_type': 'quest_passed'}
        )
        
        # Should have awarded the badge
        self.assertEqual(len(new_badges), 1)
        self.assertEqual(new_badges[0].slug, 'test-badge')
        
        # Check database
        user_badge = UserBadge.objects.get(user=self.user, badge=self.badge)
        self.assertIsNotNone(user_badge)
        self.assertFalse(user_badge.seen)

    def test_badge_no_duplicate_award(self):
        """Test badge is not awarded twice."""
        # Award badge first time
        new_badges_1 = badge_service.check_and_award_badges(
            self.user,
            'quest_passed',
            {'event_type': 'quest_passed'}
        )
        self.assertEqual(len(new_badges_1), 1)
        
        # Try to award again
        new_badges_2 = badge_service.check_and_award_badges(
            self.user,
            'quest_passed',
            {'event_type': 'quest_passed'}
        )
        self.assertEqual(len(new_badges_2), 0)
        
        # Check only one record in database
        count = UserBadge.objects.filter(
            user=self.user,
            badge=self.badge
        ).count()
        self.assertEqual(count, 1)

    def test_badge_event_type_mismatch(self):
        """Test badge not awarded if event type doesn't match."""
        new_badges = badge_service.check_and_award_badges(
            self.user,
            'xp_gained',  # Wrong event type
            {'event_type': 'xp_gained'}
        )
        self.assertEqual(len(new_badges), 0)

    def test_badge_condition_not_met(self):
        """Test badge not awarded if condition not met."""
        # Create badge requiring 10 quests
        badge = Badge.objects.create(
            slug='quest-10',
            name='Quest Hunter',
            description='Complete 10 quests',
            icon_emoji='🏹',
            rarity='common',
            unlock_condition={
                'event_type': 'quest_passed',
                'criteria': {'min_quests_passed': 10}
            }
        )
        
        # Try to award with only 1 quest
        new_badges = badge_service.check_and_award_badges(
            self.user,
            'quest_passed',
            {'event_type': 'quest_passed'}
        )
        
        # Should not award
        self.assertEqual(len(new_badges), 0)

    def test_get_user_earned_badges(self):
        """Test getting user's earned badges."""
        # Award badge
        badge_service.check_and_award_badges(
            self.user,
            'quest_passed',
            {'event_type': 'quest_passed'}
        )
        
        # Get earned badges
        earned = badge_service.get_user_earned_badges(self.user)
        self.assertEqual(len(earned), 1)
        self.assertEqual(earned[0].slug, 'test-badge')

    def test_get_user_badge_progress(self):
        """Test getting user's badge progress."""
        # Award one badge
        badge_service.check_and_award_badges(
            self.user,
            'quest_passed',
            {'event_type': 'quest_passed'}
        )
        
        # Get progress
        progress = badge_service.get_user_badge_progress(self.user)
        
        self.assertEqual(progress['earned_count'], 1)
        self.assertEqual(progress['total_count'], 1)
        self.assertEqual(progress['progress_percent'], 100)

    def test_is_earned_check(self):
        """Test checking if badge is earned."""
        # Not earned yet
        self.assertFalse(badge_service.badge_service.isEarned(self.badge.id))
        
        # Award badge
        badge_service.check_and_award_badges(
            self.user,
            'quest_passed',
            {'event_type': 'quest_passed'}
        )
        
        # Now earned
        self.assertTrue(badge_service.badge_service.isEarned(self.badge.id))


class BadgeServiceRaceConditionTests(TransactionTestCase):
    """Tests for race condition prevention."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.badge = Badge.objects.create(
            slug='race-test',
            name='Race Test Badge',
            description='For testing race conditions',
            icon_emoji='🏁',
            rarity='common',
            unlock_condition={
                'event_type': 'quest_passed',
                'criteria': {'min_quests_passed': 1}
            }
        )

    def test_concurrent_badge_award_no_duplicates(self):
        """Test concurrent badge awards don't create duplicates."""
        results = []
        
        def award_badge():
            new_badges = badge_service.check_and_award_badges(
                self.user,
                'quest_passed',
                {'event_type': 'quest_passed'}
            )
            results.append(len(new_badges))
        
        # Run 5 concurrent badge awards
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(award_badge) for _ in range(5)]
            for future in futures:
                future.result()
        
        # Only one should have succeeded
        self.assertEqual(sum(results), 1)
        
        # Check database has only one record
        count = UserBadge.objects.filter(
            user=self.user,
            badge=self.badge
        ).count()
        self.assertEqual(count, 1)


class BadgeCheckerMethodsTests(TestCase):
    """Tests for specific badge checker methods."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_check_first_xp(self):
        """Test First Steps badge (1 XP)."""
        badge = Badge.objects.create(
            slug='first-xp',
            name='First Steps',
            description='Earned your first XP',
            icon_emoji='🌱',
            rarity='common',
            unlock_condition={
                'event_type': 'xp_gained',
                'criteria': {'min_total_xp': 1}
            }
        )
        
        # User has no XP
        result = badge_service._check_first_xp(self.user, {})
        self.assertFalse(result)
        
        # Give user XP
        self.user.xp = 1
        self.user.save()
        
        result = badge_service._check_first_xp(self.user, {})
        self.assertTrue(result)

    def test_check_xp_500(self):
        """Test Rising Coder badge (500 XP)."""
        self.user.xp = 500
        self.user.save()
        
        result = badge_service._check_xp_500(self.user, {})
        self.assertTrue(result)

    def test_check_xp_1000(self):
        """Test Code Warrior badge (1000 XP)."""
        self.user.xp = 1000
        self.user.save()
        
        result = badge_service._check_xp_1000(self.user, {})
        self.assertTrue(result)

    def test_check_on_a_roll(self):
        """Test On a Roll badge (3-day streak)."""
        self.user.streak_days = 3
        self.user.save()
        
        result = badge_service._check_on_a_roll(self.user, {})
        self.assertTrue(result)

    def test_check_week_warrior(self):
        """Test Week Warrior badge (7-day streak)."""
        self.user.streak_days = 7
        self.user.save()
        
        result = badge_service._check_week_warrior(self.user, {})
        self.assertTrue(result)

    def test_check_unstoppable(self):
        """Test Unstoppable badge (30-day streak)."""
        self.user.streak_days = 30
        self.user.save()
        
        result = badge_service._check_unstoppable(self.user, {})
        self.assertTrue(result)


class BadgeGenericConditionTests(TestCase):
    """Tests for generic condition checker."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

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


class BadgeErrorHandlingTests(TestCase):
    """Tests for error handling."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_invalid_user(self):
        """Test handling of invalid user."""
        result = badge_service.check_and_award_badges(
            None,
            'quest_passed',
            {}
        )
        self.assertEqual(result, [])

    def test_invalid_event_type(self):
        """Test handling of invalid event type."""
        result = badge_service.check_and_award_badges(
            self.user,
            None,
            {}
        )
        self.assertEqual(result, [])

    def test_invalid_badge_condition(self):
        """Test handling of invalid badge condition."""
        badge = Badge.objects.create(
            slug='invalid',
            name='Invalid Badge',
            description='Test',
            icon_emoji='❌',
            rarity='common',
            unlock_condition=None  # Invalid
        )
        
        result = badge_service._check_unlock_condition(
            self.user,
            badge,
            'quest_passed',
            {}
        )
        self.assertFalse(result)

    def test_missing_event_data(self):
        """Test handling of missing event data."""
        badge = Badge.objects.create(
            slug='test',
            name='Test',
            description='Test',
            icon_emoji='🧪',
            rarity='common',
            unlock_condition={
                'event_type': 'quest_passed',
                'criteria': {}
            }
        )
        
        # Should not crash with missing event_data
        result = badge_service.check_and_award_badges(
            self.user,
            'quest_passed',
            None
        )
        self.assertIsInstance(result, list)


class BadgeCacheTests(TestCase):
    """Tests for cache functionality."""

    def test_percentile_cache_invalidation(self):
        """Test percentile cache invalidation."""
        # This test verifies the cache invalidation method exists
        # and can be called without errors
        badge_service.invalidate_percentile_cache()
        # If we get here, no exception was raised
        self.assertTrue(True)


# Run tests with: python manage.py test users.tests.test_badge_service -v 2
