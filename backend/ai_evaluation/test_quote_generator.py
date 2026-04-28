"""
SkillTree AI - Quote Generator Tests
Comprehensive test suite for motivational quote generation.
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from unittest.mock import patch, MagicMock
from datetime import timedelta

from skills.models import Skill
from quests.models import Quest, QuestSubmission
from ai_evaluation.quote_generator import QuoteGenerator, quote_generator

User = get_user_model()


class QuoteGeneratorTestCase(TransactionTestCase):
    """Test suite for QuoteGenerator."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            streak_days=7
        )

        self.skill = Skill.objects.create(
            title='Binary Search',
            description='Learn binary search',
            category='algorithms',
            difficulty=3
        )

        self.quest = Quest.objects.create(
            skill=self.skill,
            type='coding',
            title='Find Target in Sorted Array',
            description='Implement binary search',
            xp_reward=100,
            estimated_minutes=15,
            test_cases=[
                {'input': '[1,3,5,6], 5', 'expected_output': '2'},
                {'input': '[1,3,5,6], 7', 'expected_output': '4'},
            ]
        )

        self.generator = QuoteGenerator()
        cache.clear()

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    def test_generator_initialization(self):
        """Test QuoteGenerator initializes correctly."""
        self.assertIsNotNone(self.generator.client)
        self.assertEqual(self.generator.cache_ttl, 3600)

    def test_build_context_passed(self):
        """Test context building for passed submission."""
        submission = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='def search(nums, target): return 0',
            language='python',
            status='passed',
            execution_result={
                'time_ms': 1500,
                'tests_passed': 2,
                'output': 'Success'
            },
            ai_feedback={'score': 0.85}
        )

        context = self.generator._build_context(submission)

        self.assertEqual(context['quest_title'], 'Find Target in Sorted Array')
        self.assertEqual(context['skill_title'], 'Binary Search')
        self.assertEqual(context['result'], 'passed')
        self.assertEqual(context['tests_passed'], 2)
        self.assertEqual(context['tests_total'], 2)
        self.assertEqual(context['solve_time_seconds'], 1.5)
        self.assertEqual(context['ai_score'], 0.85)
        self.assertEqual(context['user_streak'], 7)

    def test_build_context_failed(self):
        """Test context building for failed submission."""
        submission = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='def search(nums, target): return -1',
            language='python',
            status='failed',
            execution_result={
                'time_ms': 3000,
                'tests_passed': 1,
                'output': 'Failed'
            }
        )

        context = self.generator._build_context(submission)

        self.assertEqual(context['result'], 'failed')
        self.assertEqual(context['tests_passed'], 1)
        self.assertEqual(context['solve_time_seconds'], 3.0)

    def test_build_context_flagged(self):
        """Test context building for flagged submission."""
        submission = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='def search(nums, target): return 0',
            language='python',
            status='flagged',
            execution_result={'time_ms': 1000}
        )

        context = self.generator._build_context(submission)

        self.assertEqual(context['result'], 'flagged')

    def test_determine_tone_celebratory(self):
        """Test tone determination for first-attempt pass."""
        submission = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='correct',
            language='python',
            status='passed',
            execution_result={'time_ms': 2000}
        )

        context = self.generator._build_context(submission)
        tone = self.generator._determine_tone(submission, context)

        self.assertEqual(tone, 'celebratory')

    def test_determine_tone_speed(self):
        """Test tone determination for fast solve."""
        # Create first attempt (failed)
        QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='wrong',
            language='python',
            status='failed',
            execution_result={'time_ms': 5000}
        )

        # Create second attempt (passed, fast)
        submission = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='correct',
            language='python',
            status='passed',
            execution_result={'time_ms': 2000}
        )

        context = self.generator._build_context(submission)
        tone = self.generator._determine_tone(submission, context)

        self.assertEqual(tone, 'speed')

    def test_determine_tone_persistent(self):
        """Test tone determination for multiple attempts pass."""
        # Create 2 failed attempts
        for i in range(2):
            QuestSubmission.objects.create(
                user=self.user,
                quest=self.quest,
                code=f'wrong_{i}',
                language='python',
                status='failed',
                execution_result={'time_ms': 3000}
            )

        # Create passing attempt (3rd attempt)
        submission = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='correct',
            language='python',
            status='passed',
            execution_result={'time_ms': 2000}
        )

        context = self.generator._build_context(submission)
        tone = self.generator._determine_tone(submission, context)

        self.assertEqual(tone, 'persistent')

    def test_determine_tone_encouraging(self):
        """Test tone determination for early failure."""
        submission = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='wrong',
            language='python',
            status='failed',
            execution_result={'time_ms': 2000}
        )

        context = self.generator._build_context(submission)
        tone = self.generator._determine_tone(submission, context)

        self.assertEqual(tone, 'encouraging')

    def test_determine_tone_committed(self):
        """Test tone determination for many failures."""
        # Create 3 failed attempts
        for i in range(3):
            QuestSubmission.objects.create(
                user=self.user,
                quest=self.quest,
                code=f'wrong_{i}',
                language='python',
                status='failed',
                execution_result={'time_ms': 2000}
            )

        # Create 4th failed attempt
        submission = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='wrong_4',
            language='python',
            status='failed',
            execution_result={'time_ms': 2000}
        )

        context = self.generator._build_context(submission)
        tone = self.generator._determine_tone(submission, context)

        self.assertEqual(tone, 'committed')

    def test_determine_tone_diplomatic(self):
        """Test tone determination for flagged submission."""
        submission = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='correct',
            language='python',
            status='flagged',
            execution_result={'time_ms': 1000}
        )

        context = self.generator._build_context(submission)
        tone = self.generator._determine_tone(submission, context)

        self.assertEqual(tone, 'diplomatic')

    def test_determine_tone_streak_milestone(self):
        """Test tone determination for streak milestone."""
        self.user.streak_days = 14  # Divisible by 7
        self.user.save()

        submission = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='correct',
            language='python',
            status='passed',
            execution_result={'time_ms': 2000}
        )

        context = self.generator._build_context(submission)
        tone = self.generator._determine_tone(submission, context)

        self.assertEqual(tone, 'streak')

    def test_get_attempt_number(self):
        """Test attempt number calculation."""
        # Create 2 submissions
        submission1 = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='attempt1',
            language='python',
            status='failed',
            execution_result={}
        )

        submission2 = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='attempt2',
            language='python',
            status='passed',
            execution_result={}
        )

        self.assertEqual(self.generator._get_attempt_number(submission1), 1)
        self.assertEqual(self.generator._get_attempt_number(submission2), 2)

    def test_get_time_of_day(self):
        """Test time of day categorization."""
        morning = timezone.now().replace(hour=8)
        afternoon = timezone.now().replace(hour=14)
        evening = timezone.now().replace(hour=19)
        night = timezone.now().replace(hour=23)

        self.assertEqual(self.generator._get_time_of_day(morning), 'morning')
        self.assertEqual(self.generator._get_time_of_day(afternoon), 'afternoon')
        self.assertEqual(self.generator._get_time_of_day(evening), 'evening')
        self.assertEqual(self.generator._get_time_of_day(night), 'night')

    def test_cache_key_generation(self):
        """Test cache key generation."""
        key = self.generator._get_cache_key(123)
        self.assertEqual(key, 'quote:123')

    def test_fallback_quote_passed_first(self):
        """Test fallback quote for first-attempt pass."""
        submission = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='correct',
            language='python',
            status='passed',
            execution_result={}
        )

        quote = self.generator._get_fallback_quote(submission)
        self.assertIn('mastered', quote.lower())
        self.assertIn('first try', quote.lower())

    def test_fallback_quote_passed_multiple(self):
        """Test fallback quote for multiple-attempt pass."""
        QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='wrong',
            language='python',
            status='failed',
            execution_result={}
        )

        submission = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='correct',
            language='python',
            status='passed',
            execution_result={}
        )

        quote = self.generator._get_fallback_quote(submission)
        self.assertIn('conquered', quote.lower())

    def test_fallback_quote_failed_early(self):
        """Test fallback quote for early failure."""
        submission = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='wrong',
            language='python',
            status='failed',
            execution_result={}
        )

        quote = self.generator._get_fallback_quote(submission)
        self.assertIn('close', quote.lower())

    def test_fallback_quote_failed_late(self):
        """Test fallback quote for many failures."""
        for i in range(4):
            QuestSubmission.objects.create(
                user=self.user,
                quest=self.quest,
                code=f'wrong_{i}',
                language='python',
                status='failed',
                execution_result={}
            )

        submission = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='wrong_5',
            language='python',
            status='failed',
            execution_result={}
        )

        quote = self.generator._get_fallback_quote(submission)
        self.assertIn('hint', quote.lower())

    def test_fallback_quote_flagged(self):
        """Test fallback quote for flagged submission."""
        submission = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='correct',
            language='python',
            status='flagged',
            execution_result={}
        )

        quote = self.generator._get_fallback_quote(submission)
        self.assertIn('approach', quote.lower())

    @patch('ai_evaluation.quote_generator.lm_client')
    def test_generate_result_quote_success(self, mock_client):
        """Test successful quote generation."""
        mock_response = {
            'choices': [
                {'message': {'content': 'Great job on Binary Search! Your pattern recognition is sharp.'}}
            ]
        }
        mock_client.chat_completion.return_value = mock_response
        mock_client.extract_content.return_value = 'Great job on Binary Search! Your pattern recognition is sharp.'

        submission = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='correct',
            language='python',
            status='passed',
            execution_result={'time_ms': 1000}
        )

        quote = self.generator.generate_result_quote(submission)

        self.assertIsNotNone(quote)
        self.assertIn('Binary Search', quote)

    @patch('ai_evaluation.quote_generator.lm_client')
    def test_generate_result_quote_caching(self, mock_client):
        """Test quote caching."""
        mock_response = {
            'choices': [
                {'message': {'content': 'Great job!'}}
            ]
        }
        mock_client.chat_completion.return_value = mock_response
        mock_client.extract_content.return_value = 'Great job!'

        submission = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='correct',
            language='python',
            status='passed',
            execution_result={'time_ms': 1000}
        )

        # First call
        quote1 = self.generator.generate_result_quote(submission)

        # Second call should use cache
        quote2 = self.generator.generate_result_quote(submission)

        self.assertEqual(quote1, quote2)
        # Should only be called once due to caching
        self.assertEqual(mock_client.chat_completion.call_count, 1)

    @patch('ai_evaluation.quote_generator.lm_client')
    def test_generate_result_quote_fallback_on_error(self, mock_client):
        """Test fallback quote on LM Studio error."""
        from core.lm_client import ExecutionServiceUnavailable

        mock_client.chat_completion.side_effect = ExecutionServiceUnavailable('Service down')

        submission = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='correct',
            language='python',
            status='passed',
            execution_result={'time_ms': 1000}
        )

        quote = self.generator.generate_result_quote(submission)

        self.assertIsNotNone(quote)
        self.assertIn('mastered', quote.lower())

    def test_is_available(self):
        """Test service availability check."""
        with patch.object(self.generator.client, 'is_available', return_value=True):
            self.assertTrue(self.generator.is_available())

        with patch.object(self.generator.client, 'is_available', return_value=False):
            self.assertFalse(self.generator.is_available())

    def test_singleton_instance(self):
        """Test quote_generator singleton."""
        self.assertIsNotNone(quote_generator)
        self.assertIsInstance(quote_generator, QuoteGenerator)
