"""
SkillTree AI - Admin Quest Generator
AI-powered quest generation for admin panel using LM Studio.
Supports single and batch generation with editable preview and ContentValidator integration.
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional
from django.conf import settings
from django.core.cache import cache
from core.lm_client import lm_client, ExecutionServiceUnavailable
from quests.models import Quest
from skills.models import Skill

logger = logging.getLogger(__name__)

QUEST_GENERATION_TIMEOUT = 60
QUEST_CACHE_TTL = 3600


class AdminQuestGenerator:
    """
    Generates complete coding quests using LM Studio.
    Supports single and batch generation with validation.
    """

    def __init__(self):
        """Initialize quest generator with LM Studio client."""
        self.client = lm_client
        self.cache_ttl = QUEST_CACHE_TTL

    def generate_quest(
        self,
        skill_id: int,
        topic_hint: str,
        difficulty: int,
        quest_type: str
    ) -> Dict[str, Any]:
        """
        Generate a single quest draft using LM Studio.

        Args:
            skill_id: ID of the skill this quest is for
            topic_hint: Topic hint for quest generation
            difficulty: Difficulty level (1-5)
            quest_type: Type of quest (coding, debugging, mcq)

        Returns:
            Dictionary with quest data matching Quest schema:
            {
                'title': str,
                'description': str,
                'starter_code': str,
                'test_cases': List[Dict],
                'xp_reward': int,
                'estimated_minutes': int,
                'difficulty_multiplier': float,
                'ai_generated': bool,
                'validation_notes': str
            }

        Raises:
            ExecutionServiceUnavailable: If LM Studio is unavailable
            ValueError: If skill not found or invalid parameters
        """
        try:
            skill = Skill.objects.get(id=skill_id)
        except Skill.DoesNotExist:
            raise ValueError(f"Skill with ID {skill_id} not found")

        if not 1 <= difficulty <= 5:
            raise ValueError("Difficulty must be between 1 and 5")

        if quest_type not in ['coding', 'debugging', 'mcq']:
            raise ValueError(f"Invalid quest_type: {quest_type}")

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(skill, topic_hint, difficulty, quest_type)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = self.client.chat_completion(
                messages=messages,
                max_tokens=2000,
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            content = self.client.extract_content(response)
            quest_data = json.loads(content)

            quest_data['ai_generated'] = True
            quest_data['validation_notes'] = ''

            self._validate_quest_data(quest_data)

            logger.info(f"Generated quest for skill {skill.title}: {quest_data['title']}")
            return quest_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LM Studio JSON response: {e}")
            raise ExecutionServiceUnavailable(f"Invalid JSON from LM Studio: {e}")
        except Exception as e:
            logger.error(f"Quest generation failed: {e}")
            raise

    async def generate_batch_quests(
        self,
        skill_id: int,
        topic_hint: str,
        difficulty: int,
        quest_type: str,
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple quests in parallel using asyncio.gather.

        Args:
            skill_id: ID of the skill
            topic_hint: Topic hint for generation
            difficulty: Difficulty level (1-5)
            quest_type: Type of quest
            count: Number of quests to generate (default 5)

        Returns:
            List of quest dictionaries

        Raises:
            ExecutionServiceUnavailable: If LM Studio is unavailable
            ValueError: If parameters are invalid
        """
        if count < 1 or count > 10:
            raise ValueError("Batch count must be between 1 and 10")

        tasks = [
            self._generate_quest_async(skill_id, topic_hint, difficulty, quest_type)
            for _ in range(count)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        quests = []
        errors = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch quest {i+1} generation failed: {result}")
                errors.append(str(result))
            else:
                quests.append(result)

        if errors:
            logger.warning(f"Batch generation completed with {len(errors)} errors: {errors}")

        return quests

    async def _generate_quest_async(
        self,
        skill_id: int,
        topic_hint: str,
        difficulty: int,
        quest_type: str
    ) -> Dict[str, Any]:
        """
        Async wrapper for quest generation.
        Runs in thread pool to avoid blocking.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.generate_quest,
            skill_id,
            topic_hint,
            difficulty,
            quest_type
        )

    def save_quest_draft(
        self,
        skill_id: int,
        quest_data: Dict[str, Any]
    ) -> Quest:
        """
        Save generated quest data as a draft Quest object.

        Args:
            skill_id: ID of the skill
            quest_data: Quest data from generate_quest

        Returns:
            Created Quest object with status draft
        """
        try:
            skill = Skill.objects.get(id=skill_id)
        except Skill.DoesNotExist:
            raise ValueError(f"Skill with ID {skill_id} not found")

        quest = Quest.objects.create(
            skill=skill,
            type=quest_data.get('type', 'coding'),
            title=quest_data['title'],
            description=quest_data['description'],
            starter_code=quest_data.get('starter_code', ''),
            test_cases=quest_data.get('test_cases', []),
            xp_reward=quest_data.get('xp_reward', 100),
            estimated_minutes=quest_data.get('estimated_minutes', 15),
            difficulty_multiplier=quest_data.get('difficulty_multiplier', 1.0),
        )

        logger.info(f"Saved quest draft: {quest.title} (ID: {quest.id})")
        return quest

    def _build_system_prompt(self) -> str:
        """Build system prompt for LM Studio."""
        return (
            "You are an expert computer science educator. "
            "Generate a complete, original coding quest for a developer learning platform. "
            "The quest should be engaging, educational, and have clear success criteria. "
            "Respond ONLY in valid JSON matching the specified schema. "
            "Do not include any text outside the JSON object."
        )

    def _build_user_prompt(
        self,
        skill: Skill,
        topic_hint: str,
        difficulty: int,
        quest_type: str
    ) -> str:
        """Build user prompt with quest requirements."""
        difficulty_description = {
            1: "Beginner - Basic concepts, simple implementation",
            2: "Intermediate - Some complexity, requires understanding",
            3: "Advanced - Significant complexity, multiple concepts",
            4: "Expert - Complex problem, requires deep knowledge",
            5: "Master - Very complex, requires mastery and optimization"
        }

        xp_range = {
            1: "100-150",
            2: "150-250",
            3: "250-350",
            4: "350-450",
            5: "450-500"
        }

        prompt = f"""Generate a complete coding quest with the following requirements:

Skill: {skill.title}
Topic Hint: {topic_hint}
Difficulty: {difficulty}/5 - {difficulty_description[difficulty]}
Quest Type: {quest_type}

The quest MUST include:
1. Engaging title (5-10 words, no generic names)
2. Clear problem statement (3-5 sentences with a concrete example)
3. Starter code with TODO comments (Python, ready to run)
4. Exactly 5 test cases with real input/output pairs
5. XP reward ({xp_range[difficulty]} based on difficulty)
6. One-line hint for each test case
7. Estimated time to complete (in minutes)

Respond ONLY with this JSON structure (no markdown, no extra text):
{{
    "title": "Quest Title",
    "description": "Full problem statement with example",
    "starter_code": "Python code with TODO",
    "test_cases": [
        {{"input": "...", "expected_output": "...", "hint": "One-line hint"}},
        ...
    ],
    "xp_reward": {xp_range[difficulty].split('-')[0]},
    "estimated_minutes": 15,
    "difficulty_multiplier": {difficulty / 5.0},
    "type": "{quest_type}"
}}"""

        return prompt

    def _validate_quest_data(self, quest_data: Dict[str, Any]) -> None:
        """
        Validate generated quest data.

        Raises:
            ValueError: If required fields are missing or invalid
        """
        required_fields = ['title', 'description', 'starter_code', 'test_cases', 'xp_reward']

        for field in required_fields:
            if field not in quest_data:
                raise ValueError(f"Missing required field: {field}")

        if not isinstance(quest_data['title'], str) or len(quest_data['title']) < 5:
            raise ValueError("Title must be a non-empty string (min 5 chars)")

        if not isinstance(quest_data['description'], str) or len(quest_data['description']) < 20:
            raise ValueError("Description must be a non-empty string (min 20 chars)")

        if not isinstance(quest_data['test_cases'], list) or len(quest_data['test_cases']) != 5:
            raise ValueError("Must have exactly 5 test cases")

        for i, test_case in enumerate(quest_data['test_cases']):
            if not isinstance(test_case, dict):
                raise ValueError(f"Test case {i} must be a dictionary")
            if 'input' not in test_case or 'expected_output' not in test_case:
                raise ValueError(f"Test case {i} missing input or expected_output")

        if not isinstance(quest_data['xp_reward'], int) or not 100 <= quest_data['xp_reward'] <= 500:
            raise ValueError("XP reward must be between 100 and 500")

        if 'estimated_minutes' in quest_data:
            if not isinstance(quest_data['estimated_minutes'], int) or quest_data['estimated_minutes'] < 5:
                raise ValueError("Estimated minutes must be at least 5")

    def is_available(self) -> bool:
        """Check if LM Studio is available for quest generation."""
        return self.client.is_available()


quest_generator = AdminQuestGenerator()
