"""
SkillTree AI - Badge System Tests
Comprehensive test suite for achievement badges.
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from users.models import Badge, UserBadge
from users.badge_checker import badge_checker
from quests.models import Quest, QuestSubmission
from skills.models import Skill

User = get_user_model()


class BadgeModelTestCase(TestCase):
    """Test suite for Badge model."""

    def setUp(self):
        """Set up test fixtures."""
        self.badge = Badge.objects.create(
            slug='test_badge',
            name='Test Badge',
            description='A test badge',
            icon_emoji='🧪',
            rarity='common',
            unlock_condition={'event_type': 'test_event'}
        )

    def test_badge_creation(self):
        """Test badge creation."""
        self.assertEqual(self.badge.name, 'Test Badge')
        self.assertEqual(self.badge.rarity, 'common')
        self.assertEqual(self.badge.icon_emoji, '🧪')

    def test_badge_slug_unique(self):
        """Test badge slug is unique."""
        with self.assertRaises(Exception):
            Badge.objects.create(
                slug='test_badge',
                name='Duplicate',
                description='Duplicate badge',
                icon_emoji='🔄',
                rarity='common'
            )

    def test_badge_rarity_choices(self):
        """Test badge rarity choices."""
        rarities = ['common', 'rare', 'epic', 'legendary']
        for rarity in rarities:
            badge = Badge.objects.create(
                slug=f'badge_{rarity}',
                name=f'{rarity.title()} Badge',
                description='Test',
                icon_emoji='✨',
                rarity=rarity
            )
            self.assertEqual(badge.rarity, rarity)

    def test_badge_str(self):
        """Test badge string representation."""
        self.assertIn('Test Badge', str(self.badge))
        self.assertIn('🧪', str(self.badge))


class UserBadgeModelTestCase(TestCase):
    """Test suite for UserBadge model."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.badge = Badge.objects.create(
            slug='test_badge',
            name='Test Badge',
            description='A test badge',
            icon_emoji='🧪',
            rarity='common'
        )

    def test_user_badge_creation(self):
        """Test user badge creation."""
        user_badge = UserBadge.objects.create(
            user=self.user,
            badge=self.badge
        )

        self.assertEqual(user_badge.user.id, self.user.id)
        self.assertEqual(user_badge.badge.id, self.badge.id)
        self.assertFalse(user_badge.seen)

    def test_user_badge_unique_constraint(self):
        """Test unique constraint on user-badge."""
        UserBadge.objects.create(user=self.user, badge=self.badge)

        with self.assertRaises(Exception):
            UserBadge.objects.create(user=self.user, badge=self.badge)

    def test_user_badge_seen_flag(self):
        """Test seen flag on user badge."""
        user_badge = UserBadge.objects.create(
            user=self.user,
            badge=self.badge,
            seen=False
        )

        self.assertFalse(user_badge.seen)

        user_badge.seen = True
        user_badge.save()

        user_badge.refresh_from_db()
        self.assertTrue(user_badge.seen)

    def test_user_badge_str(self):
        """Test user badge string representation."""
        user_badge = UserBadge.objects.create(
            user=self.user,
            badge=self.badge
        )

        self.assertIn(self.user.username, str(user_badge))
        self.assertIn(self.badge.name, str(user_badge))


class BadgeCheckerTestCase(TransactionTestCase):
    """Test suite for BadgeChecker service."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.skill = Skill.objects.create(
            title='Test Skill',
            description='Test skill',
            category='test',
            difficulty=1
        )

        self.quest = Quest.objects.create(
            skill=self.skill,
            type='coding',
            title='Test Quest',
            description='Test quest',
            xp_reward=100,
            estimated_minutes=15
        )

        # Create badges
        self.first_blood_badge = Badge.objects.create(
            slug='first_blood',
            name='First Blood',
            description='Pass your first quest',
            icon_emoji='🩸',
            rarity='common',
            unlock_condition={'event_type': 'quest_passed'}
        )

        self.speed_demon_badge = Badge.objects.create(
            slug='speed_demon',
            name='Speed Demon',
            description='Solve a quest in the top 5% fastest time',
            icon_emoji='⚡',
            rarity='rare',
            unlock_condition={'event_type': 'quest_passed'}
        )

    def test_check_first_blood(self):
        """Test first blood badge."""
        # Create first quest submission
        submission = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='correct',
            language='python',
            status='passed',
            execution_result={'time_ms': 5000}
        )

        # Check badges
        new_badges = badge_checker.check_badges(
            self.user,
            'quest_passed',
            {'event_type': 'quest_passed', 'solve_time_ms': 5000}
        )

        # Should earn first blood
        self.assertIn(self.first_blood_badge, new_badges)

        # Verify UserBadge created
        user_badge = UserBadge.objects.filter(
            user=self.user,
            badge=self.first_blood_badge
        ).first()
        self.assertIsNotNone(user_badge)

    def test_check_first_blood_not_first(self):
        """Test first blood not awarded if not first quest."""
        # Create first submission
        QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='correct',
            language='python',
            status='passed',
            execution_result={'time_ms': 5000}
        )

        # Create second submission
        submission2 = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='correct',
            language='python',
            status='passed',
            execution_result={'time_ms': 5000}
        )

        # Check badges on second submission
        new_badges = badge_checker.check_badges(
            self.user,
            'quest_passed',
            {'event_type': 'quest_passed', 'solve_time_ms': 5000}
        )

        # Should not earn first blood again
        self.assertNotIn(self.first_blood_badge, new_badges)

    def test_check_badges_no_duplicates(self):
        """Test badges are not awarded twice."""
        # Create first submission
        QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='correct',
            language='python',
            status='passed',
            execution_result={'time_ms': 5000}
        )

        # Check badges first time
        new_badges1 = badge_checker.check_badges(
            self.user,
            'quest_passed',
            {'event_type': 'quest_passed', 'solve_time_ms': 5000}
        )

        # Check badges second time
        new_badges2 = badge_checker.check_badges(
            self.user,
            'quest_passed',
            {'event_type': 'quest_passed', 'solve_time_ms': 5000}
        )

        # Second check should not award any badges
        self.assertEqual(len(new_badges2), 0)

    def test_check_badges_invalid_event(self):
        """Test badges not awarded for invalid events."""
        new_badges = badge_checker.check_badges(
            self.user,
            'invalid_event',
            {'event_type': 'invalid_event'}
        )

        self.assertEqual(len(new_badges), 0)

    def test_badge_checker_singleton(self):
        """Test badge_checker is singleton."""
        from users.badge_checker import badge_checker as bc1
        from users.badge_checker import badge_checker as bc2

        self.assertIs(bc1, bc2)

    def test_get_solve_time_percentile(self):
        """Test solve time percentile calculation."""
        # Create submissions with various times
        for i in range(10):
            QuestSubmission.objects.create(
                user=self.user,
                quest=self.quest,
                code='code',
                language='python',
                status='passed',
                execution_result={'time_ms': (i + 1) * 1000}
            )

        percentile_95 = badge_checker._get_solve_time_percentile(95)
        self.assertGreater(percentile_95, 0)

    def test_check_badges_error_handling(self):
        """Test error handling in badge checking."""
        # Should not raise exception even with invalid data
        new_badges = badge_checker.check_badges(
            self.user,
            'quest_passed',
            {}
        )

        # Should return empty list
        self.assertEqual(len(new_badges), 0)


class BadgeIntegrationTestCase(TransactionTestCase):
    """Integration tests for badge system."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.skill = Skill.objects.create(
            title='Test Skill',
            description='Test skill',
            category='test',
            difficulty=1
        )

        self.quest = Quest.objects.create(
            skill=self.skill,
            type='coding',
            title='Test Quest',
            description='Test quest',
            xp_reward=100,
            estimated_minutes=15
        )

    def test_badge_workflow(self):
        """Test complete badge workflow."""
        # Create badge
        badge = Badge.objects.create(
            slug='test_badge',
            name='Test Badge',
            description='Test badge',
            icon_emoji='🧪',
            rarity='common',
            unlock_condition={'event_type': 'quest_passed'}
        )

        # User earns badge
        QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='correct',
            language='python',
            status='passed',
            execution_result={'time_ms': 5000}
        )

        # Check badges
        new_badges = badge_checker.check_badges(
            self.user,
            'quest_passed',
            {'event_type': 'quest_passed', 'solve_time_ms': 5000}
        )

        # Verify badge earned
        user_badge = UserBadge.objects.filter(
            user=self.user,
            badge=badge
        ).first()

        self.assertIsNotNone(user_badge)
        self.assertFalse(user_badge.seen)

        # Mark as seen
        user_badge.seen = True
        user_badge.save()

        user_badge.refresh_from_db()
        self.assertTrue(user_badge.seen)

    def test_multiple_badges_same_event(self):
        """Test multiple badges can be earned from same event."""
        # Create two badges with same event
        badge1 = Badge.objects.create(
            slug='badge1',
            name='Badge 1',
            description='Badge 1',
            icon_emoji='1️⃣',
            rarity='common',
            unlock_condition={'event_type': 'quest_passed'}
        )

        badge2 = Badge.objects.create(
            slug='badge2',
            name='Badge 2',
            description='Badge 2',
            icon_emoji='2️⃣',
            rarity='common',
            unlock_condition={'event_type': 'quest_passed'}
        )

        # Create submission
        QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='correct',
            language='python',
            status='passed',
            execution_result={'time_ms': 5000}
        )

        # Check badges
        new_badges = badge_checker.check_badges(
            self.user,
            'quest_passed',
            {'event_type': 'quest_passed', 'solve_time_ms': 5000}
        )

        # Both badges should be earned
        self.assertEqual(len(new_badges), 2)
        self.assertIn(badge1, new_badges)
        self.assertIn(badge2, new_badges)
