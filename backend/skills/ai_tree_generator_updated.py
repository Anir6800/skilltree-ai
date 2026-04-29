"""
SkillTree AI Generator Service - UPDATED
Generates AI-powered skill trees with proper depth tracking and auto-fill.
"""

import json
import logging
from typing import Dict, List, Tuple
from django.db import transaction
from django.conf import settings
from celery import shared_task
from core.lm_client import lm_client, ExecutionServiceUnavailable
from skills.models import GeneratedSkillTree, Skill, SkillPrerequisite
from quests.models import Quest

logger = logging.getLogger(__name__)


class SkillTreeGeneratorService:
    """
    Generates AI-powered skill trees with depth tracking.
    """
    
    def __init__(self):
        self.lm = lm_client
        self.max_retries = getattr(settings, 'LM_STUDIO_MAX_RETRIES', 2)
    
    def execute_generation(self, tree_id: str, topic: str, depth: int, user_id: int) -> Dict:
        """
        Main generation pipeline with depth persistence.
        
        Args:
            tree_id: UUID of GeneratedSkillTree
            topic: Topic for tree generation
            depth: Tree depth (1-5)
            user_id: User ID
            
        Returns:
            Generation result with status and skill count
        """
        logger.info(f"[TREE] Starting tree generation: topic={topic}, depth={depth}")
        
        try:
            tree = GeneratedSkillTree.objects.get(id=tree_id)
            
            # Step 1: Generate skills with LM Studio
            logger.info(f"[TREE] Calling LM Studio for tree generation")
            ai_response = self._call_lm_studio(topic, depth)
            
            # Step 2: Parse and validate response
            logger.info(f"[TREE] Parsing AI response")
            skills_data = self._parse_ai_response(ai_response)
            
            # Step 3: Create skills and prerequisites
            logger.info(f"[TREE] Creating {len(skills_data)} skills")
            skills = self._create_skills(skills_data, topic)
            
            # Step 4: Calculate and store tree depths
            logger.info(f"[TREE] Calculating tree depths")
            self._calculate_and_store_depths(skills, skills_data)
            
            # Step 5: Create prerequisites (DAG edges)
            logger.info(f"[TREE] Creating prerequisites")
            self._create_prerequisites(skills, skills_data)
            
            # Step 6: Create stub quests
            logger.info(f"[TREE] Creating stub quests")
            self._create_stub_quests(skills)
            
            # Step 7: Update tree metadata
            tree.skills_created.set(skills)
            tree.raw_ai_response = ai_response
            tree.depth = depth  # NEW: Store depth
            tree.status = 'ready'
            tree.save()
            
            logger.info(f"[TREE] Tree generation complete: {len(skills)} skills created")
            
            # Step 8: Auto-trigger quest auto-fill
            logger.info(f"[TREE] Auto-triggering quest auto-fill")
            from skills.tasks import autofill_quests_task
            autofill_quests_task.delay(str(tree_id))
            
            return {
                'status': 'success',
                'tree_id': str(tree_id),
                'skills_count': len(skills),
                'depth': depth,
            }
            
        except Exception as e:
            logger.error(f"[TREE] Generation failed: {str(e)}", exc_info=True)
            tree.status = 'failed'
            tree.save()
            raise
    
    def _call_lm_studio(self, topic: str, depth: int) -> Dict:
        """
        Call LM Studio to generate skill tree structure.
        
        Args:
            topic: Topic for tree
            depth: Tree depth (1-5)
            
        Returns:
            AI response with skills and prerequisites
        """
        prompt = f"""Generate a comprehensive skill tree for "{topic}" with depth level {depth}.

Requirements:
- Generate 6-12 skills based on depth (deeper = more skills)
- Each skill should have: title, description, difficulty (1-5), category
- Define prerequisite relationships (from_skill → to_skill)
- Ensure no circular dependencies
- Organize skills in a logical progression

Depth Guidelines:
- Depth 1: 6-8 foundational skills
- Depth 2: 8-10 skills with 1-2 levels
- Depth 3: 10-12 skills with 2-3 levels
- Depth 4: 12-15 skills with 3-4 levels
- Depth 5: 15-20 skills with 4-5 levels

Return ONLY valid JSON with this structure:
{{
  "skills": [
    {{"id": "skill_1", "title": "...", "description": "...", "difficulty": 2, "category": "..."}},
    ...
  ],
  "prerequisites": [
    {{"from": "skill_1", "to": "skill_2"}},
    ...
  ]
}}"""
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert curriculum designer. Generate skill trees that are well-structured, progressive, and comprehensive."
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
            logger.debug(f"[TREE] LM Studio response: {response_text[:200]}...")
            
            # Parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in LM Studio response")
            
            return json.loads(json_match.group())
            
        except ExecutionServiceUnavailable as e:
            logger.error(f"[TREE] LM Studio unavailable: {str(e)}")
            raise
    
    def _parse_ai_response(self, response: Dict) -> List[Dict]:
        """
        Parse and validate AI response.
        
        Args:
            response: AI response with skills and prerequisites
            
        Returns:
            Validated skills data
        """
        if not isinstance(response, dict):
            raise ValueError("Response must be a dictionary")
        
        skills = response.get('skills', [])
        if not isinstance(skills, list) or len(skills) == 0:
            raise ValueError("Response must contain 'skills' array")
        
        # Validate each skill
        for skill in skills:
            required_fields = ['id', 'title', 'description', 'difficulty', 'category']
            if not all(field in skill for field in required_fields):
                raise ValueError(f"Skill missing required fields: {skill}")
            
            if not 1 <= skill['difficulty'] <= 5:
                raise ValueError(f"Difficulty must be 1-5: {skill}")
        
        return skills
    
    @transaction.atomic
    def _create_skills(self, skills_data: List[Dict], topic: str) -> List[Skill]:
        """
        Create Skill objects from AI response.
        
        Args:
            skills_data: Skills from AI response
            topic: Topic for categorization
            
        Returns:
            Created Skill objects
        """
        skills = []
        skill_map = {}  # Map AI skill IDs to DB skill objects
        
        for skill_data in skills_data:
            skill = Skill.objects.create(
                title=skill_data['title'],
                description=skill_data['description'],
                difficulty=skill_data['difficulty'],
                category=f"custom_{topic.lower().replace(' ', '_')}",
                tree_depth=0,  # Will be calculated later
            )
            skills.append(skill)
            skill_map[skill_data['id']] = skill
            logger.debug(f"[TREE] Created skill: {skill.title}")
        
        return skills
    
    def _calculate_and_store_depths(self, skills: List[Skill], skills_data: List[Dict]):
        """
        Calculate tree depth for each skill using BFS.
        
        Args:
            skills: Created Skill objects
            skills_data: Original skills data with prerequisites
        """
        # Build skill ID map
        skill_map = {s.id: s for s in skills}
        
        # Build prerequisite graph
        prerequisites = {}
        for skill_data in skills_data:
            prerequisites[skill_data['id']] = []
        
        # Find root nodes (no prerequisites)
        root_nodes = []
        for skill_data in skills_data:
            has_prereq = False
            for skill_data2 in skills_data:
                # Check if this skill is a prerequisite for another
                for prereq in skill_data2.get('prerequisites', []):
                    if prereq.get('from') == skill_data['id']:
                        has_prereq = True
                        break
            if not has_prereq:
                root_nodes.append(skill_data['id'])
        
        # BFS to calculate depths
        depths = {s['id']: 0 for s in skills_data}
        queue = root_nodes.copy()
        
        while queue:
            current_id = queue.pop(0)
            current_depth = depths[current_id]
            
            # Find all skills that depend on current
            for skill_data in skills_data:
                for prereq in skill_data.get('prerequisites', []):
                    if prereq.get('from') == current_id:
                        to_id = prereq.get('to')
                        if to_id and depths[to_id] <= current_depth:
                            depths[to_id] = current_depth + 1
                            if to_id not in queue:
                                queue.append(to_id)
        
        # Update skills with calculated depths
        for skill_data in skills_data:
            skill = skill_map.get(skill_data['id'])
            if skill:
                skill.tree_depth = depths[skill_data['id']]
                skill.save(update_fields=['tree_depth'])
                logger.debug(f"[TREE] Set depth for {skill.title}: {skill.tree_depth}")
    
    @transaction.atomic
    def _create_prerequisites(self, skills: List[Skill], skills_data: List[Dict]):
        """
        Create prerequisite relationships (DAG edges).
        
        Args:
            skills: Created Skill objects
            skills_data: Original skills data with prerequisites
        """
        skill_map = {s.id: s for s in skills}
        
        for skill_data in skills_data:
            from_skill = skill_map.get(skill_data['id'])
            if not from_skill:
                continue
            
            for prereq in skill_data.get('prerequisites', []):
                to_id = prereq.get('to')
                to_skill = skill_map.get(to_id)
                
                if to_skill and from_skill != to_skill:
                    # Check for cycles before creating
                    if not self._would_create_cycle(from_skill, to_skill):
                        SkillPrerequisite.objects.get_or_create(
                            from_skill=from_skill,
                            to_skill=to_skill
                        )
                        logger.debug(f"[TREE] Created prerequisite: {from_skill.title} → {to_skill.title}")
    
    def _would_create_cycle(self, from_skill: Skill, to_skill: Skill) -> bool:
        """
        Check if creating edge would create a cycle using DFS.
        
        Args:
            from_skill: Source skill
            to_skill: Target skill
            
        Returns:
            True if cycle would be created
        """
        visited = set()
        
        def has_path(current, target):
            if current == target:
                return True
            if current in visited:
                return False
            
            visited.add(current)
            for dependent in current.unlocks.all():
                if has_path(dependent, target):
                    return True
            
            return False
        
        return has_path(to_skill, from_skill)
    
    @transaction.atomic
    def _create_stub_quests(self, skills: List[Skill]):
        """
        Create stub quests for each skill.
        
        Args:
            skills: Created Skill objects
        """
        for skill in skills:
            # Create 2 stub quests per skill
            for i in range(2):
                quest_type = 'coding' if i == 0 else 'debugging'
                
                quest = Quest.objects.create(
                    skill=skill,
                    type=quest_type,
                    title=f"{skill.title} - {quest_type.title()} Challenge",
                    description='',
                    starter_code='',
                    test_cases=[],
                    xp_reward=50 * skill.difficulty,
                    estimated_minutes=15,
                    difficulty_multiplier=1.0,
                    is_stub=True,  # NEW: Mark as stub
                )
                logger.debug(f"[TREE] Created stub quest: {quest.title}")


@shared_task(name='skills.tasks.generate_tree_task', bind=True, max_retries=2)
def generate_tree_task(self, tree_id: str, topic: str, depth: int, user_id: int):
    """
    Celery task for async tree generation.
    
    Args:
        tree_id: UUID of GeneratedSkillTree
        topic: Topic for tree
        depth: Tree depth (1-5)
        user_id: User ID
    """
    try:
        service = SkillTreeGeneratorService()
        result = service.execute_generation(tree_id, topic, depth, user_id)
        logger.info(f"[TASK] Tree generation task complete: {result}")
        return result
    except Exception as exc:
        logger.error(f"[TASK] Tree generation task failed: {str(exc)}", exc_info=True)
        raise self.retry(exc=exc, countdown=10)


def generate_skill_map(topic, depth, user):
    """
    Helper function to generate a skill map for a specific user.
    Used during full_reset to pre-warm demo accounts.
    """
    try:
        # If user is an ID, get the object
        if isinstance(user, int):
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user)

        # Create a placeholder GeneratedSkillTree
        tree = GeneratedSkillTree.objects.create(
            user=user,
            topic=topic,
            depth=depth,
            status='generating'
        )
        
        # Initialize the generator service
        service = SkillTreeGeneratorService()
        
        # Execute generation synchronously for the reset command
        result = service.execute_generation(
            tree_id=tree.id,
            topic=tree.topic,
            depth=tree.depth,
            user_id=user.id
        )
        
        return result
    except Exception as e:
        logger.error(f"Failed to generate skill map for user {user.id}: {e}")
        raise
