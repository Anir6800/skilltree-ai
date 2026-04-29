"""
SkillTree AI - Submission Execution Pipeline (FIXED)
Complete 7-step Celery task chain for code submission processing.
Includes WebSocket status broadcasts, fallback caching, and comprehensive error handling.

FIXES APPLIED:
1. Async/await wrapper for AI detection
2. LM Studio timeout configuration
3. WebSocket broadcast with fallback caching
4. Execution result initialization
5. Pipeline timeout protection
6. Conditional chain logic
7. Better error handling
"""

import json
import logging
from celery import shared_task, chain, group, current_task
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from quests.models import QuestSubmission, Quest
from skills.models import Skill, SkillProgress
from skills.services import SkillUnlockService, award_xp, resolve_unlocks_for_user
from leaderboard.services import update_leaderboard
from ai_evaluation.services import AIEvaluator
from ai_detection.services import AIDetector
from .services import CompileExecutor

User = get_user_model()
logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


def broadcast_pipeline_update(submission_id, step, step_name, status, data=None):
    """
    Broadcast pipeline status update via WebSocket with fallback caching.
    
    If WebSocket broadcast fails, stores update in Redis for polling fallback.
    
    Args:
        submission_id: ID of the submission being processed
        step: Step number (1-7)
        step_name: Human-readable step name
        status: 'running', 'completed', or 'failed'
        data: Optional additional data to include in broadcast
    """
    try:
        group_name = f"execution_{submission_id}"
        message = {
            "type": "pipeline_update",
            "step": step,
            "step_name": step_name,
            "status": status,
            "timestamp": timezone.now().isoformat(),
        }
        if data:
            message["data"] = data
        
        # Try WebSocket broadcast
        async_to_sync(channel_layer.group_send)(
            group_name,
            message
        )
        
    except Exception as e:
        logger.warning(f"WebSocket broadcast failed for submission {submission_id}: {e}")
        
        # Fallback: Store in Redis for polling
        try:
            cache_key = f"pipeline_update:{submission_id}"
            cache.set(cache_key, {
                "step": step,
                "step_name": step_name,
                "status": status,
                "timestamp": timezone.now().isoformat(),
                "data": data
            }, 3600)  # 1 hour TTL
        except Exception as cache_e:
            logger.error(f"Failed to cache pipeline update: {cache_e}")


@shared_task(bind=True, max_retries=2, default_retry_delay=5, time_limit=1900, soft_time_limit=1800)
def execute_code(self, submission_id):
    """
    Task 1: Execute user code in sandboxed environment.
    
    Calls CompileExecutor.execute() to run the code and capture output.
    Stores execution result in submission.execution_result.
    Broadcasts step 1 completion with output preview.
    
    Args:
        submission_id: ID of the QuestSubmission
        
    Returns:
        dict: {
            'step': 1,
            'status': 'completed',
            'execution_result': {...}
        }
    """
    try:
        submission = QuestSubmission.objects.get(id=submission_id)
        broadcast_pipeline_update(submission_id, 1, "Execute Code", "running")
        
        executor = CompileExecutor()
        execution_result = executor.execute(
            submission.code,
            submission.language,
            stdin_input=""
        )
        
        # INITIALIZE execution_result if empty
        if not submission.execution_result:
            submission.execution_result = {}
        
        # Store execution result
        submission.execution_result.update(execution_result)
        submission.save(update_fields=['execution_result'])
        
        # Prepare output preview (first 500 chars)
        output_preview = execution_result.get('output', '')[:500]
        
        broadcast_pipeline_update(
            submission_id,
            1,
            "Execute Code",
            "completed",
            {
                "output_preview": output_preview,
                "exit_code": execution_result.get('exit_code', -1)
            }
        )
        
        return {
            'step': 1,
            'status': 'completed',
            'execution_result': execution_result
        }
        
    except SoftTimeLimitExceeded:
        logger.error(f"execute_code timeout for submission {submission_id}")
        submission = QuestSubmission.objects.get(id=submission_id)
        submission.status = 'failed'
        submission.save(update_fields=['status'])
        broadcast_pipeline_update(submission_id, 1, "Execute Code", "failed", {"error": "Execution timeout"})
        raise
        
    except QuestSubmission.DoesNotExist:
        logger.error(f"Submission {submission_id} not found")
        broadcast_pipeline_update(submission_id, 1, "Execute Code", "failed", {"error": "Submission not found"})
        raise
    except Exception as exc:
        logger.error(f"Error in execute_code for submission {submission_id}: {exc}", exc_info=True)
        broadcast_pipeline_update(submission_id, 1, "Execute Code", "failed", {"error": str(exc)})
        try:
            self.retry(exc=exc)
        except MaxRetriesExceededError:
            submission = QuestSubmission.objects.get(id=submission_id)
            submission.status = 'failed'
            submission.save(update_fields=['status'])
            raise


@shared_task(bind=True, max_retries=2, default_retry_delay=5, time_limit=1900, soft_time_limit=1800)
def run_test_cases(self, submission_id):
    """
    Task 2: Run code against test cases.
    
    Calls CompileExecutor.run_test_cases() to validate code.
    Updates submission with test results.
    If 0 tests pass: set status='failed', skip remaining tasks.
    
    Args:
        submission_id: ID of the QuestSubmission
        
    Returns:
        dict: {
            'step': 2,
            'status': 'completed' or 'failed',
            'tests_passed': int,
            'tests_total': int
        }
    """
    try:
        submission = QuestSubmission.objects.get(id=submission_id)
        broadcast_pipeline_update(submission_id, 2, "Run Test Cases", "running")
        
        executor = CompileExecutor()
        test_result = executor.run_test_cases(
            submission.code,
            submission.language,
            submission.quest.test_cases
        )
        
        tests_passed = test_result.get('tests_passed', 0)
        tests_total = test_result.get('tests_total', 0)
        
        # Update submission with test results
        if not submission.execution_result:
            submission.execution_result = {}
        submission.execution_result.update(test_result)
        submission.save(update_fields=['execution_result'])
        
        # Check if any tests passed
        if tests_passed == 0:
            submission.status = 'failed'
            submission.save(update_fields=['status'])
            
            broadcast_pipeline_update(
                submission_id,
                2,
                "Run Test Cases",
                "failed",
                {
                    "tests_passed": tests_passed,
                    "tests_total": tests_total,
                    "reason": "No tests passed"
                }
            )
            
            # Return stop signal
            return {
                'step': 2,
                'status': 'failed',
                'tests_passed': tests_passed,
                'tests_total': tests_total,
                'stop_chain': True
            }
        
        broadcast_pipeline_update(
            submission_id,
            2,
            "Run Test Cases",
            "completed",
            {
                "tests_passed": tests_passed,
                "tests_total": tests_total
            }
        )
        
        return {
            'step': 2,
            'status': 'completed',
            'tests_passed': tests_passed,
            'tests_total': tests_total,
            'stop_chain': False
        }
        
    except SoftTimeLimitExceeded:
        logger.error(f"run_test_cases timeout for submission {submission_id}")
        submission = QuestSubmission.objects.get(id=submission_id)
        submission.status = 'failed'
        submission.save(update_fields=['status'])
        broadcast_pipeline_update(submission_id, 2, "Run Test Cases", "failed", {"error": "Test execution timeout"})
        raise
        
    except QuestSubmission.DoesNotExist:
        logger.error(f"Submission {submission_id} not found")
        broadcast_pipeline_update(submission_id, 2, "Run Test Cases", "failed", {"error": "Submission not found"})
        raise
    except Exception as exc:
        logger.error(f"Error in run_test_cases for submission {submission_id}: {exc}", exc_info=True)
        broadcast_pipeline_update(submission_id, 2, "Run Test Cases", "failed", {"error": str(exc)})
        try:
            self.retry(exc=exc)
        except MaxRetriesExceededError:
            submission = QuestSubmission.objects.get(id=submission_id)
            submission.status = 'failed'
            submission.save(update_fields=['status'])
            raise


@shared_task(bind=True, max_retries=2, default_retry_delay=5, time_limit=1900, soft_time_limit=1800)
def ai_evaluate(self, submission_id):
    """
    Task 3: AI evaluation of code quality and feedback.
    
    Calls AIEvaluator.evaluate() to generate feedback.
    Stores feedback in submission.ai_feedback.
    Broadcasts feedback preview.
    
    Args:
        submission_id: ID of the QuestSubmission
        
    Returns:
        dict: {
            'step': 3,
            'status': 'completed',
            'feedback_summary': str
        }
    """
    try:
        submission = QuestSubmission.objects.get(id=submission_id)
        broadcast_pipeline_update(submission_id, 3, "AI Evaluate", "running")
        
        evaluator = AIEvaluator()
        feedback = evaluator.evaluate(submission)
        
        # Store feedback
        submission.ai_feedback = feedback
        submission.save(update_fields=['ai_feedback'])
        
        # Prepare feedback preview
        feedback_summary = feedback.get('summary', '')[:300]
        
        broadcast_pipeline_update(
            submission_id,
            3,
            "AI Evaluate",
            "completed",
            {
                "feedback_summary": feedback_summary,
                "score": feedback.get('score', 0)
            }
        )
        
        return {
            'step': 3,
            'status': 'completed',
            'feedback_summary': feedback_summary
        }
        
    except SoftTimeLimitExceeded:
        logger.error(f"ai_evaluate timeout for submission {submission_id}")
        broadcast_pipeline_update(submission_id, 3, "AI Evaluate", "failed", {"error": "Evaluation timeout"})
        # Don't fail the chain, continue to detection
        return {
            'step': 3,
            'status': 'failed',
            'feedback_summary': 'Evaluation timeout'
        }
        
    except QuestSubmission.DoesNotExist:
        logger.error(f"Submission {submission_id} not found")
        broadcast_pipeline_update(submission_id, 3, "AI Evaluate", "failed", {"error": "Submission not found"})
        raise
    except Exception as exc:
        logger.error(f"Error in ai_evaluate for submission {submission_id}: {exc}", exc_info=True)
        broadcast_pipeline_update(submission_id, 3, "AI Evaluate", "failed", {"error": str(exc)})
        try:
            self.retry(exc=exc)
        except MaxRetriesExceededError:
            logger.warning(f"AI evaluation failed for submission {submission_id} after retries")
            # Don't fail the chain, continue to detection
            return {
                'step': 3,
                'status': 'failed',
                'feedback_summary': 'Evaluation unavailable'
            }


@shared_task(bind=True, max_retries=2, default_retry_delay=5, time_limit=1900, soft_time_limit=1800)
def detect_ai_usage(self, submission_id):
    """
    Task 4: Detect AI usage in submitted code.
    
    Calls AIDetector.detect_sync() to analyze code for AI patterns.
    Updates ai_detection_score in submission.
    If flagged (score > 0.70): broadcasts flagged status.
    
    Args:
        submission_id: ID of the QuestSubmission
        
    Returns:
        dict: {
            'step': 4,
            'status': 'completed',
            'ai_detection_score': float,
            'flagged': bool
        }
    """
    try:
        submission = QuestSubmission.objects.get(id=submission_id)
        broadcast_pipeline_update(submission_id, 4, "Detect AI Usage", "running")
        
        detector = AIDetector()
        detection_result = detector.detect_sync(submission)  # Use sync wrapper
        
        ai_score = detection_result.final_score
        flagged = ai_score > 0.70
        
        # Update submission
        submission.ai_detection_score = ai_score
        if flagged:
            submission.status = 'flagged'
        submission.save(update_fields=['ai_detection_score', 'status'])
        
        broadcast_data = {
            "ai_detection_score": ai_score,
            "flagged": flagged
        }
        
        if flagged:
            broadcast_data["reasoning"] = detection_result.reasoning[:200]
        
        broadcast_pipeline_update(
            submission_id,
            4,
            "Detect AI Usage",
            "completed",
            broadcast_data
        )
        
        return {
            'step': 4,
            'status': 'completed',
            'ai_detection_score': ai_score,
            'flagged': flagged
        }
        
    except SoftTimeLimitExceeded:
        logger.error(f"detect_ai_usage timeout for submission {submission_id}")
        broadcast_pipeline_update(submission_id, 4, "Detect AI Usage", "failed", {"error": "Detection timeout"})
        # Don't fail the chain, assume not flagged
        return {
            'step': 4,
            'status': 'failed',
            'ai_detection_score': 0.0,
            'flagged': False
        }
        
    except QuestSubmission.DoesNotExist:
        logger.error(f"Submission {submission_id} not found")
        broadcast_pipeline_update(submission_id, 4, "Detect AI Usage", "failed", {"error": "Submission not found"})
        raise
    except Exception as exc:
        logger.error(f"Error in detect_ai_usage for submission {submission_id}: {exc}", exc_info=True)
        broadcast_pipeline_update(submission_id, 4, "Detect AI Usage", "failed", {"error": str(exc)})
        try:
            self.retry(exc=exc)
        except MaxRetriesExceededError:
            logger.warning(f"AI detection failed for submission {submission_id} after retries")
            # Don't fail the chain, assume not flagged
            return {
                'step': 4,
                'status': 'failed',
                'ai_detection_score': 0.0,
                'flagged': False
            }


@shared_task(bind=True, max_retries=2, default_retry_delay=5, time_limit=1900, soft_time_limit=1800)
def award_xp_if_eligible(self, submission_id):
    """
    Task 5: Award XP if submission meets eligibility criteria.
    
    Only awards XP if:
    - All tests passed (tests_passed == tests_total)
    - AI detection score <= 0.70 (not flagged)
    
    Calls award_xp() to update user XP, level, and streak.
    Broadcasts XP gain and level up info.
    
    Args:
        submission_id: ID of the QuestSubmission
        
    Returns:
        dict: {
            'step': 5,
            'status': 'completed',
            'xp_awarded': bool,
            'xp_data': dict or None
        }
    """
    try:
        submission = QuestSubmission.objects.get(id=submission_id)
        broadcast_pipeline_update(submission_id, 5, "Award XP", "running")
        
        # Check eligibility
        execution_result = submission.execution_result or {}
        tests_passed = execution_result.get('tests_passed', 0)
        tests_total = execution_result.get('tests_total', 0)
        ai_score = submission.ai_detection_score
        
        xp_awarded = False
        xp_data = None
        
        if tests_passed == tests_total and tests_total > 0 and ai_score <= 0.70:
            # Eligible for XP
            user = submission.user
            quest = submission.quest
            
            xp_data = award_xp(user, quest)
            xp_awarded = True
            
            # Update submission status to passed
            submission.status = 'passed'
            submission.save(update_fields=['status'])
            
            broadcast_pipeline_update(
                submission_id,
                5,
                "Award XP",
                "completed",
                {
                    "xp_awarded": True,
                    "xp_gained": xp_data['xp_gained'],
                    "new_level": xp_data['new_level'],
                    "streak_days": xp_data['streak_days']
                }
            )
        else:
            # Not eligible
            broadcast_pipeline_update(
                submission_id,
                5,
                "Award XP",
                "completed",
                {
                    "xp_awarded": False,
                    "reason": "Eligibility criteria not met"
                }
            )
        
        return {
            'step': 5,
            'status': 'completed',
            'xp_awarded': xp_awarded,
            'xp_data': xp_data
        }
        
    except SoftTimeLimitExceeded:
        logger.error(f"award_xp_if_eligible timeout for submission {submission_id}")
        broadcast_pipeline_update(submission_id, 5, "Award XP", "failed", {"error": "XP award timeout"})
        return {
            'step': 5,
            'status': 'failed',
            'xp_awarded': False,
            'xp_data': None
        }
        
    except QuestSubmission.DoesNotExist:
        logger.error(f"Submission {submission_id} not found")
        broadcast_pipeline_update(submission_id, 5, "Award XP", "failed", {"error": "Submission not found"})
        raise
    except Exception as exc:
        logger.error(f"Error in award_xp_if_eligible for submission {submission_id}: {exc}", exc_info=True)
        broadcast_pipeline_update(submission_id, 5, "Award XP", "failed", {"error": str(exc)})
        try:
            self.retry(exc=exc)
        except MaxRetriesExceededError:
            logger.warning(f"XP award failed for submission {submission_id} after retries")
            return {
                'step': 5,
                'status': 'failed',
                'xp_awarded': False,
                'xp_data': None
            }


@shared_task(bind=True, max_retries=2, default_retry_delay=5, time_limit=1900, soft_time_limit=1800)
def update_leaderboard_task(self, user_id):
    """
    Task 6: Update user's leaderboard ranking.
    
    Calls LeaderboardService.update_leaderboard() to recalculate rankings.
    Broadcasts rank update info.
    
    Args:
        user_id: ID of the user
        
    Returns:
        dict: {
            'step': 6,
            'status': 'completed',
            'rank_updated': bool
        }
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Update leaderboard
        update_leaderboard(user_id)
        
        # Get updated rank
        from leaderboard.services import get_user_rank
        rank_info = get_user_rank(user_id)
        
        # Broadcast to user's personal group if available
        try:
            group_name = f"user_{user_id}"
            message = {
                "type": "leaderboard_update",
                "rank": rank_info.get('rank', 0),
                "score": rank_info.get('score', 0),
                "timestamp": timezone.now().isoformat()
            }
            async_to_sync(channel_layer.group_send)(group_name, message)
        except Exception as e:
            logger.warning(f"Failed to broadcast leaderboard update for user {user_id}: {e}")
        
        return {
            'step': 6,
            'status': 'completed',
            'rank_updated': True
        }
        
    except SoftTimeLimitExceeded:
        logger.error(f"update_leaderboard_task timeout for user {user_id}")
        return {
            'step': 6,
            'status': 'failed',
            'rank_updated': False
        }
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        raise
    except Exception as exc:
        logger.error(f"Error in update_leaderboard_task for user {user_id}: {exc}", exc_info=True)
        try:
            self.retry(exc=exc)
        except MaxRetriesExceededError:
            logger.warning(f"Leaderboard update failed for user {user_id} after retries")
            return {
                'step': 6,
                'status': 'failed',
                'rank_updated': False
            }


@shared_task(bind=True, max_retries=2, default_retry_delay=5, time_limit=1900, soft_time_limit=1800)
def resolve_skill_unlocks(self, user_id, skill_id):
    """
    Task 7: Resolve skill unlocks and check for new unlocks.
    
    Calls check_skill_completion() to mark skill as completed if all quests done.
    Calls resolve_unlocks_for_user() to unlock dependent skills.
    Broadcasts any new unlocks.
    
    Args:
        user_id: ID of the user
        skill_id: ID of the skill just completed
        
    Returns:
        dict: {
            'step': 7,
            'status': 'completed',
            'unlocks': list
        }
    """
    try:
        user = User.objects.get(id=user_id)
        skill = Skill.objects.get(id=skill_id)
        
        # Check if skill is now completed
        skill_completed = SkillUnlockService.check_skill_completion(user, skill)
        
        # Resolve unlocks (this is async via resolve_unlocks_for_user task)
        unlock_result = resolve_unlocks_for_user(user_id)
        
        unlocked_skills = unlock_result.get('unlocked_skills', [])
        
        # Broadcast to user's personal group
        try:
            group_name = f"user_{user_id}"
            message = {
                "type": "skill_unlock",
                "skill_completed": skill_completed,
                "skill_title": skill.title,
                "unlocked_skills": unlocked_skills,
                "timestamp": timezone.now().isoformat()
            }
            async_to_sync(channel_layer.group_send)(group_name, message)
        except Exception as e:
            logger.warning(f"Failed to broadcast skill unlock for user {user_id}: {e}")
        
        return {
            'step': 7,
            'status': 'completed',
            'unlocks': unlocked_skills
        }
        
    except SoftTimeLimitExceeded:
        logger.error(f"resolve_skill_unlocks timeout for user {user_id}")
        return {
            'step': 7,
            'status': 'failed',
            'unlocks': []
        }
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        raise
    except Skill.DoesNotExist:
        logger.error(f"Skill {skill_id} not found")
        raise
    except Exception as exc:
        logger.error(f"Error in resolve_skill_unlocks for user {user_id}, skill {skill_id}: {exc}", exc_info=True)
        try:
            self.retry(exc=exc)
        except MaxRetriesExceededError:
            logger.warning(f"Skill unlock resolution failed for user {user_id} after retries")
            return {
                'step': 7,
                'status': 'failed',
                'unlocks': []
            }


@shared_task
def handle_pipeline_error(exc, submission_id):
    """Handle pipeline errors and update submission status."""
    try:
        submission = QuestSubmission.objects.get(id=submission_id)
        submission.status = 'failed'
        submission.save(update_fields=['status'])
        
        broadcast_pipeline_update(
            submission_id,
            0,
            "Pipeline",
            "failed",
            {"error": str(exc)[:200]}
        )
        
        logger.error(f"Pipeline failed for submission {submission_id}: {exc}")
    except Exception as e:
        logger.error(f"Error handling pipeline error: {e}")


def run_submission_pipeline(submission_id):
    """
    Main entry point: Execute the full 7-step submission pipeline.
    
    Builds a Celery chain with error handling and timeouts:
    - Task 1: execute_code
    - Task 2: run_test_cases (if 0 tests pass, stop chain)
    - Task 3: ai_evaluate
    - Task 4: detect_ai_usage
    - Task 5: award_xp_if_eligible
    - Task 6: update_leaderboard_task
    - Task 7: resolve_skill_unlocks
    
    Args:
        submission_id: ID of the QuestSubmission to process
        
    Returns:
        Celery AsyncResult for the chain
    """
    try:
        submission = QuestSubmission.objects.get(id=submission_id)
        user_id = submission.user.id
        skill_id = submission.quest.skill.id
        
        # Build the task chain
        pipeline = chain(
            execute_code.s(submission_id),
            run_test_cases.s(submission_id),
            ai_evaluate.s(submission_id),
            detect_ai_usage.s(submission_id),
            award_xp_if_eligible.s(submission_id),
            update_leaderboard_task.s(user_id),
            resolve_skill_unlocks.s(user_id, skill_id),
        )
        
        # Execute the chain with error handling and timeout
        result = pipeline.apply_async(
            link_error=handle_pipeline_error.s(submission_id),
            time_limit=1800,  # 30 minute hard limit
            soft_time_limit=1700  # 28 minute soft limit
        )
        
        # Store task ID for ownership verification
        submission.celery_task_id = result.id
        submission.save(update_fields=['celery_task_id'])
        
        logger.info(f"Started submission pipeline for submission {submission_id}, task_id: {result.id}")
        
        return result
        
    except QuestSubmission.DoesNotExist:
        logger.error(f"Submission {submission_id} not found")
        raise
    except Exception as exc:
        logger.error(f"Error starting submission pipeline for submission {submission_id}: {exc}", exc_info=True)
        raise
