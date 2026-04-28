"""
SkillTree AI - Hint Engine
Tiered hint system with LM Studio integration.
Generates conceptual nudges, approach explanations, and skeleton code.
"""

import logging
from typing import Dict, Any, Optional
from django.conf import settings
from django.utils import timezone

from core.lm_client import lm_client, ExecutionServiceUnavailable
from mentor.models import HintUsage, AIInteraction
from quests.models import Quest, QuestSubmission
from users.models import User

logger = logging.getLogger(__name__)


class HintEngine:
    """
    Generates tiered hints for coding quests using LM Studio.
    Manages XP penalties and rate limiting.
    """

    # XP penalties per hint level
    XP_PENALTIES = {
        1: 0,      # Nudge: no penalty
        2: 10,     # Approach: -10 XP from reward
        3: 25,     # Near-Solution: -25 XP from reward
    }

    # Hint level names
    HINT_NAMES = {
        1: 'Nudge',
        2: 'Approach',
        3: 'Near-Solution',
    }

    def get_hint(
        self,
        user: User,
        quest: Quest,
        hint_level: int,
        current_code: str
    ) -> Dict[str, Any]:
        """
        Generate a tiered hint for a quest.

        Args:
            user: User requesting the hint
            quest: Quest to get hint for
            hint_level: 1 (Nudge), 2 (Approach), or 3 (Near-Solution)
            current_code: User's current code attempt

        Returns:
            Dict with keys:
            - hint_text: Generated hint
            - xp_penalty: XP penalty for this hint level
            - hints_used_today: Count of hints used today for this quest
            - hint_level_name: Name of hint level

        Raises:
            ValueError: If hint_level is invalid or rate limit exceeded
            ExecutionServiceUnavailable: If LM Studio is unavailable
        """
        # Validate hint level
        if hint_level not in [1, 2, 3]:
            raise ValueError(f"Invalid hint level: {hint_level}. Must be 1, 2, or 3.")

        # Check rate limit
        if not HintUsage.can_request_hint(user, quest):
            raise ValueError("Rate limit exceeded: max 5 hints per quest per day.")

        # Get attempt count
        attempt_count = QuestSubmission.objects.filter(
            user=user,
            quest=quest,
            status__in=['failed', 'pending']
        ).count()

        # Get skill and difficulty
        skill = quest.skill
        difficulty = int(quest.difficulty_multiplier * 5)

        # Generate hint using LM Studio
        hint_text = self._generate_hint_with_lm(
            quest=quest,
            skill=skill,
            difficulty=difficulty,
            hint_level=hint_level,
            current_code=current_code,
            attempt_count=attempt_count
        )

        # Calculate XP penalty
        xp_penalty = self.XP_PENALTIES[hint_level]

        # Save hint usage
        hint_usage = HintUsage.objects.create(
            user=user,
            quest=quest,
            hint_level=hint_level,
            hint_text=hint_text,
            xp_penalty=xp_penalty
        )

        # Log AI interaction
        AIInteraction.objects.create(
            user=user,
            interaction_type='hint',
            context_prompt=self._build_prompt(
                quest, skill, difficulty, hint_level, current_code, attempt_count
            ),
            response=hint_text,
            tokens_used=0
        )

        # Get hints used today
        hints_used_today = HintUsage.get_hints_used_today(user, quest)

        return {
            'hint_text': hint_text,
            'xp_penalty': xp_penalty,
            'hints_used_today': hints_used_today,
            'hint_level_name': self.HINT_NAMES[hint_level],
        }

    def _build_prompt(
        self,
        quest: Quest,
        skill,
        difficulty: int,
        hint_level: int,
        current_code: str,
        attempt_count: int
    ) -> str:
        """Build the prompt for LM Studio based on hint level."""
        code_preview = current_code[:500] if current_code else "[No code submitted yet]"

        base_prompt = (
            f"You are a coding mentor. The student is solving '{quest.title}' "
            f"(skill: {skill.title}, difficulty: {difficulty}/5). "
            f"Their current code: {code_preview}. "
            f"They have failed {attempt_count} times."
        )

        if hint_level == 1:
            return (
                f"{base_prompt} "
                f"Generate a Level 1 (Nudge) hint - a conceptual nudge only (1 sentence). "
                f"Provide algorithmic direction without any code. "
                f"Example: 'Think about what data structure gives O(1) lookup.'"
            )
        elif hint_level == 2:
            return (
                f"{base_prompt} "
                f"Generate a Level 2 (Approach) hint - explain the correct approach in 3 sentences. "
                f"Use pseudocode-level explanation but NO actual code. "
                f"Focus on the algorithm and data structures needed."
            )
        else:  # hint_level == 3
            return (
                f"{base_prompt} "
                f"Generate a Level 3 (Near-Solution) hint - provide working skeleton code. "
                f"Include the overall structure and key logic replaced by TODO comments. "
                f"The student should be able to fill in the TODOs to complete the solution. "
                f"Never reveal the full solution."
            )

    def _generate_hint_with_lm(
        self,
        quest: Quest,
        skill,
        difficulty: int,
        hint_level: int,
        current_code: str,
        attempt_count: int
    ) -> str:
        """Generate hint using LM Studio."""
        try:
            prompt = self._build_prompt(
                quest, skill, difficulty, hint_level, current_code, attempt_count
            )

            messages = [
                {
                    "role": "system",
                    "content": "You are an expert coding mentor who provides helpful hints at different levels of detail."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            # Adjust max_tokens based on hint level
            max_tokens = 150 if hint_level == 1 else (300 if hint_level == 2 else 500)

            response = lm_client.chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.3  # Lower temperature for consistency
            )

            hint_text = lm_client.extract_content(response)
            return hint_text.strip()

        except ExecutionServiceUnavailable as e:
            logger.error(f"LM Studio unavailable for hint generation: {e}")
            return self._get_fallback_hint(hint_level, quest)
        except Exception as e:
            logger.error(f"Error generating hint: {e}")
            return self._get_fallback_hint(hint_level, quest)

    def _get_fallback_hint(self, hint_level: int, quest: Quest) -> str:
        """Return fallback hint if LM Studio is unavailable."""
        if hint_level == 1:
            return (
                "Think about the problem requirements. What data structures or algorithms "
                "might be most efficient for this task?"
            )
        elif hint_level == 2:
            return (
                "Break down the problem into steps: 1) Parse the input, 2) Process the data, "
                "3) Format and return the output. Consider what data structures would help."
            )
        else:
            return (
                f"Here's a skeleton for {quest.title}:\n\n"
                "def solve(input_data):\n"
                "    # TODO: Parse input\n"
                "    # TODO: Implement main logic\n"
                "    # TODO: Return result\n"
                "    pass"
            )

    def get_hint_unlock_status(self, user: User, quest: Quest) -> Dict[str, bool]:
        """
        Get which hint levels are unlocked for a user on a quest.
        L2 unlocks after L1 is used, L3 unlocks after L2 is used.

        Returns:
            Dict with keys 'level_1', 'level_2', 'level_3' (all True if available)
        """
        hints_used = HintUsage.get_hints_used_for_quest(user, quest)
        hint_levels_used = set(h.hint_level for h in hints_used)

        return {
            'level_1': True,  # Always available
            'level_2': 1 in hint_levels_used,  # Available after L1 used
            'level_3': 2 in hint_levels_used,  # Available after L2 used
        }

    def get_xp_penalty_for_level(self, hint_level: int) -> int:
        """Get XP penalty for a hint level."""
        return self.XP_PENALTIES.get(hint_level, 0)


# Singleton instance
hint_engine = HintEngine()
