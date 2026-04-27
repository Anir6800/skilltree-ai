"""
SkillTree AI - Quest AutoFill Service
Generates complete quest content for stub quests using LM Studio.
Handles per-quest generation, validation, and WebSocket progress streaming.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from django.db import transaction
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from core.lm_client import lm_client, ExecutionServiceUnavailable
from quests.models import Quest
from skills.models import GeneratedSkillTree, Skill

logger = logging.getLogger(__name__)


class QuestAutoFillService:
    """
    Service for auto-filling stub quests with complete content.
    Generates quest descriptions, test cases, and metadata via LM Studio.
    Broadcasts per-quest progress via WebSocket.
    """
    
    MAX_RETRIES = 2
    SYSTEM_PROMPT = (
        "You are an expert curriculum designer. Generate complete, pedagogically sound "
        "coding and assessment quests. Respond ONLY with valid JSON."
    )
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def autofill_quests_for_tree(self, tree_id: str) -> Dict[str, Any]:
        """
        Auto-fill all stub quests for a generated skill tree.
        Dispatches async Celery task for background processing.
        
        Args:
            tree_id: GeneratedSkillTree ID
            
        Returns:
            Dictionary with quests_to_fill count and status
        """
        try:
            tree = GeneratedSkillTree.objects.get(id=tree_id)
        except GeneratedSkillTree.DoesNotExist:
            raise ValueError(f"GeneratedSkillTree {tree_id} not found")
        
        if tree.status != "ready":
            raise ValueError(f"Tree must be in 'ready' status, current status: {tree.status}")
        
        # Count stub quests
        stub_quests = Quest.objects.filter(
            skill__generated_from_trees=tree,
            description__exact="Complete this quest to master " + ""  # Placeholder check
        )
        
        # More reliable: check if test_cases is empty or minimal
        stub_quests = Quest.objects.filter(
            skill__generated_from_trees=tree
        ).exclude(
            test_cases__len__gt=0  # Exclude quests with non-empty test_cases
        )
        
        quests_to_fill = stub_quests.count()
        
        if quests_to_fill == 0:
            logger.info(f"No stub quests found for tree {tree_id}")
            return {
                "tree_id": tree_id,
                "quests_to_fill": 0,
                "status": "no_quests",
            }
        
        logger.info(f"Found {quests_to_fill} stub quests for tree {tree_id}")
        
        # Dispatch async Celery task
        from skills.tasks import autofill_quests_task
        autofill_quests_task.delay(tree_id)
        
        return {
            "tree_id": tree_id,
            "quests_to_fill": quests_to_fill,
            "status": "filling",
        }
    
    def _build_quest_prompt(
        self,
        skill_title: str,
        quest_title: str,
        difficulty: int,
    ) -> str:
        """
        Build the user prompt for LM Studio quest generation.
        
        Args:
            skill_title: Title of the skill
            quest_title: Title of the quest
            difficulty: Difficulty level (1-5)
            
        Returns:
            Formatted user prompt
        """
        json_format = """{
  "description": "3-sentence problem statement",
  "type": "coding|mcq|open_ended",
  "starter_code": "code with TODO comment or null",
  "test_cases": [{"input":"...","expected_output":"...","description":"..."}],
  "mcq_options": ["A","B","C","D"] or null,
  "correct_answer": "answer or null",
  "xp_reward": 50-500,
  "difficulty_multiplier": 1.0-3.0
}"""
        
        return (
            f"Generate a complete coding/theory quest for the skill '{skill_title}' "
            f"titled '{quest_title}'. The learner's level is {difficulty}/5. "
            f"Respond ONLY in JSON: {json_format}"
        )
    
    def _call_lm_studio_for_quest(
        self,
        skill_title: str,
        quest_title: str,
        difficulty: int,
    ) -> Dict[str, Any]:
        """
        Call LM Studio to generate quest content.
        Retries up to MAX_RETRIES times with simplified prompt on failure.
        
        Args:
            skill_title: Title of the skill
            quest_title: Title of the quest
            difficulty: Difficulty level (1-5)
            
        Returns:
            Parsed JSON response with quest content
            
        Raises:
            ExecutionServiceUnavailable: If LM Studio is unavailable
            ValueError: If response cannot be parsed after retries
        """
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": self._build_quest_prompt(skill_title, quest_title, difficulty)},
        ]
        
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                logger.info(
                    f"LM Studio call attempt {attempt + 1}/{self.MAX_RETRIES + 1} "
                    f"for quest '{quest_title}' (skill: {skill_title})"
                )
                
                response = lm_client.chat_completion(
                    messages=messages,
                    max_tokens=1500,
                    temperature=0.1,
                )
                
                content = lm_client.extract_content(response)
                parsed = self._extract_json(content)
                
                if not parsed:
                    raise ValueError("Failed to parse JSON response")
                
                # Validate required fields
                required_fields = ["description", "type", "xp_reward", "difficulty_multiplier"]
                missing_fields = [f for f in required_fields if f not in parsed]
                
                if missing_fields:
                    raise ValueError(f"Missing required fields: {missing_fields}")
                
                logger.info(f"Successfully generated quest content for '{quest_title}'")
                return parsed
                
            except (ExecutionServiceUnavailable, ValueError, json.JSONDecodeError) as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.MAX_RETRIES:
                    # Simplify prompt for retry
                    messages[1]["content"] = (
                        f"Generate a simple {difficulty}-level quest for {skill_title}: {quest_title}. "
                        f"Return ONLY JSON: {{'description':'...','type':'coding','xp_reward':100,'difficulty_multiplier':1.0}}"
                    )
                else:
                    raise ValueError(
                        f"Failed to generate quest after {self.MAX_RETRIES + 1} attempts: {str(e)}"
                    )
    
    def _extract_json(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from LM Studio response.
        Handles markdown code blocks and partial JSON.
        
        Args:
            content: Raw response content
            
        Returns:
            Parsed JSON dictionary or None
        """
        # Remove markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        content = content.strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON: {content[:200]}")
            return None
    
    def _validate_quest_data(self, quest_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate quest data from LM Studio response.
        
        Args:
            quest_data: Quest data dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate type
        valid_types = ["coding", "mcq", "open_ended", "debugging"]
        if quest_data.get("type") not in valid_types:
            return False, f"Invalid quest type: {quest_data.get('type')}"
        
        # Validate xp_reward
        xp_reward = quest_data.get("xp_reward", 0)
        if not isinstance(xp_reward, (int, float)) or xp_reward < 50 or xp_reward > 500:
            return False, f"XP reward must be between 50-500, got {xp_reward}"
        
        # Validate difficulty_multiplier
        diff_mult = quest_data.get("difficulty_multiplier", 1.0)
        if not isinstance(diff_mult, (int, float)) or diff_mult < 1.0 or diff_mult > 3.0:
            return False, f"Difficulty multiplier must be between 1.0-3.0, got {diff_mult}"
        
        # Validate description
        description = quest_data.get("description", "").strip()
        if not description or len(description) < 10:
            return False, "Description too short or missing"
        
        # Validate test_cases for coding quests
        if quest_data.get("type") == "coding":
            test_cases = quest_data.get("test_cases", [])
            if not isinstance(test_cases, list) or len(test_cases) < 3:
                return False, "Coding quests must have at least 3 test cases"
            
            for i, tc in enumerate(test_cases):
                if not isinstance(tc, dict) or "input" not in tc or "expected_output" not in tc:
                    return False, f"Test case {i} missing input or expected_output"
        
        # Validate MCQ options
        if quest_data.get("type") == "mcq":
            options = quest_data.get("mcq_options", [])
            if not isinstance(options, list) or len(options) != 4:
                return False, "MCQ must have exactly 4 options"
            
            correct_answer = quest_data.get("correct_answer")
            if not correct_answer or correct_answer not in options:
                return False, "Correct answer must be one of the options"
        
        return True, None
    
    @transaction.atomic
    def _fill_quest(
        self,
        quest: Quest,
        tree_id: str,
        user_id: int,
    ) -> Tuple[bool, Optional[str]]:
        """
        Fill a single quest with generated content.
        
        Args:
            quest: Quest object to fill
            tree_id: GeneratedSkillTree ID (for WebSocket broadcast)
            user_id: User ID (for WebSocket group)
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            skill = quest.skill
            
            # Generate quest content via LM Studio
            try:
                quest_data = self._call_lm_studio_for_quest(
                    skill.title,
                    quest.title,
                    skill.difficulty,
                )
            except (ExecutionServiceUnavailable, ValueError) as e:
                error_msg = f"LM Studio generation failed: {str(e)}"
                logger.error(f"Quest {quest.id}: {error_msg}")
                return False, error_msg
            
            # Validate generated data
            is_valid, validation_error = self._validate_quest_data(quest_data)
            if not is_valid:
                error_msg = f"Validation failed: {validation_error}"
                logger.error(f"Quest {quest.id}: {error_msg}")
                return False, error_msg
            
            # Update quest with generated content
            quest.description = quest_data.get("description", "")
            quest.type = quest_data.get("type", "coding")
            quest.starter_code = quest_data.get("starter_code", "")
            quest.test_cases = quest_data.get("test_cases", [])
            quest.xp_reward = int(quest_data.get("xp_reward", 100))
            quest.difficulty_multiplier = float(quest_data.get("difficulty_multiplier", 1.0))
            
            # Store MCQ options if applicable
            if quest.type == "mcq":
                quest.test_cases = {
                    "mcq_options": quest_data.get("mcq_options", []),
                    "correct_answer": quest_data.get("correct_answer", ""),
                }
            
            quest.save()
            
            logger.info(f"Successfully filled quest {quest.id}: {quest.title}")
            
            # Broadcast progress via WebSocket
            self._broadcast_quest_filled(tree_id, user_id, quest)
            
            return True, None
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Quest {quest.id}: {error_msg}", exc_info=True)
            return False, error_msg
    
    def _broadcast_quest_filled(
        self,
        tree_id: str,
        user_id: int,
        quest: Quest,
    ) -> None:
        """
        Broadcast quest filled event via WebSocket.
        
        Args:
            tree_id: GeneratedSkillTree ID
            user_id: User ID
            quest: Filled Quest object
        """
        try:
            group_name = f"quest_autofill_{tree_id}"
            message = {
                "type": "quest_filled",
                "quest_id": quest.id,
                "quest_title": quest.title,
                "skill_title": quest.skill.title,
                "timestamp": timezone.now().isoformat(),
            }
            
            async_to_sync(self.channel_layer.group_send)(
                group_name,
                {
                    "type": "quest_filled",
                    "quest_id": quest.id,
                    "quest_title": quest.title,
                    "skill_title": quest.skill.title,
                    "timestamp": message["timestamp"],
                }
            )
            
            logger.info(f"Broadcasted quest filled: {quest.id}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast quest filled event: {str(e)}")
    
    def execute_autofill(self, tree_id: str) -> Dict[str, Any]:
        """
        Execute the full quest auto-fill pipeline.
        Called by Celery task.
        
        Args:
            tree_id: GeneratedSkillTree ID
            
        Returns:
            Result dictionary with status and details
        """
        try:
            tree = GeneratedSkillTree.objects.get(id=tree_id)
            user_id = tree.created_by.id
            
            logger.info(f"Starting quest auto-fill for tree {tree_id}")
            
            # Get all stub quests for this tree
            stub_quests = Quest.objects.filter(
                skill__generated_from_trees=tree
            ).exclude(
                test_cases__len__gt=0
            )
            
            total_quests = stub_quests.count()
            
            if total_quests == 0:
                logger.info(f"No stub quests found for tree {tree_id}")
                return {
                    "status": "completed",
                    "tree_id": tree_id,
                    "quests_filled": 0,
                    "total_quests": 0,
                    "errors": [],
                }
            
            logger.info(f"Found {total_quests} stub quests to fill")
            
            filled_count = 0
            errors = []
            
            # Fill each quest
            for quest in stub_quests:
                success, error_msg = self._fill_quest(quest, tree_id, user_id)
                
                if success:
                    filled_count += 1
                else:
                    errors.append({
                        "quest_id": quest.id,
                        "quest_title": quest.title,
                        "error": error_msg,
                    })
            
            logger.info(
                f"Quest auto-fill completed: {filled_count}/{total_quests} filled, "
                f"{len(errors)} errors"
            )
            
            return {
                "status": "completed",
                "tree_id": tree_id,
                "quests_filled": filled_count,
                "total_quests": total_quests,
                "errors": errors,
            }
            
        except GeneratedSkillTree.DoesNotExist:
            logger.error(f"GeneratedSkillTree {tree_id} not found")
            return {
                "status": "failed",
                "error": "Tree not found",
                "tree_id": tree_id,
            }
        except Exception as e:
            logger.error(f"Unexpected error in quest auto-fill: {str(e)}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
                "tree_id": tree_id,
            }
