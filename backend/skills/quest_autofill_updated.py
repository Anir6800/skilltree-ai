"""
Quest Auto-Fill Service - UPDATED
Fills stub quests with AI-generated content using reliable stub detection.
"""

import json
import logging
from typing import Dict, List
from django.db import transaction
from django.conf import settings
from celery import shared_task
from core.lm_client import lm_client, ExecutionServiceUnavailable
from quests.models import Quest
from skills.models import GeneratedSkillTree

logger = logging.getLogger(__name__)


class QuestAutoFillService:
    """
    Fills stub quests with AI-generated content.
    Uses explicit is_stub flag for reliable detection.
    """
    
    def __init__(self):
        self.lm = lm_client
        self.max_retries = getattr(settings, 'LM_STUDIO_MAX_RETRIES', 2)
    
    def execute_autofill(self, tree_id: str) -> Dict:
        """
        Main auto-fill pipeline.
        
        Args:
            tree_id: UUID of GeneratedSkillTree
            
        Returns:
            Auto-fill result with status and quest count
        """
        logger.info(f"[AUTOFILL] Starting quest auto-fill for tree {tree_id}")
        
        try:
            tree = GeneratedSkillTree.objects.get(id=tree_id)
            
            # Step 1: Find stub quests using NEW is_stub flag
            logger.info(f"[AUTOFILL] Finding stub quests")
            stub_quests = self._find_stub_quests(tree)
            logger.info(f"[AUTOFILL] Found {len(stub_quests)} stub quests")
            
            if not stub_quests:
                logger.info(f"[AUTOFILL] No stub quests to fill")
                return {
                    'status': 'success',
                    'tree_id': str(tree_id),
                    'quests_filled': 0,
                }
            
            # Step 2: Fill each stub quest
            filled_count = 0
            for quest in stub_quests:
                try:
                    logger.info(f"[AUTOFILL] Filling quest: {quest.title}")
                    self._fill_quest(quest)
                    filled_count += 1
                except Exception as e:
                    logger.warning(f"[AUTOFILL] Failed to fill quest {quest.id}: {str(e)}")
                    continue
            
            logger.info(f"[AUTOFILL] Auto-fill complete: {filled_count}/{len(stub_quests)} quests filled")
            
            return {
                'status': 'success',
                'tree_id': str(tree_id),
                'quests_filled': filled_count,
                'total_stubs': len(stub_quests),
            }
            
        except Exception as e:
            logger.error(f"[AUTOFILL] Auto-fill failed: {str(e)}", exc_info=True)
            raise
    
    def _find_stub_quests(self, tree: GeneratedSkillTree) -> List[Quest]:
        """
        Find stub quests using NEW is_stub flag.
        
        Args:
            tree: GeneratedSkillTree instance
            
        Returns:
            List of stub quests
        """
        # NEW: Use explicit is_stub flag instead of test_cases length
        stub_quests = Quest.objects.filter(
            skill__in=tree.skills_created.all(),
            is_stub=True  # NEW: Reliable flag
        ).select_related('skill')
        
        logger.debug(f"[AUTOFILL] Found {stub_quests.count()} stub quests using is_stub flag")
        return list(stub_quests)
    
    @transaction.atomic
    def _fill_quest(self, quest: Quest):
        """
        Fill a single stub quest with AI-generated content.
        
        Args:
            quest: Quest to fill
        """
        logger.info(f"[AUTOFILL] Generating content for: {quest.title}")
        
        # Step 1: Generate quest content
        content = self._generate_quest_content(quest)
        
        # Step 2: Validate content
        self._validate_quest_content(content, quest.type)
        
        # Step 3: Update quest
        quest.description = content['description']
        quest.starter_code = content.get('starter_code', '')
        quest.test_cases = content['test_cases']
        quest.xp_reward = content.get('xp_reward', 50 * quest.skill.difficulty)
        quest.difficulty_multiplier = content.get('difficulty_multiplier', 1.0)
        quest.is_stub = False  # NEW: Mark as filled
        quest.save()
        
        logger.info(f"[AUTOFILL] Quest filled: {quest.title}")
    
    def _generate_quest_content(self, quest: Quest) -> Dict:
        """
        Generate quest content using LM Studio.
        
        Args:
            quest: Quest to generate content for
            
        Returns:
            Generated content dictionary
        """
        prompt = self._build_generation_prompt(quest)
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert coding instructor. Generate high-quality programming challenges that are clear, engaging, and educational."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            response = self.lm.chat_completion(
                messages=messages,
                max_tokens=2000,
                temperature=0.3,
            )
            
            response_text = self.lm.extract_content(response)
            logger.debug(f"[AUTOFILL] LM Studio response: {response_text[:200]}...")
            
            # Parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in LM Studio response")
            
            return json.loads(json_match.group())
            
        except ExecutionServiceUnavailable as e:
            logger.error(f"[AUTOFILL] LM Studio unavailable: {str(e)}")
            raise
    
    def _build_generation_prompt(self, quest: Quest) -> str:
        """
        Build prompt for quest content generation.
        
        Args:
            quest: Quest to generate content for
            
        Returns:
            Generation prompt
        """
        skill = quest.skill
        
        if quest.type == 'coding':
            return f"""Generate a coding challenge for the skill: "{skill.title}"

Skill Description: {skill.description}
Difficulty Level: {skill.difficulty}/5

Requirements:
- Create a clear problem statement
- Provide starter code (if applicable)
- Define 3-5 test cases with inputs and expected outputs
- Ensure the challenge is solvable in 15-30 minutes
- Make it educational and engaging

Return ONLY valid JSON with this structure:
{{
  "description": "Clear problem statement with examples",
  "starter_code": "// Starter code here",
  "test_cases": [
    {{"input": "...", "expected_output": "..."}},
    ...
  ],
  "xp_reward": 100,
  "difficulty_multiplier": 1.5
}}"""
        
        elif quest.type == 'debugging':
            return f"""Generate a debugging challenge for the skill: "{skill.title}"

Skill Description: {skill.description}
Difficulty Level: {skill.difficulty}/5

Requirements:
- Provide buggy code with 2-3 intentional bugs
- Create a clear problem description
- Define 3-5 test cases to verify the fix
- Bugs should be educational (common mistakes)
- Challenge should take 15-30 minutes to debug

Return ONLY valid JSON with this structure:
{{
  "description": "Problem description and debugging task",
  "starter_code": "// Buggy code here",
  "test_cases": [
    {{"input": "...", "expected_output": "..."}},
    ...
  ],
  "xp_reward": 120,
  "difficulty_multiplier": 1.5
}}"""
        
        else:  # mcq
            return f"""Generate a multiple-choice question for the skill: "{skill.title}"

Skill Description: {skill.description}
Difficulty Level: {skill.difficulty}/5

Requirements:
- Create a clear question about the skill
- Provide 4 options (A, B, C, D)
- Exactly one correct answer
- Distractors should be plausible but incorrect
- Question should test understanding, not memorization

Return ONLY valid JSON with this structure:
{{
  "description": "Question text",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "correct_answer": 0,
  "explanation": "Why this is correct",
  "xp_reward": 50,
  "difficulty_multiplier": 1.0
}}"""
    
    def _validate_quest_content(self, content: Dict, quest_type: str):
        """
        Validate generated quest content.
        
        Args:
            content: Generated content
            quest_type: Type of quest (coding/debugging/mcq)
            
        Raises:
            ValueError: If content is invalid
        """
        if not isinstance(content, dict):
            raise ValueError("Content must be a dictionary")
        
        if 'description' not in content or not content['description']:
            raise ValueError("Content must have 'description'")
        
        if quest_type in ['coding', 'debugging']:
            if 'test_cases' not in content or not isinstance(content['test_cases'], list):
                raise ValueError("Coding quests must have 'test_cases' array")
            
            if len(content['test_cases']) < 3:
                raise ValueError("Must have at least 3 test cases")
            
            for tc in content['test_cases']:
                if 'input' not in tc or 'expected_output' not in tc:
                    raise ValueError("Each test case must have 'input' and 'expected_output'")
        
        elif quest_type == 'mcq':
            if 'options' not in content or len(content['options']) != 4:
                raise ValueError("MCQ must have exactly 4 options")
            
            if 'correct_answer' not in content or not (0 <= content['correct_answer'] < 4):
                raise ValueError("MCQ must have valid 'correct_answer' (0-3)")
        
        # Validate XP reward
        xp_reward = content.get('xp_reward', 50)
        if not (50 <= xp_reward <= 500):
            raise ValueError(f"XP reward must be 50-500, got {xp_reward}")
        
        # Validate difficulty multiplier
        difficulty_multiplier = content.get('difficulty_multiplier', 1.0)
        if not (1.0 <= difficulty_multiplier <= 3.0):
            raise ValueError(f"Difficulty multiplier must be 1.0-3.0, got {difficulty_multiplier}")
        
        logger.debug(f"[AUTOFILL] Content validation passed")


@shared_task(name='skills.tasks.autofill_quests_task', bind=True, max_retries=2)
def autofill_quests_task(self, tree_id: str):
    """
    Celery task for async quest auto-fill.
    
    Args:
        tree_id: UUID of GeneratedSkillTree
    """
    try:
        service = QuestAutoFillService()
        result = service.execute_autofill(tree_id)
        logger.info(f"[TASK] Quest auto-fill task complete: {result}")
        return result
    except Exception as exc:
        logger.error(f"[TASK] Quest auto-fill task failed: {str(exc)}", exc_info=True)
        raise self.retry(exc=exc, countdown=10)
