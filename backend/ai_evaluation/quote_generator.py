"""
SkillTree AI - Quote Generator
Context-aware motivational quotes for quest results using LM Studio.
Implements tone rules based on outcome and caches results in Redis.
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from core.lm_client import lm_client, ExecutionServiceUnavailable
from quests.models import QuestSubmission

logger = logging.getLogger(__name__)

QUOTE_CACHE_TTL = 3600  # 1 hour
QUOTE_CACHE_KEY_PREFIX = "quote"


class QuoteGenerator:
    """
    Generates context-aware motivational quotes for quest submissions.
    Uses LM Studio with tone rules based on outcome and attempt history.
    Caches results in Redis to avoid regeneration.
    """

    def __init__(self):
        """Initialize quote generator with LM Studio client."""
        self.client = lm_client
        self.cache_ttl = QUOTE_CACHE_TTL

    def generate_result_quote(self, submission: QuestSubmission) -> str:
        """
        Generate a motivational quote for a quest submission result.

        Args:
            submission: QuestSubmission object with result data

        Returns:
            Motivational quote string (max 30 words, 2 sentences)
        """
        cache_key = self._get_cache_key(submission.id)

        # Check cache first
        cached_quote = cache.get(cache_key)
        if cached_quote:
            logger.info(f"Quote cache hit for submission {submission.id}")
            return cached_quote

        try:
            # Build context from submission
            context = self._build_context(submission)

            # Determine tone based on outcome and context
            tone = self._determine_tone(submission, context)

            # Generate quote via LM Studio
            quote = self._call_lm_studio(context, tone)

            # Cache the result
            cache.set(cache_key, quote, self.cache_ttl)

            logger.info(f"Generated quote for submission {submission.id}: {quote[:50]}...")
            return quote

        except ExecutionServiceUnavailable as e:
            logger.error(f"LM Studio unavailable for submission {submission.id}: {e}")
            return self._get_fallback_quote(submission)
        except Exception as e:
            logger.error(f"Failed to generate quote for submission {submission.id}: {e}")
            return self._get_fallback_quote(submission)

    def _build_context(self, submission: QuestSubmission) -> Dict[str, Any]:
        """
        Build context object from submission data.

        Returns dict with: quest_title, skill_title, result, tests_passed, tests_total,
        attempt_number, solve_time_seconds, ai_score, user_streak, ability_score, time_of_day
        """
        quest = submission.quest
        skill = quest.skill
        user = submission.user

        # Determine result status
        if submission.status == 'flagged':
            result = 'flagged'
        elif submission.status == 'passed':
            result = 'passed'
        else:
            result = 'failed'

        # Extract test results
        execution_result = submission.execution_result or {}
        tests_passed = execution_result.get('tests_passed', 0)
        tests_total = len(quest.test_cases) if quest.test_cases else 1

        # Calculate attempt number
        attempt_number = self._get_attempt_number(submission)

        # Calculate solve time in seconds
        solve_time_ms = execution_result.get('time_ms', 0)
        solve_time_seconds = solve_time_ms / 1000.0

        # Get AI score if available
        ai_feedback = submission.ai_feedback or {}
        ai_score = ai_feedback.get('score', 0.0)

        # Get user stats
        streak = user.streak_days if hasattr(user, 'streak_days') else 0
        ability_score = 0.5
        if hasattr(user, 'adaptive_profile'):
            ability_score = user.adaptive_profile.ability_score

        # Determine time of day
        time_of_day = self._get_time_of_day(submission.created_at)

        return {
            'quest_title': quest.title,
            'skill_title': skill.title,
            'result': result,
            'tests_passed': tests_passed,
            'tests_total': tests_total,
            'attempt_number': attempt_number,
            'solve_time_seconds': solve_time_seconds,
            'ai_score': ai_score,
            'user_streak': streak,
            'ability_score': ability_score,
            'time_of_day': time_of_day,
        }

    def _determine_tone(self, submission: QuestSubmission, context: Dict[str, Any]) -> str:
        """
        Determine the tone of the quote based on outcome and context.

        Returns: 'celebratory', 'persistent', 'speed', 'encouraging', 'committed', 'diplomatic', or 'streak'
        """
        result = context['result']
        attempt = context['attempt_number']
        solve_time = context['solve_time_seconds']
        streak = context['user_streak']

        # Check for streak milestone (divisible by 7)
        if streak > 0 and streak % 7 == 0:
            return 'streak'

        if result == 'passed':
            # First attempt pass
            if attempt == 1:
                return 'celebratory'

            # Fast solve (top 10% - estimate ~5 seconds for most quests)
            if solve_time < 5.0:
                return 'speed'

            # Multiple attempts (3+)
            if attempt >= 3:
                return 'persistent'

            return 'celebratory'

        elif result == 'failed':
            # Early attempts (1-2)
            if attempt <= 2:
                return 'encouraging'

            # Many attempts (4+)
            if attempt >= 4:
                return 'committed'

            return 'encouraging'

        elif result == 'flagged':
            return 'diplomatic'

        return 'encouraging'

    def _call_lm_studio(self, context: Dict[str, Any], tone: str) -> str:
        """
        Call LM Studio to generate a quote with the given context and tone.

        Args:
            context: Context dictionary with submission data
            tone: Tone type (celebratory, persistent, speed, etc.)

        Returns:
            Generated quote string
        """
        system_prompt = self._build_system_prompt(tone)
        user_prompt = self._build_user_prompt(context, tone)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = self.client.chat_completion(
                messages=messages,
                max_tokens=100,
                temperature=0.7,
            )

            quote = self.client.extract_content(response).strip()

            # Validate quote length
            words = quote.split()
            if len(words) > 30:
                quote = ' '.join(words[:30])

            return quote

        except Exception as e:
            logger.error(f"LM Studio quote generation failed: {e}")
            raise

    def _build_system_prompt(self, tone: str) -> str:
        """Build system prompt for LM Studio based on tone."""
        base_prompt = (
            "You are an inspiring coding mentor. Generate ONE short motivational quote "
            "(max 2 sentences, max 30 words) based on the exact result provided. "
            "Match the emotional tone to the outcome. Never be generic. "
            "Reference the actual quest or skill by name when possible."
        )

        tone_instructions = {
            'celebratory': (
                "Celebrate the win enthusiastically. Praise their achievement and pattern recognition. "
                "Example: 'Two Pointers mastered first try — your pattern recognition is sharp.'"
            ),
            'persistent': (
                "Acknowledge their persistence and breakthrough. Emphasize how multiple attempts lead to mastery. "
                "Example: 'Four attempts. One breakthrough. That's how Dynamic Programming gets learned.'"
            ),
            'speed': (
                "Praise their speed and efficiency. Reference interview-ready performance. "
                "Example: 'Solved Sliding Window in 4 minutes — that's interview speed.'"
            ),
            'encouraging': (
                "Encourage them to retry with specific, constructive feedback. Be supportive and specific. "
                "Example: 'The logic is close — your Binary Search boundary condition needs one more look.'"
            ),
            'committed': (
                "Acknowledge their commitment and suggest using hints or taking a break. Be supportive. "
                "Example: '5 attempts shows real commitment. Try the hint system — sometimes a nudge unlocks everything.'"
            ),
            'diplomatic': (
                "Be diplomatic about AI flagging. Encourage them to explain their approach. "
                "Example: 'Strong solution — but the AI flagged it. Walk us through your approach to confirm it's yours.'"
            ),
            'streak': (
                "Celebrate their streak milestone and consistency. Emphasize the value of consistency. "
                "Example: '7-day streak on Binary Search — consistency is the real skill.'"
            ),
        }

        tone_instruction = tone_instructions.get(tone, tone_instructions['encouraging'])
        return f"{base_prompt}\n\nTone: {tone_instruction}"

    def _build_user_prompt(self, context: Dict[str, Any], tone: str) -> str:
        """Build user prompt with context data for LM Studio."""
        quest_title = context['quest_title']
        skill_title = context['skill_title']
        result = context['result']
        tests_passed = context['tests_passed']
        tests_total = context['tests_total']
        attempt = context['attempt_number']
        solve_time = context['solve_time_seconds']
        ai_score = context['ai_score']
        streak = context['user_streak']
        ability_score = context['ability_score']

        prompt = (
            f"Quest: {quest_title}\n"
            f"Skill: {skill_title}\n"
            f"Result: {result}\n"
            f"Tests Passed: {tests_passed}/{tests_total}\n"
            f"Attempt: #{attempt}\n"
            f"Solve Time: {solve_time:.1f} seconds\n"
            f"AI Score: {ai_score:.2f}\n"
            f"User Streak: {streak} days\n"
            f"Ability Score: {ability_score:.2f}\n"
        )

        if tone == 'streak' and streak > 0:
            prompt += f"\nStreak Milestone: {streak}-day streak on {skill_title}\n"

        prompt += "\nGenerate a motivational quote based on this exact result."

        return prompt

    def _get_attempt_number(self, submission: QuestSubmission) -> int:
        """
        Get the attempt number for this submission.
        Counts all submissions for this user on this quest up to and including this one.
        """
        attempt_count = QuestSubmission.objects.filter(
            user=submission.user,
            quest=submission.quest,
            created_at__lte=submission.created_at,
        ).count()

        return attempt_count

    def _get_time_of_day(self, dt: datetime) -> str:
        """Get time of day category from datetime."""
        hour = dt.hour

        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 21:
            return 'evening'
        else:
            return 'night'

    def _get_cache_key(self, submission_id: int) -> str:
        """Generate Redis cache key for a submission quote."""
        return f"{QUOTE_CACHE_KEY_PREFIX}:{submission_id}"

    def _get_fallback_quote(self, submission: QuestSubmission) -> str:
        """
        Return a fallback quote when LM Studio is unavailable.
        Based on submission result and attempt number.
        """
        attempt = self._get_attempt_number(submission)
        quest_title = submission.quest.title

        fallback_quotes = {
            'passed_first': f"✓ {quest_title} mastered on first try. Sharp work.",
            'passed_multiple': f"✓ {quest_title} conquered. Persistence pays off.",
            'failed_early': f"Close on {quest_title}. You've got this — try again.",
            'failed_late': f"Strong effort on {quest_title}. Consider the hint system.",
            'flagged': f"Strong solution on {quest_title}. Let's verify your approach.",
        }

        if submission.status == 'passed':
            if attempt == 1:
                return fallback_quotes['passed_first']
            else:
                return fallback_quotes['passed_multiple']
        elif submission.status == 'flagged':
            return fallback_quotes['flagged']
        else:
            if attempt <= 2:
                return fallback_quotes['failed_early']
            else:
                return fallback_quotes['failed_late']

    def is_available(self) -> bool:
        """Check if LM Studio is available for quote generation."""
        return self.client.is_available()


# Singleton instance
quote_generator = QuoteGenerator()
