"""
SkillTree AI - Adaptive Engine Tests
Comprehensive test suite for adaptive learning functionality.
"""

from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from skills.models import Skill, SkillProgress
from skills.adaptive_engine import AdaptiveTreeEngine
from users.models_adaptive import AdaptiveProfile, UserSkillFlag
from quests.models import Quest, QuestSubmission

User = get_user_model()


class AdaptiveEngineTestCase(TransactionTestCase):
    """Test suite for AdaptiveTreeEngine."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.skill1 = Skill.objects.create(
            title='Python Basics',
            description='Learn Python fundamentals',
            category='programming',
            difficulty=1
        )

        self.skill2 = Skill.objects.create(
            title='Advanced Python',
            description='Advanced Python concepts',
            category='programming',
            difficulty=4
        )

        self.skill3 = Skill.objects.create(
            title='Intermediate Python',
            description='Intermediate Python concepts',
            category='programming',
            difficulty=3
        )

        self.quest1 = Quest.objects.create(
            skill=self.skill1,
            type='coding',
            title='Hello World',
            description='Write a hello world program',
            xp_reward=50,
            estimated_minutes=5
        )

        self.quest2 = Quest.objects.create(
            skill=self.skill1,
            type='coding',
            title='Variables',
            description='Work with variables',
            xp_reward=75,
            estimated_minutes=10
        )

        self.engine = AdaptiveTreeEngine(self.user.id)

    def test_engine_initialization(self):
        """Test engine initializes correctly."""
        self.assertEqual(self.engine.user.id, self.user.id)

    def test_collect_performance_signals_empty(self):
        """Test performance signal collection with no submissions."""
        signals = self.engine.collect_performance_signals()

        self.assertIn('solve_speed_percentile', signals)
        self.assertIn('consecutive_fails', signals)
        self.assertIn('first_attempt_pass_rate', signals)
        self.assertIn('hint_usage_rate', signals)

        self.assertEqual(signals['consecutive_fails'], 0)
        self.assertEqual(signals['first_attempt_pass_rate'], 0.0)
        self.assertEqual(signals['hint_usage_rate'], 0.0)

    def test_collect_performance_signals_with_submissions(self):
        """Test performance signal collection with submissions."""
        # Create passed submission
        QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest1,
            code='print("hello")',
            language='python',
            status='passed',
            execution_result={'time_ms': 1000, 'tests_passed': 1}
        )

        # Create failed submission
        QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest2,
            code='x = ',
            language='python',
            status='failed',
            execution_result={'time_ms': 500, 'tests_passed': 0}
        )

        signals = self.engine.collect_performance_signals()

        self.assertEqual(signals['consecutive_fails'], 1)
        self.assertGreater(signals['first_attempt_pass_rate'], 0.0)

    def test_update_ability_score(self):
        """Test Bayesian ability score update."""
        profile = AdaptiveProfile.objects.create(user=self.user, ability_score=0.5)

        # Update with positive outcome
        new_score = self.engine.update_ability_score(1.0)
        self.assertGreater(new_score, 0.5)

        # Update with negative outcome
        new_score = self.engine.update_ability_score(0.0)
        self.assertLess(new_score, 0.65)

    def test_update_preferred_difficulty(self):
        """Test preferred difficulty auto-update."""
        profile = AdaptiveProfile.objects.create(user=self.user, ability_score=0.8)

        new_difficulty = self.engine.update_preferred_difficulty()
        self.assertEqual(new_difficulty, 4)

        profile.ability_score = 0.2
        profile.save()
        new_difficulty = self.engine.update_preferred_difficulty()
        self.assertEqual(new_difficulty, 1)

    def test_adapt_tree_for_user(self):
        """Test main tree adaptation logic."""
        profile = AdaptiveProfile.objects.create(user=self.user, ability_score=0.5)

        SkillProgress.objects.create(
            user=self.user,
            skill=self.skill1,
            status='available'
        )

        SkillProgress.objects.create(
            user=self.user,
            skill=self.skill2,
            status='available'
        )

        changes = self.engine.adapt_tree_for_user()

        self.assertIn('reordered_skills', changes)
        self.assertIn('flagged_too_easy', changes)
        self.assertIn('flagged_struggling', changes)
        self.assertIn('bridge_quests_generated', changes)

    def test_flag_too_easy_skills(self):
        """Test flagging of too easy skills."""
        profile = AdaptiveProfile.objects.create(user=self.user, ability_score=0.9)

        SkillProgress.objects.create(
            user=self.user,
            skill=self.skill1,
            status='available'
        )

        self.engine.adapt_tree_for_user()

        flag = UserSkillFlag.objects.filter(
            user=self.user,
            skill=self.skill1,
            flag='too_easy'
        ).first()

        self.assertIsNotNone(flag)

    def test_flag_struggling_skills(self):
        """Test flagging of struggling skills."""
        profile = AdaptiveProfile.objects.create(user=self.user)

        SkillProgress.objects.create(
            user=self.user,
            skill=self.skill1,
            status='available'
        )

        # Create multiple failed submissions
        for i in range(3):
            QuestSubmission.objects.create(
                user=self.user,
                quest=self.quest1,
                code=f'fail_{i}',
                language='python',
                status='failed',
                execution_result={'time_ms': 500}
            )

        self.engine.adapt_tree_for_user()

        flag = UserSkillFlag.objects.filter(
            user=self.user,
            skill=self.skill1,
            flag='struggling'
        ).first()

        self.assertIsNotNone(flag)

    def test_reorder_skills_by_difficulty(self):
        """Test skill reordering by difficulty."""
        user_skills = [
            SkillProgress(user=self.user, skill=self.skill1, status='available'),
            SkillProgress(user=self.user, skill=self.skill2, status='available'),
            SkillProgress(user=self.user, skill=self.skill3, status='available'),
        ]

        reordered = self.engine._reorder_skills_by_difficulty(user_skills, preferred_difficulty=3)

        # Skill3 (difficulty 3) should be first (ideal range)
        self.assertEqual(reordered[0].skill.id, self.skill3.id)

    def test_consecutive_fails_counting(self):
        """Test consecutive fail counting."""
        # Create submissions: pass, fail, fail, fail
        QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest1,
            code='pass',
            language='python',
            status='passed',
            execution_result={}
        )

        for i in range(3):
            QuestSubmission.objects.create(
                user=self.user,
                quest=self.quest2,
                code=f'fail_{i}',
                language='python',
                status='failed',
                execution_result={}
            )

        submissions = QuestSubmission.objects.filter(user=self.user).order_by('created_at')
        consecutive = self.engine._count_consecutive_fails(submissions)

        self.assertEqual(consecutive, 3)

    def test_first_attempt_detection(self):
        """Test first attempt detection."""
        submission1 = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest1,
            code='first',
            language='python',
            status='passed',
            execution_result={}
        )

        submission2 = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest1,
            code='second',
            language='python',
            status='passed',
            execution_result={}
        )

        self.assertTrue(self.engine._is_first_attempt(submission1))
        self.assertFalse(self.engine._is_first_attempt(submission2))

    def test_ability_score_bounds(self):
        """Test ability score stays within bounds."""
        profile = AdaptiveProfile.objects.create(user=self.user, ability_score=0.95)

        # Try to push above max
        new_score = self.engine.update_ability_score(1.0)
        self.assertLessEqual(new_score, 1.0)

        profile.ability_score = 0.05
        profile.save()

        # Try to push below min
        new_score = self.engine.update_ability_score(0.0)
        self.assertGreaterEqual(new_score, 0.0)

    def test_adjustment_history_logging(self):
        """Test adjustment history is logged."""
        profile = AdaptiveProfile.objects.create(user=self.user)

        self.engine.adapt_tree_for_user()

        profile.refresh_from_db()
        self.assertGreater(len(profile.adjustment_history), 0)

        last_adjustment = profile.adjustment_history[-1]
        self.assertIn('timestamp', last_adjustment)
        self.assertIn('reason', last_adjustment)
        self.assertIn('signals', last_adjustment)
        self.assertIn('changes', last_adjustment)


class AdaptiveProfileModelTestCase(TestCase):
    """Test suite for AdaptiveProfile model."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_adaptive_profile_creation(self):
        """Test AdaptiveProfile creation."""
        profile = AdaptiveProfile.objects.create(
            user=self.user,
            ability_score=0.7,
            preferred_difficulty=4
        )

        self.assertEqual(profile.user.id, self.user.id)
        self.assertEqual(profile.ability_score, 0.7)
        self.assertEqual(profile.preferred_difficulty, 4)

    def test_adaptive_profile_defaults(self):
        """Test AdaptiveProfile default values."""
        profile = AdaptiveProfile.objects.create(user=self.user)

        self.assertEqual(profile.ability_score, 0.5)
        self.assertEqual(profile.preferred_difficulty, 3)
        self.assertEqual(profile.adjustment_history, [])

    def test_adjustment_history_json(self):
        """Test adjustment history JSON field."""
        profile = AdaptiveProfile.objects.create(user=self.user)

        profile.adjustment_history.append({
            'timestamp': timezone.now().isoformat(),
            'reason': 'Test adjustment',
            'signals': {'test': 'data'},
        })
        profile.save()

        profile.refresh_from_db()
        self.assertEqual(len(profile.adjustment_history), 1)
        self.assertEqual(profile.adjustment_history[0]['reason'], 'Test adjustment')


class UserSkillFlagModelTestCase(TestCase):
    """Test suite for UserSkillFlag model."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.skill = Skill.objects.create(
            title='Test Skill',
            description='Test description',
            category='test',
            difficulty=2
        )

    def test_user_skill_flag_creation(self):
        """Test UserSkillFlag creation."""
        flag = UserSkillFlag.objects.create(
            user=self.user,
            skill=self.skill,
            flag='too_easy',
            reason='Test reason'
        )

        self.assertEqual(flag.user.id, self.user.id)
        self.assertEqual(flag.skill.id, self.skill.id)
        self.assertEqual(flag.flag, 'too_easy')

    def test_user_skill_flag_unique_constraint(self):
        """Test unique constraint on user-skill-flag."""
        UserSkillFlag.objects.create(
            user=self.user,
            skill=self.skill,
            flag='too_easy'
        )

        with self.assertRaises(Exception):
            UserSkillFlag.objects.create(
                user=self.user,
                skill=self.skill,
                flag='too_easy'
            )

    def test_user_skill_flag_different_flags_allowed(self):
        """Test different flags for same user-skill are allowed."""
        UserSkillFlag.objects.create(
            user=self.user,
            skill=self.skill,
            flag='too_easy'
        )

        flag2 = UserSkillFlag.objects.create(
            user=self.user,
            skill=self.skill,
            flag='struggling'
        )

        self.assertEqual(flag2.flag, 'struggling')
