"""
SkillTree AI - Adaptive Learning Engine
Bayesian ability scoring, difficulty reordering, skill flagging, and bridge quest generation.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from django.db.models import Q, Avg, Count
from django.utils import timezone
from quests.models import QuestSubmission, Quest
from skills.models import Skill, SkillProgress
from users.models import User

logger = logging.getLogger(__name__)


class AdaptiveTreeEngine:
    """
    Manages adaptive skill tree adjustments based on user performance signals.
    Implements Bayesian ability scoring and difficulty-based skill reordering.
    """

    LEARNING_RATE = 0.15
    ABILITY_MIN = 0.0
    ABILITY_MAX = 1.0
    DIFFICULTY_TIERS = 5
    CONSECUTIVE_FAIL_THRESHOLD = 3
    EASY_SKILL_THRESHOLD = 0.8
    EASY_SKILL_DIFFICULTY_CAP = 2
    FIRST_ATTEMPT_WINDOW = 10
    PERFORMANCE_WINDOW_DAYS = 30

    def __init__(self, user_id: int):
        """Initialize engine for a specific user."""
        try:
            self.user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ValueError(f"User {user_id} not found")

    def collect_performance_signals(self) -> Dict[str, Any]:
        """
        Collect performance metrics from recent quest submissions.
        Returns dict with solve_speed_percentile, consecutive_fails, first_attempt_pass_rate, hint_usage_rate.
        """
        cutoff_date = timezone.now() - timedelta(days=self.PERFORMANCE_WINDOW_DAYS)
        recent_submissions = QuestSubmission.objects.filter(
            user=self.user,
            created_at__gte=cutoff_date,
            status__in=['passed', 'failed']
        ).select_related('quest__skill')

        if not recent_submissions.exists():
            return {
                'solve_speed_percentile': 0.5,
                'consecutive_fails': 0,
                'first_attempt_pass_rate': 0.0,
                'hint_usage_rate': 0.0,
            }

        # Solve speed percentile: compare user's avg solve time vs global median
        user_solve_times = []
        for submission in recent_submissions:
            if submission.execution_result and 'time_ms' in submission.execution_result:
                user_solve_times.append(submission.execution_result['time_ms'])

        if user_solve_times:
            user_avg_time = sum(user_solve_times) / len(user_solve_times)
            global_median_time = self._get_global_median_solve_time()
            solve_speed_percentile = self._calculate_percentile(user_avg_time, global_median_time)
        else:
            solve_speed_percentile = 0.5

        # Consecutive fails: count recent consecutive failed submissions
        consecutive_fails = self._count_consecutive_fails(recent_submissions)

        # First attempt pass rate: % of quests passed on first try (last 10 quests)
        last_10_submissions = recent_submissions.order_by('-created_at')[:self.FIRST_ATTEMPT_WINDOW]
        first_attempt_passes = sum(
            1 for sub in last_10_submissions
            if sub.status == 'passed' and self._is_first_attempt(sub)
        )
        first_attempt_pass_rate = first_attempt_passes / len(last_10_submissions) if last_10_submissions else 0.0

        # Hint usage rate: % of quests where user requested a hint
        hint_usage_rate = self._calculate_hint_usage_rate(recent_submissions)

        return {
            'solve_speed_percentile': solve_speed_percentile,
            'consecutive_fails': consecutive_fails,
            'first_attempt_pass_rate': first_attempt_pass_rate,
            'hint_usage_rate': hint_usage_rate,
        }

    def update_ability_score(self, outcome: float) -> float:
        """
        Apply Bayesian update to user's ability score.
        outcome: 1.0 for fast first-pass, 0.0 for repeated fail, 0.5 for normal pass.
        Returns new ability score.
        """
        from users.models_adaptive import AdaptiveProfile

        profile = self._get_or_create_adaptive_profile()
        old_score = profile.ability_score

        new_score = old_score + self.LEARNING_RATE * (outcome - old_score)
        new_score = max(self.ABILITY_MIN, min(self.ABILITY_MAX, new_score))

        profile.ability_score = new_score
        profile.save()

        logger.info(f"User {self.user.id}: ability_score {old_score:.3f} -> {new_score:.3f} (outcome={outcome})")
        return new_score

    def update_preferred_difficulty(self) -> int:
        """
        Auto-set preferred_difficulty to ceil(ability_score * 5).
        Returns new preferred difficulty.
        """
        from users.models_adaptive import AdaptiveProfile

        profile = self._get_or_create_adaptive_profile()
        new_difficulty = max(1, min(self.DIFFICULTY_TIERS, int(profile.ability_score * self.DIFFICULTY_TIERS) + 1))
        profile.preferred_difficulty = new_difficulty
        profile.save()

        return new_difficulty

    def adapt_tree_for_user(self) -> Dict[str, Any]:
        """
        Main adaptation logic:
        1. Reorder skills in user's start_queue
        2. Flag "Too Easy" skills
        3. Flag "Challenging" skills
        4. Generate bridge quests for struggling skills
        Returns summary of changes.
        """
        from users.models_adaptive import AdaptiveProfile, UserSkillFlag

        profile = self._get_or_create_adaptive_profile()
        signals = self.collect_performance_signals()
        preferred_difficulty = profile.preferred_difficulty

        changes = {
            'reordered_skills': [],
            'flagged_too_easy': [],
            'flagged_struggling': [],
            'bridge_quests_generated': [],
        }

        # Get user's available skills
        user_skills = SkillProgress.objects.filter(
            user=self.user,
            status__in=['available', 'in_progress']
        ).select_related('skill')

        # 1. Reorder skills: deprioritize 2+ levels above, surface ±1 level
        reordered = self._reorder_skills_by_difficulty(user_skills, preferred_difficulty)
        changes['reordered_skills'] = [s.skill.id for s in reordered]

        # 2. Flag "Too Easy" skills
        for skill_progress in user_skills:
            skill = skill_progress.skill
            if profile.ability_score >= self.EASY_SKILL_THRESHOLD and skill.difficulty <= self.EASY_SKILL_DIFFICULTY_CAP:
                flag, created = UserSkillFlag.objects.get_or_create(
                    user=self.user,
                    skill=skill,
                    flag='too_easy',
                    defaults={'reason': 'Ability score indicates mastery of this difficulty level'}
                )
                if created:
                    changes['flagged_too_easy'].append(skill.id)

        # 3. Flag "Challenging" skills and generate bridge quests
        if signals['consecutive_fails'] >= self.CONSECUTIVE_FAIL_THRESHOLD:
            for skill_progress in user_skills:
                skill = skill_progress.skill
                flag, created = UserSkillFlag.objects.get_or_create(
                    user=self.user,
                    skill=skill,
                    flag='struggling',
                    defaults={'reason': f"Consecutive failures: {signals['consecutive_fails']}"}
                )
                if created:
                    changes['flagged_struggling'].append(skill.id)

                # Generate bridge quest at difficulty-1
                if skill.difficulty > 1:
                    bridge_quest = self._generate_bridge_quest(skill)
                    if bridge_quest:
                        changes['bridge_quests_generated'].append(bridge_quest.id)

        # Log adjustment
        profile.adjustment_history.append({
            'timestamp': timezone.now().isoformat(),
            'reason': 'Periodic adaptation',
            'signals': signals,
            'changes': {k: len(v) for k, v in changes.items()},
        })
        profile.save()

        return changes

    def _get_or_create_adaptive_profile(self):
        """Get or create AdaptiveProfile for user."""
        from users.models_adaptive import AdaptiveProfile

        profile, created = AdaptiveProfile.objects.get_or_create(user=self.user)
        return profile

    def _get_global_median_solve_time(self) -> float:
        """Get global median solve time across all users."""
        cutoff_date = timezone.now() - timedelta(days=self.PERFORMANCE_WINDOW_DAYS)
        submissions = QuestSubmission.objects.filter(
            created_at__gte=cutoff_date,
            status='passed'
        ).values_list('execution_result', flat=True)

        times = []
        for result in submissions:
            if result and 'time_ms' in result:
                times.append(result['time_ms'])

        if not times:
            return 5000.0

        times.sort()
        return times[len(times) // 2]

    def _calculate_percentile(self, user_time: float, global_median: float) -> float:
        """
        Calculate percentile: 1.0 if user is faster, 0.0 if slower.
        Normalized to [0, 1] range.
        """
        if global_median == 0:
            return 0.5
        ratio = user_time / global_median
        percentile = 1.0 / (1.0 + ratio)
        return max(0.0, min(1.0, percentile))

    def _count_consecutive_fails(self, submissions) -> int:
        """Count consecutive failed submissions from most recent."""
        count = 0
        for submission in submissions.order_by('-created_at'):
            if submission.status == 'failed':
                count += 1
            else:
                break
        return count

    def _is_first_attempt(self, submission: QuestSubmission) -> bool:
        """Check if this is the user's first attempt at this quest."""
        earlier_attempts = QuestSubmission.objects.filter(
            user=self.user,
            quest=submission.quest,
            created_at__lt=submission.created_at
        ).count()
        return earlier_attempts == 0

    def _calculate_hint_usage_rate(self, submissions) -> float:
        """Calculate % of submissions where user requested a hint."""
        if not submissions:
            return 0.0
        hint_count = sum(
            1 for sub in submissions
            if sub.execution_result and sub.execution_result.get('hint_requested', False)
        )
        return hint_count / len(submissions)

    def _reorder_skills_by_difficulty(self, user_skills, preferred_difficulty: int) -> List:
        """
        Reorder skills: prioritize ±1 level around preferred_difficulty.
        Deprioritize 2+ levels above.
        """
        ideal_range = (preferred_difficulty - 1, preferred_difficulty + 1)
        above_range = preferred_difficulty + 2

        ideal = []
        acceptable = []
        too_hard = []

        for skill_progress in user_skills:
            diff = skill_progress.skill.difficulty
            if ideal_range[0] <= diff <= ideal_range[1]:
                ideal.append(skill_progress)
            elif diff < ideal_range[0]:
                acceptable.append(skill_progress)
            else:
                too_hard.append(skill_progress)

        return ideal + acceptable + too_hard

    def _generate_bridge_quest(self, skill: Skill) -> Quest:
        """
        Generate a bridge quest at difficulty-1 level for struggling users.
        Uses LM Studio to create the quest.
        """
        from core.lm_client import LMStudioClient

        bridge_difficulty = max(1, skill.difficulty - 1)
        prompt = f"""
        Create a beginner-friendly quest for the skill: {skill.title}
        Description: {skill.description}
        Target difficulty: {bridge_difficulty}/5
        
        Return JSON with:
        - title: string (max 100 chars)
        - description: string (max 500 chars)
        - starter_code: string (optional)
        - test_cases: list of {{"input": "...", "expected_output": "..."}}
        """

        try:
            client = LMStudioClient()
            response = client.generate(prompt, max_tokens=1000)
            quest_data = self._parse_quest_response(response)

            bridge_quest = Quest.objects.create(
                skill=skill,
                type='coding',
                title=f"[Bridge] {quest_data.get('title', 'Practice')}",
                description=quest_data.get('description', ''),
                starter_code=quest_data.get('starter_code', ''),
                test_cases=quest_data.get('test_cases', []),
                xp_reward=int(50 * (bridge_difficulty / 5)),
                estimated_minutes=10,
                difficulty_multiplier=0.7,
            )
            logger.info(f"Generated bridge quest {bridge_quest.id} for skill {skill.id}")
            return bridge_quest
        except Exception as e:
            logger.error(f"Failed to generate bridge quest for skill {skill.id}: {e}")
            return None

    def _parse_quest_response(self, response: str) -> Dict[str, Any]:
        """Parse LM Studio response into quest data."""
        import json
        import re

        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass

        return {
            'title': 'Practice Problem',
            'description': response[:500],
            'starter_code': '',
            'test_cases': [],
        }
