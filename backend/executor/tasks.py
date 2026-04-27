"""
SkillTree AI - Executor Celery Tasks
Async code evaluation pipeline: execute → AI evaluate → AI detect → update XP.
Also exports pipeline tasks from pipeline.py for Celery autodiscovery.
"""

import logging
from celery import shared_task

# Import pipeline tasks so Celery autodiscovers them
from executor.pipeline import (  # noqa: F401
    execute_code,
    run_test_cases,
    ai_evaluate,
    detect_ai_usage,
    award_xp_if_eligible,
    update_leaderboard_task,
    resolve_skill_unlocks,
    run_submission_pipeline,
)

logger = logging.getLogger(__name__)


@shared_task(name='executor.tasks.evaluate_submission', bind=True, max_retries=2)
def evaluate_submission(self, submission_id):
    """
    Full evaluation pipeline for a quest submission:
    1. Run code against test cases (Docker)
    2. AI code quality evaluation (LM Studio)
    3. AI detection check
    4. Award XP if passed
    5. Update leaderboard score
    """
    try:
        from quests.models import QuestSubmission
        from executor.services import executor

        submission = QuestSubmission.objects.select_related('quest', 'user').get(id=submission_id)
        submission.status = 'running'
        submission.save(update_fields=['status'])

        quest = submission.quest
        user = submission.user

        # 1. Run test cases — try Docker first, fall back to AI simulation
        test_cases = [
            {'input': tc.get('input', ''), 'expected': tc.get('expected_output', tc.get('expected', ''))}
            for tc in (quest.test_cases or [])
        ]

        if test_cases:
            # Try Docker execution first
            exec_result = executor.run_test_cases(submission.code, submission.language, test_cases)
            tests_passed = exec_result.get('tests_passed', 0)
            tests_total = exec_result.get('tests_total', 0)

            # If Docker unavailable (all failed with runtime_error/stderr), fall back to AI simulation
            raw_results = exec_result.get('results', [])
            docker_failed = tests_total > 0 and all(
                r.get('status') in ('runtime_error', 'tle', 'mle', 'compile_error')
                or 'Docker is not available' in str(r.get('actual', ''))
                or 'Docker is not available' in str(exec_result.get('stderr', ''))
                for r in raw_results
            ) if raw_results else False

            if docker_failed or (tests_total > 0 and tests_passed == 0 and not raw_results):
                # Try AI simulation as fallback
                try:
                    from executor.ai_executor import ai_executor
                    if ai_executor.is_available():
                        logger.info(f"Docker unavailable, using AI simulation for submission {submission_id}")
                        exec_result = ai_executor.simulate_execution(
                            submission.code, submission.language, test_cases
                        )
                        tests_passed = exec_result.get('tests_passed', 0)
                        tests_total = exec_result.get('tests_total', 0)
                        raw_results = exec_result.get('results', [])
                except Exception as e:
                    logger.warning(f"AI simulation fallback failed: {e}")

            test_results = [
                {
                    'input': r.get('input', ''),
                    'expected': r.get('expected', ''),
                    'actual': r.get('actual', ''),
                    'status': 'passed' if r.get('passed') else 'failed',
                    'time_ms': r.get('time_ms', 0),
                }
                for r in raw_results
            ]
            all_passed = tests_total > 0 and tests_passed == tests_total
        else:
            # No test cases — just execute and check for errors
            exec_result = executor.execute(submission.code, submission.language)
            all_passed = exec_result.get('status') == 'ok'
            tests_passed = 1 if all_passed else 0
            tests_total = 1
            test_results = []

        submission.execution_result = {
            'output': exec_result.get('output', ''),
            'stderr': exec_result.get('stderr', ''),
            'exit_code': exec_result.get('exit_code', -1),
            'time_ms': exec_result.get('execution_time_ms', 0),
            'tests_passed': tests_passed,
            'tests_total': tests_total,
            'test_results': test_results,
        }

        # 2. AI evaluation (best-effort)
        ai_feedback = {}
        try:
            from ai_evaluation.services import AIEvaluator
            evaluator = AIEvaluator()
            ai_feedback = evaluator.evaluate(submission)
        except Exception as e:
            logger.warning(f"AI evaluation skipped for submission {submission_id}: {e}")

        submission.ai_feedback = ai_feedback

        # 3. AI detection (best-effort)
        detection_score = 0.0
        try:
            from ai_detection.views import detect_ai_code
            detection_result = detect_ai_code(submission_id)
            if detection_result:
                detection_score = detection_result.final_score
        except Exception as e:
            logger.warning(f"AI detection skipped for submission {submission_id}: {e}")

        submission.ai_detection_score = detection_score

        # 4. Determine final status
        if detection_score >= 0.85:
            submission.status = 'flagged'
        elif all_passed:
            submission.status = 'passed'
        else:
            submission.status = 'failed'

        submission.save()

        # 5. Award XP if passed (only first time)
        if submission.status == 'passed':
            already_awarded = QuestSubmission.objects.filter(
                user=user, quest=quest, status='passed'
            ).exclude(id=submission_id).exists()

            if not already_awarded:
                xp_earned = int(quest.xp_reward * quest.difficulty_multiplier)
                user.xp += xp_earned
                user.save(update_fields=['xp', 'level'])

                # Log XP
                from users.models import XPLog
                XPLog.objects.create(
                    user=user,
                    amount=xp_earned,
                    source=f"Quest: {quest.title}"
                )

                # Update streak
                _update_streak(user)

                # Update leaderboard
                try:
                    from leaderboard.tasks import refresh_user_score
                    refresh_user_score.delay(user.id)
                except Exception as e:
                    logger.warning(f"Leaderboard update skipped: {e}")

        logger.info(
            f"evaluate_submission complete: submission={submission_id} "
            f"status={submission.status} passed={tests_passed}/{tests_total}"
        )
        return {'status': submission.status, 'tests_passed': tests_passed, 'tests_total': tests_total}

    except Exception as exc:
        logger.error(f"evaluate_submission failed for {submission_id}: {exc}", exc_info=True)
        try:
            from quests.models import QuestSubmission
            QuestSubmission.objects.filter(id=submission_id).update(status='failed')
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=10)


def _update_streak(user):
    """Update user's daily streak."""
    from django.utils import timezone
    from datetime import date, timedelta

    today = timezone.now().date()
    last_active = user.last_active

    if last_active is None:
        user.streak_days = 1
    elif last_active == today:
        return  # Already active today
    elif last_active == today - timedelta(days=1):
        user.streak_days += 1
    else:
        user.streak_days = 1  # Streak broken

    user.last_active = today
    user.save(update_fields=['streak_days', 'last_active'])
