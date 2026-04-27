"""
SkillTree AI - AI-Powered Skill Tree Generator
Generates pedagogically sound skill trees using LM Studio.
Handles prerequisite resolution, quest creation, and WebSocket notifications.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from uuid import uuid4
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from core.lm_client import lm_client, ExecutionServiceUnavailable
from skills.models import Skill, SkillPrerequisite, SkillProgress
from quests.models import Quest

User = get_user_model()
logger = logging.getLogger(__name__)


class SkillTreeGeneratorService:
    """
    Service for generating AI-powered skill trees.
    Orchestrates LM Studio calls, prerequisite resolution, and quest creation.
    """
    
    MAX_RETRIES = 2
    SYSTEM_PROMPT = (
        "You are an expert curriculum architect. Generate a complete, pedagogically sound "
        "skill tree for learning the given topic. Every skill must have a clear prerequisite "
        "relationship. Respond ONLY with valid JSON."
    )
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def generate_tree(
        self,
        topic: str,
        user: User,
        depth: int = 3
    ) -> Dict[str, Any]:
        """
        Generate a skill tree for the given topic.
        Creates GeneratedSkillTree record and dispatches async Celery task.
        
        Args:
            topic: Learning topic (e.g., "Machine Learning", "DevOps")
            user: User requesting the tree generation
            depth: Tree depth (1-5 levels)
            
        Returns:
            Dictionary with tree_id and status
        """
        from skills.models import GeneratedSkillTree
        
        # Validate inputs
        if not topic or len(topic.strip()) == 0:
            raise ValueError("Topic cannot be empty")
        
        if depth < 1 or depth > 5:
            raise ValueError("Depth must be between 1 and 5")
        
        topic = topic.strip()
        
        # Create GeneratedSkillTree record with "generating" status
        tree = GeneratedSkillTree.objects.create(
            topic=topic,
            created_by=user,
            status="generating",
            raw_ai_response={},
        )
        
        logger.info(f"Created GeneratedSkillTree {tree.id} for topic '{topic}' by user {user.id}")
        
        # Dispatch async Celery task
        from skills.tasks import generate_tree_task
        generate_tree_task.delay(str(tree.id), topic, depth)
        
        return {
            "tree_id": str(tree.id),
            "status": "generating",
            "topic": topic,
        }
    
    def _build_user_prompt(self, topic: str, depth: int) -> str:
        """
        Build the user prompt for LM Studio.
        
        Args:
            topic: Learning topic
            depth: Tree depth
            
        Returns:
            Formatted user prompt
        """
        json_format = "{'skills': [{'title':'...','description':'...','category':'...','difficulty':1-5,'estimated_hours':N,'prerequisites':[],'quest_titles':['...','...']}]}"
        return (
            f"Generate a skill tree for learning: {topic}. "
            f"Depth: {depth} levels. "
            f"Rules: "
            f"(1) 6–12 skills total, "
            f"(2) each skill has: title, description (2 sentences), category, difficulty (1–5), "
            f"estimated_hours, prerequisites (list of titles), "
            f"(3) 2 starter quest titles per skill, "
            f"(4) skills must flow from fundamentals to advanced. "
            f"Respond ONLY with valid JSON: {json_format}"
        )
    
    def _call_lm_studio(self, topic: str, depth: int) -> Dict[str, Any]:
        """
        Call LM Studio to generate skill tree JSON.
        Retries up to MAX_RETRIES times with simplified prompt on failure.
        
        Args:
            topic: Learning topic
            depth: Tree depth
            
        Returns:
            Parsed JSON response with skills
            
        Raises:
            ExecutionServiceUnavailable: If LM Studio is unavailable
            ValueError: If response cannot be parsed after retries
        """
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": self._build_user_prompt(topic, depth)},
        ]
        
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                logger.info(f"LM Studio call attempt {attempt + 1}/{self.MAX_RETRIES + 1} for topic '{topic}'")
                
                response = lm_client.chat_completion(
                    messages=messages,
                    max_tokens=2000,
                    temperature=0.1,
                )
                
                content = lm_client.extract_content(response)
                
                # Parse JSON from response
                parsed = self._extract_json(content)
                
                if not parsed or "skills" not in parsed:
                    raise ValueError("Response missing 'skills' key")
                
                logger.info(f"Successfully generated {len(parsed['skills'])} skills for topic '{topic}'")
                return parsed
                
            except (ExecutionServiceUnavailable, ValueError, json.JSONDecodeError) as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.MAX_RETRIES:
                    # Simplify prompt for retry
                    messages[1]["content"] = (
                        f"Generate a simple skill tree for {topic} with 6-8 skills. "
                        f"Each skill: title, description, difficulty (1-5), prerequisites (list of titles). "
                        f"Return ONLY valid JSON: {{'skills': [{{'title':'...','description':'...','difficulty':1-5,'prerequisites':[]}}]}}"
                    )
                else:
                    raise ValueError(f"Failed to generate skill tree after {self.MAX_RETRIES + 1} attempts: {str(e)}")
    
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
    
    def _would_create_cycle(self, from_skill: Skill, to_skill: Skill) -> bool:
        """
        Check if adding an edge from_skill -> to_skill would create a cycle.
        Uses DFS to detect cycles in the prerequisite graph.
        
        Args:
            from_skill: Source skill (prerequisite)
            to_skill: Target skill (dependent)
            
        Returns:
            True if adding this edge would create a cycle, False otherwise
        """
        visited = set()
        rec_stack = set()
        
        def has_cycle(skill):
            visited.add(skill)
            rec_stack.add(skill)
            
            # Check all skills that depend on this skill
            for edge in skill.dependent_edges.all():
                dependent = edge.to_skill
                
                if dependent == from_skill:
                    # Found a path back to from_skill - would create cycle
                    return True
                
                if dependent not in visited:
                    if has_cycle(dependent):
                        return True
                elif dependent in rec_stack:
                    # Back edge found - cycle detected
                    return True
            
            rec_stack.remove(skill)
            return False
        
        return has_cycle(to_skill)
    
    @transaction.atomic
    def _process_skills(
        self,
        tree_id: str,
        skills_data: List[Dict[str, Any]],
        topic: str,
    ) -> tuple[int, List[str]]:
        """
        Process skills from LM Studio response.
        Creates Skill, SkillPrerequisite, and Quest records.
        
        Args:
            tree_id: GeneratedSkillTree ID
            skills_data: List of skill dictionaries from LM Studio
            topic: Topic for category slug
            
        Returns:
            Tuple of (skills_created_count, error_messages)
        """
        from skills.models import GeneratedSkillTree
        
        tree = GeneratedSkillTree.objects.get(id=tree_id)
        topic_slug = topic.lower().replace(" ", "_")
        category = f"custom_{topic_slug}"
        
        created_skills = {}
        errors = []
        
        # First pass: Create all skills
        for skill_data in skills_data:
            try:
                title = skill_data.get("title", "").strip()
                description = skill_data.get("description", "").strip()
                difficulty = skill_data.get("difficulty", 1)
                estimated_hours = skill_data.get("estimated_hours", 1)
                
                if not title or not description:
                    errors.append(f"Skipped skill with missing title or description")
                    continue
                
                # Validate difficulty
                difficulty = max(1, min(5, int(difficulty)))
                estimated_hours = max(1, int(estimated_hours))
                
                skill, created = Skill.objects.get_or_create(
                    title=title,
                    defaults={
                        "description": description,
                        "category": category,
                        "difficulty": difficulty,
                        "xp_required_to_unlock": 0,
                    }
                )
                
                created_skills[title] = skill
                tree.skills_created.add(skill)
                
                logger.info(f"{'Created' if created else 'Found'} skill: {title}")
                
            except Exception as e:
                error_msg = f"Error processing skill '{skill_data.get('title', 'Unknown')}': {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Second pass: Resolve prerequisites
        for skill_data in skills_data:
            title = skill_data.get("title", "").strip()
            if title not in created_skills:
                continue
            
            skill = created_skills[title]
            prerequisites = skill_data.get("prerequisites", [])
            
            for prereq_title in prerequisites:
                prereq_title = prereq_title.strip()
                if prereq_title not in created_skills:
                    logger.warning(f"Prerequisite '{prereq_title}' not found for skill '{title}'")
                    continue
                
                prereq_skill = created_skills[prereq_title]
                
                # Check for circular dependencies before creating edge
                if self._would_create_cycle(prereq_skill, skill):
                    logger.warning(
                        f"Skipping circular prerequisite: {prereq_title} -> {title} "
                        f"(would create cycle in dependency graph)"
                    )
                    errors.append(f"Circular dependency detected: {prereq_title} -> {title}")
                    continue
                
                # Create prerequisite edge
                SkillPrerequisite.objects.get_or_create(
                    from_skill=prereq_skill,
                    to_skill=skill,
                )
                
                logger.info(f"Created prerequisite: {prereq_title} -> {title}")
        
        # Third pass: Create quests
        for skill_data in skills_data:
            title = skill_data.get("title", "").strip()
            if title not in created_skills:
                continue
            
            skill = created_skills[title]
            quest_titles = skill_data.get("quest_titles", [])
            
            # Create 2 quest stubs per skill
            for i, quest_title in enumerate(quest_titles[:2]):
                quest_title = quest_title.strip()
                if not quest_title:
                    continue
                
                try:
                    quest, created = Quest.objects.get_or_create(
                        skill=skill,
                        title=quest_title,
                        defaults={
                            "type": "coding",
                            "description": f"Complete this quest to master {skill.title}",
                            "starter_code": "",
                            "test_cases": [
                                {"input": "", "expected_output": ""},
                                {"input": "", "expected_output": ""},
                                {"input": "", "expected_output": ""},
                            ],
                            "xp_reward": 50 * skill.difficulty,
                            "estimated_minutes": 15 * skill.difficulty,
                            "difficulty_multiplier": 1.0,
                        }
                    )
                    
                    logger.info(f"{'Created' if created else 'Found'} quest: {quest_title} for skill {title}")
                    
                except Exception as e:
                    error_msg = f"Error creating quest '{quest_title}' for skill '{title}': {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
        
        return len(created_skills), errors
    
    def _broadcast_completion(
        self,
        tree_id: str,
        user_id: int,
        skill_count: int,
        topic: str,
    ) -> None:
        """
        Broadcast tree generation completion via WebSocket.
        
        Args:
            tree_id: GeneratedSkillTree ID
            user_id: User ID
            skill_count: Number of skills created
            topic: Topic name
        """
        try:
            group_name = f"tree_generation_{user_id}"
            message = {
                "type": "tree_generated",
                "tree_id": tree_id,
                "skill_count": skill_count,
                "topic": topic,
                "timestamp": timezone.now().isoformat(),
            }
            
            async_to_sync(self.channel_layer.group_send)(
                group_name,
                {
                    "type": "tree_generated",
                    "tree_id": tree_id,
                    "skill_count": skill_count,
                    "topic": topic,
                    "timestamp": message["timestamp"],
                }
            )
            
            logger.info(f"Broadcasted tree generation completion for tree {tree_id}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast tree generation: {str(e)}")
    
    def execute_generation(
        self,
        tree_id: str,
        topic: str,
        depth: int,
    ) -> Dict[str, Any]:
        """
        Execute the full skill tree generation pipeline.
        Called by Celery task.
        
        Args:
            tree_id: GeneratedSkillTree ID
            topic: Learning topic
            depth: Tree depth
            
        Returns:
            Result dictionary with status and details
        """
        from skills.models import GeneratedSkillTree
        
        try:
            tree = GeneratedSkillTree.objects.get(id=tree_id)
            
            logger.info(f"Starting skill tree generation for tree {tree_id}, topic '{topic}'")
            
            # Step 1: Call LM Studio
            try:
                skills_data = self._call_lm_studio(topic, depth)
            except (ExecutionServiceUnavailable, ValueError) as e:
                logger.error(f"LM Studio call failed: {str(e)}")
                tree.status = "failed"
                tree.raw_ai_response = {"error": str(e)}
                tree.save(update_fields=["status", "raw_ai_response"])
                return {
                    "status": "failed",
                    "error": str(e),
                    "tree_id": tree_id,
                }
            
            # Store raw response for debugging
            tree.raw_ai_response = skills_data
            tree.save(update_fields=["raw_ai_response"])
            
            # Step 2-4: Process skills, prerequisites, and quests
            try:
                skill_count, errors = self._process_skills(tree_id, skills_data.get("skills", []), topic)
            except Exception as e:
                logger.error(f"Skill processing failed: {str(e)}", exc_info=True)
                tree.status = "failed"
                tree.raw_ai_response["processing_error"] = str(e)
                tree.save(update_fields=["status", "raw_ai_response"])
                return {
                    "status": "failed",
                    "error": f"Skill processing failed: {str(e)}",
                    "tree_id": tree_id,
                }
            
            # Step 5: Mark as ready
            tree.status = "ready"
            tree.save(update_fields=["status"])
            
            logger.info(f"Skill tree generation completed: {skill_count} skills created")
            
            # Step 6: Broadcast completion
            self._broadcast_completion(tree_id, tree.created_by.id, skill_count, topic)
            
            return {
                "status": "ready",
                "tree_id": tree_id,
                "skill_count": skill_count,
                "topic": topic,
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
            logger.error(f"Unexpected error in tree generation: {str(e)}", exc_info=True)
            try:
                tree = GeneratedSkillTree.objects.get(id=tree_id)
                tree.status = "failed"
                tree.raw_ai_response["unexpected_error"] = str(e)
                tree.save(update_fields=["status", "raw_ai_response"])
            except Exception:
                pass
            return {
                "status": "failed",
                "error": str(e),
                "tree_id": tree_id,
            }
