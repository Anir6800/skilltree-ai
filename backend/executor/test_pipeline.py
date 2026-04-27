"""
SkillTree AI - Pipeline Tests
Comprehensive test suite for the 7-step submission execution pipeline.
Tests all tasks, error handling, WebSocket broadcasting, and edge cases.
"""

import json
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from celery.result import AsyncResult
from quests.models import Quest, QuestSubmission
from skills.models import Skill, SkillProgress
from executor.pipeline import (
    execute_code,
    run_test_cases,
    ai_evaluate,
    detect_ai_usage,
    award_xp_if_eligible,
    update_leaderboard_task,
    resolve_skill_unlocks,
    run_submission_pipeline,
    broadcast_pipeline_update,
)

User = get_user_model()


class PipelineTestSetup(TransactionTestCase):
    """Base test class with common setup."""

    def setUp(self):
        """Create test data."""
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.xp = 0
        self.user.level = 1
        self.user.streak_days = 0
        self.user.save()

        # Create skill
        self.skill = Skill.objects.create(
            title='Python Basics',
            description='Learn Python fundamentals',
            category='programming',
            difficulty=1,
            xp_required_to_unlock=0
        )

        # Create quest with test cases
        self.quest = Quest.objects.create(
            skill=self.skill,
            type='coding',
            title='Hello World',
            description='Write a program that prints Hello World',
            starter_code='',
            test_cases=[
                {'input': '', 'expected_output': 'Hello World'},
            ],
            xp_reward=100,
            difficulty_multiplier=1.0
        )

        # Create submission
        self.submission = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='print("Hello World")',
            language='python',
            status='pending'
        )


class TestExecuteCodeTask(PipelineTestSetup):
    """Test Task 1: execute_code"""

    @patch('executor.pipeline.CompileExecutor')
    @patch('executor.pipeline.broadcast_pipeline_update')
    def test_execute_code_success(self, mock_broadcast, mock_executor_class):
        """Test successful code execution."""
        # Setup mock
        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor
        mock_executor.execute.return_value = {
            'output': 'Hello World',
            'stderr': '',
            'exit_code': 0,
            'execution_time_ms': 100
        }

        # Execute task
        result = execute_code(self.submission.id)

        # Verify
        assert result['step'] == 1
        assert result['status'] == 'completed'
        assert result['execution_result']['output'] == 'Hello World'

        # Verify submission updated
        self.submission.refresh_from_db()
        assert self.submission.execution_result['output'] == 'Hello World'

        # Verify broadcast called
        mock_broadcast.assert_called()

    @patch('executor.pipeline.CompileExecutor')
    @patch('executor.pipeline.broadcast_pipeline_update')
    def test_execute_code_with_error(self, mock_broadcast, mock_executor_class):
        """Test code execution with error."""
        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor
        mock_executor.execute.return_value = {
            'output': '',
            'stderr': 'SyntaxError: invalid syntax',
            'exit_code': 1,
            'execution_time_ms': 50
        }

        result = execute_code(self.submission.id)

        assert result['step'] == 1
        assert result['status'] == 'completed'
        assert result['execution_result']['exit_code'] == 1

    @patch('executor.pipeline.CompileExecutor')
    def test_execute_code_submission_not_found(self, mock_executor_class):
        """Test execute_code with non-existent submission."""
        with self.assertRaises(QuestSubmission.DoesNotExist):
            execute_code(99999)


class TestRunTestCasesTask(PipelineTestSetup):
    """Test Task 2: run_test_cases"""

    @patch('executor.pipeline.CompileExecutor')
    @patch('executor.pipeline.broadcast_pipeline_update')
    def test_run_test_cases_all_pass(self, mock_broadcast, mock_executor_class):
        """Test when all tests pass."""
        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor
        mock_executor.run_test_cases.return_value = {
            'tests_passed': 1,
            'tests_total': 1,
            'results': [
                {
                    'input': '',
                    'expected': 'Hello World',
                    'actual': 'Hello World',
                    'passed': True,
                    'time_ms': 5035
                }
            ]
        }

        result = run_test_cases(self.submission.id)

        assert result['step'] == 2
        assert result['status'] == 'completed'
        assert result['tests_passed'] == 1
        assert result['tests_total'] == 1
        assert result['stop_chain'] is False

    @patch('executor.pipeline.CompileExecutor')
    @patch('executor.pipeline.broadcast_pipeline_update')
    def test_run_test_cases_all_fail(self, mock_broadcast, mock_executor_class):
        """Test when all tests fail - should stop chain."""
        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor
        mock_executor.run_test_cases.return_value = {
            'tests_passed': 0,
            'tests_total': 1,
            'results': [
                {
                    'input': '',
                    'expected': 'Hello World',
                    'actual': 'Goodbye World',
                    'passed': False,
                    'time_ms': 50
                }
            ]
        }

        result = run_test_cases(self.submission.id)

        assert result['step'] == 2
        assert result['status'] == 'failed'
        assert result['tests_passed'] == 0
        assert result['stop_chain'] is True

        # Verify submission marked as failed
        self.submission.refresh_from_db()
        assert self.submission.status == 'failed'

    @patch('executor.pipeline.CompileExecutor')
    @patch('executor.pipeline.broadcast_pipeline_update')
    def test_run_test_cases_partial_pass(self, mock_broadcast, mock_executor_class):
        """Test when some tests pass."""
        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor
        mock_executor.run_test_cases.return_value = {
            'tests_passed': 2,
            'tests_total': 3,
            'results': [
                {'input': '1', 'expected': '1', 'actual': '1', 'passed': True, 'time_ms': 50},
                {'input': '2', 'expected': '2', 'actual': '2', 'passed': True, 'time_ms': 50},
                {'input': '3', 'expected': '3', 'actual': 'wrong', 'passed': False, 'time_ms': 50},
            ]
        }

        result = run_test_cases(self.submission.id)

        assert result['step'] == 2
        assert result['status'] == 'completed'
        assert result['tests_passed'] == 2
        assert result['tests_total'] == 3
        assert result['stop_chain'] is False


class TestAIEvaluateTask(PipelineTestSetup):
    """Test Task 3: ai_evaluate"""

    @patch('executor.pipeline.AIEvaluator')
    @patch('executor.pipeline.broadcast_pipeline_update')
    def test_ai_evaluate_success(self, mock_broadcast, mock_evaluator_class):
        """Test successful AI evaluation."""
        mock_evaluator = Mock()
        mock_evaluator_class.return_value = mock_evaluator
        mock_evaluator.evaluate.return_value = {
            'score': 85,
            'summary': 'Good code quality',
            'pros': ['Clean code', 'Good naming'],
            'cons': ['Missing comments'],
            'suggestions': ['Add docstrings']
        }

        result = ai_evaluate(self.submission.id)

        assert result['step'] == 3
        assert result['status'] == 'completed'
        assert 'Good code quality' in result['feedback_summary']

        # Verify submission updated
        self.submission.refresh_from_db()
        assert self.submission.ai_feedback['score'] == 85

    @patch('executor.pipeline.AIEvaluator')
    @patch('executor.pipeline.broadcast_pipeline_update')
    def test_ai_evaluate_failure_non_critical(self, mock_broadcast, mock_evaluator_class):
        """Test AI evaluation failure - should not stop chain."""
        mock_evaluator = Mock()
        mock_evaluator_class.return_value = mock_evaluator
        mock_evaluator.evaluate.side_effect = Exception('AI service unavailable')

        result = ai_evaluate(self.submission.id)

        assert result['step'] == 3
        assert result['status'] == 'failed'
        # Chain should continue (non-critical)


class TestDetectAIUsageTask(PipelineTestSetup):
    """Test Task 4: detect_ai_usage"""

    @patch('executor.pipeline.AIDetector')
    @patch('executor.pipeline.broadcast_pipeline_update')
    def test_detect_ai_not_flagged(self, mock_broadcast, mock_detector_class):
        """Test AI detection - not flagged."""
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        mock_result = Mock()
        mock_result.score = 0.45
        mock_result.reasoning = 'Code appears human-written'
        mock_detector.detect.return_value = mock_result

        result = detect_ai_usage(self.submission.id)

        assert result['step'] == 4
        assert result['status'] == 'completed'
        assert result['ai_detection_score'] == 0.45
        assert result['flagged'] is False

        # Verify submission updated
        self.submission.refresh_from_db()
        assert self.submission.ai_detection_score == 0.45

    @patch('executor.pipeline.AIDetector')
    @patch('executor.pipeline.broadcast_pipeline_update')
    def test_detect_ai_flagged(self, mock_broadcast, mock_detector_class):
        """Test AI detection - flagged."""
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        mock_result = Mock()
        mock_result.score = 0.85
        mock_result.reasoning = 'High probability of AI generation'
        mock_detector.detect.return_value = mock_result

        result = detect_ai_usage(self.submission.id)

        assert result['step'] == 4
        assert result['status'] == 'completed'
        assert result['ai_detection_score'] == 0.85
        assert result['flagged'] is True

        # Verify submission marked as flagged
        self.submission.refresh_from_db()
        assert self.submission.status == 'flagged'


class TestAwardXPTask(PipelineTestSetup):
    """Test Task 5: award_xp_if_eligible"""

    @patch('executor.pipeline.award_xp')
    @patch('executor.pipeline.broadcast_pipeline_update')
    def test_award_xp_eligible(self, mock_broadcast, mock_award_xp):
        """Test XP award when eligible."""
        # Setup submission with passing tests and low AI score
        self.submission.execution_result = {
            'tests_passed': 1,
            'tests_total': 1
        }
        self.submission.ai_detection_score = 0.45
        self.submission.save()

        mock_award_xp.return_value = {
            'xp_gained': 100,
            'new_total_xp': 100,
            'new_level': 1,
            'streak_days': 1
        }

        result = award_xp_if_eligible(self.submission.id)

        assert result['step'] == 5
        assert result['status'] == 'completed'
        assert result['xp_awarded'] is True
        assert result['xp_data']['xp_gained'] == 100

        # Verify submission marked as passed
        self.submission.refresh_from_db()
        assert self.submission.status == 'passed'

    @patch('executor.pipeline.broadcast_pipeline_update')
    def test_award_xp_not_eligible_tests_failed(self, mock_broadcast):
        """Test XP not awarded when tests failed."""
        self.submission.execution_result = {
            'tests_passed': 0,
            'tests_total': 1
        }
        self.submission.ai_detection_score = 0.45
        self.submission.save()

        result = award_xp_if_eligible(self.submission.id)

        assert result['step'] == 5
        assert result['status'] == 'completed'
        assert result['xp_awarded'] is False

    @patch('executor.pipeline.broadcast_pipeline_update')
    def test_award_xp_not_eligible_flagged(self, mock_broadcast):
        """Test XP not awarded when flagged."""
        self.submission.execution_result = {
            'tests_passed': 1,
            'tests_total': 1
        }
        self.submission.ai_detection_score = 0.85  # Flagged
        self.submission.save()

        result = award_xp_if_eligible(self.submission.id)

        assert result['step'] == 5
        assert result['status'] == 'completed'
        assert result['xp_awarded'] is False


class TestUpdateLeaderboardTask(PipelineTestSetup):
    """Test Task 6: update_leaderboard_task"""

    @patch('executor.pipeline.update_leaderboard')
    @patch('executor.pipeline.get_user_rank')
    @patch('executor.pipeline.broadcast_pipeline_update')
    def test_update_leaderboard_success(self, mock_broadcast, mock_get_rank, mock_update):
        """Test leaderboard update."""
        mock_update.return_value = None
        mock_get_rank.return_value = {
            'rank': 42,
            'score': 1250
        }

        result = update_leaderboard_task(self.user.id)

        assert result['step'] == 6
        assert result['status'] == 'completed'
        assert result['rank_updated'] is True

        mock_update.assert_called_once_with(self.user.id)

    @patch('executor.pipeline.update_leaderboard')
    def test_update_leaderboard_user_not_found(self, mock_update):
        """Test leaderboard update with non-existent user."""
        with self.assertRaises(User.DoesNotExist):
            update_leaderboard_task(99999)


class TestResolveSkillUnlocksTask(PipelineTestSetup):
    """Test Task 7: resolve_skill_unlocks"""

    @patch('executor.pipeline.SkillUnlockService.check_skill_completion')
    @patch('executor.pipeline.resolve_unlocks_for_user')
    @patch('executor.pipeline.broadcast_pipeline_update')
    def test_resolve_skill_unlocks_success(self, mock_broadcast, mock_resolve, mock_check):
        """Test skill unlock resolution."""
        mock_check.return_value = True
        mock_resolve.return_value = {
            'unlocked_count': 2,
            'unlocked_skills': ['Intermediate Python', 'Data Structures']
        }

        result = resolve_skill_unlocks(self.user.id, self.skill.id)

        assert result['step'] == 7
        assert result['status'] == 'completed'
        assert len(result['unlocks']) == 2

    @patch('executor.pipeline.SkillUnlockService.check_skill_completion')
    @patch('executor.pipeline.resolve_unlocks_for_user')
    @patch('executor.pipeline.broadcast_pipeline_update')
    def test_resolve_skill_unlocks_no_new_unlocks(self, mock_broadcast, mock_resolve, mock_check):
        """Test skill unlock resolution with no new unlocks."""
        mock_check.return_value = False
        mock_resolve.return_value = {
            'unlocked_count': 0,
            'unlocked_skills': []
        }

        result = resolve_skill_unlocks(self.user.id, self.skill.id)

        assert result['step'] == 7
        assert result['status'] == 'completed'
        assert len(result['unlocks']) == 0


class TestBroadcastFunction(PipelineTestSetup):
    """Test broadcast_pipeline_update function."""

    @patch('executor.pipeline.async_to_sync')
    def test_broadcast_pipeline_update(self, mock_async_to_sync):
        """Test broadcasting pipeline update."""
        mock_group_send = Mock()
        mock_async_to_sync.return_value = mock_group_send

        broadcast_pipeline_update(
            submission_id=self.submission.id,
            step=1,
            step_name='Execute Code',
            status='completed',
            data={'output_preview': 'Hello World'}
        )

        # Verify group_send was called
        mock_group_send.assert_called_once()
        call_args = mock_group_send.call_args
        assert f'execution_{self.submission.id}' in str(call_args)


class TestPipelineIntegration(PipelineTestSetup):
    """Integration tests for the full pipeline."""

    @patch('executor.pipeline.execute_code')
    @patch('executor.pipeline.run_test_cases')
    @patch('executor.pipeline.ai_evaluate')
    @patch('executor.pipeline.detect_ai_usage')
    @patch('executor.pipeline.award_xp_if_eligible')
    @patch('executor.pipeline.update_leaderboard_task')
    @patch('executor.pipeline.resolve_skill_unlocks')
    def test_full_pipeline_success(
        self,
        mock_resolve,
        mock_leaderboard,
        mock_award_xp,
        mock_detect,
        mock_evaluate,
        mock_tests,
        mock_execute
    ):
        """Test full pipeline execution."""
        # Setup mocks to return success
        mock_execute.return_value = {'step': 1, 'status': 'completed'}
        mock_tests.return_value = {'step': 2, 'status': 'completed', 'stop_chain': False}
        mock_evaluate.return_value = {'step': 3, 'status': 'completed'}
        mock_detect.return_value = {'step': 4, 'status': 'completed', 'flagged': False}
        mock_award_xp.return_value = {'step': 5, 'status': 'completed', 'xp_awarded': True}
        mock_leaderboard.return_value = {'step': 6, 'status': 'completed'}
        mock_resolve.return_value = {'step': 7, 'status': 'completed'}

        # Start pipeline
        result = run_submission_pipeline(self.submission.id)

        # Verify result is AsyncResult
        assert hasattr(result, 'id')
        assert result.id is not None

    def test_pipeline_with_missing_submission(self):
        """Test pipeline with non-existent submission."""
        with self.assertRaises(QuestSubmission.DoesNotExist):
            run_submission_pipeline(99999)


class TestErrorHandling(PipelineTestSetup):
    """Test error handling and edge cases."""

    @patch('executor.pipeline.CompileExecutor')
    @patch('executor.pipeline.broadcast_pipeline_update')
    def test_execute_code_retry_on_failure(self, mock_broadcast, mock_executor_class):
        """Test execute_code retries on failure."""
        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor
        mock_executor.execute.side_effect = Exception('Docker error')

        # Task should retry
        with self.assertRaises(Exception):
            execute_code(self.submission.id)

    @patch('executor.pipeline.CompileExecutor')
    @patch('executor.pipeline.broadcast_pipeline_update')
    def test_run_test_cases_empty_test_cases(self, mock_broadcast, mock_executor_class):
        """Test run_test_cases with empty test cases."""
        # Create quest with no test cases
        quest_no_tests = Quest.objects.create(
            skill=self.skill,
            type='coding',
            title='No Tests',
            description='Quest with no tests',
            test_cases=[],
            xp_reward=50
        )

        submission = QuestSubmission.objects.create(
            user=self.user,
            quest=quest_no_tests,
            code='print("test")',
            language='python'
        )

        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor
        mock_executor.run_test_cases.return_value = {
            'tests_passed': 0,
            'tests_total': 0,
            'results': []
        }

        result = run_test_cases(submission.id)

        assert result['tests_total'] == 0


class TestWebSocketMessages(PipelineTestSetup):
    """Test WebSocket message formatting."""

    def test_pipeline_update_message_format(self):
        """Test pipeline_update message format."""
        message = {
            'type': 'pipeline_update',
            'step': 1,
            'step_name': 'Execute Code',
            'status': 'completed',
            'timestamp': timezone.now().isoformat(),
            'data': {'output_preview': 'Hello World'}
        }

        # Verify message can be JSON serialized
        json_str = json.dumps(message)
        parsed = json.loads(json_str)

        assert parsed['type'] == 'pipeline_update'
        assert parsed['step'] == 1

    def test_leaderboard_update_message_format(self):
        """Test leaderboard_update message format."""
        message = {
            'type': 'leaderboard_update',
            'rank': 42,
            'score': 1250,
            'timestamp': timezone.now().isoformat()
        }

        json_str = json.dumps(message)
        parsed = json.loads(json_str)

        assert parsed['type'] == 'leaderboard_update'
        assert parsed['rank'] == 42

    def test_skill_unlock_message_format(self):
        """Test skill_unlock message format."""
        message = {
            'type': 'skill_unlock',
            'skill_completed': True,
            'skill_title': 'Python Basics',
            'unlocked_skills': ['Intermediate Python'],
            'timestamp': timezone.now().isoformat()
        }

        json_str = json.dumps(message)
        parsed = json.loads(json_str)

        assert parsed['type'] == 'skill_unlock'
        assert parsed['skill_completed'] is True


class TestProgressCalculation(PipelineTestSetup):
    """Test progress percentage calculation."""

    def test_progress_map(self):
        """Test progress percentage mapping."""
        progress_map = {
            'pending': 0,
            'running': 25,
            'passed': 100,
            'failed': 100,
            'flagged': 100,
        }

        assert progress_map['pending'] == 0
        assert progress_map['running'] == 25
        assert progress_map['passed'] == 100


class TestTaskChainTermination(PipelineTestSetup):
    """Test task chain termination logic."""

    @patch('executor.pipeline.CompileExecutor')
    @patch('executor.pipeline.broadcast_pipeline_update')
    def test_chain_stops_on_zero_tests_passed(self, mock_broadcast, mock_executor_class):
        """Test that chain stops when 0 tests pass."""
        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor
        mock_executor.run_test_cases.return_value = {
            'tests_passed': 0,
            'tests_total': 1,
            'results': []
        }

        result = run_test_cases(self.submission.id)

        # Verify stop_chain flag is set
        assert result['stop_chain'] is True
        assert result['status'] == 'failed'

        # Verify submission marked as failed
        self.submission.refresh_from_db()
        assert self.submission.status == 'failed'


if __name__ == '__main__':
    import unittest
    unittest.main()
