"""
SkillTree AI Generator Service
Generates AI-powered skill trees with proper depth tracking, DAG edge creation,
and stub quest seeding.

Bug fixes applied:
  - _create_skills now returns both (skills_list, ai_id_map) so downstream
    methods receive the correct ai_string_id → Skill mapping.
  - _parse_ai_response now returns (skills_list, prerequisites_list) keeping
    the top-level prerequisites array that the AI emits.
  - _calculate_and_store_depths and _create_prerequisites accept the ai_id_map
    directly instead of rebuilding it with wrong DB-integer keys.
  - execute_generation wires all corrected return values through the pipeline.
  - generate_tree() is the new public entry point used by the view; it creates
    the GeneratedSkillTree record and dispatches the async Celery task.
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
    Generates AI-powered skill trees with depth tracking and DAG edge creation.
    """

    def __init__(self):
        self.lm = lm_client
        self.max_retries = getattr(settings, 'LM_STUDIO_MAX_RETRIES', 2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_tree(self, topic: str, user, depth: int = 3) -> Dict:
        """
        Public entry point called by GenerateSkillTreeView.
        Creates the GeneratedSkillTree record and dispatches the async task.

        Args:
            topic: Learning topic
            user: Django User instance
            depth: Tree depth 1-5

        Returns:
            dict with tree_id and status='generating'
        """
        topic = topic.strip()
        if not topic:
            raise ValueError("Topic is required")

        depth = max(1, min(5, int(depth)))

        tree = GeneratedSkillTree.objects.create(
            topic=topic,
            created_by=user,
            depth=depth,
            status='generating',
        )

        # Dispatch async generation task
        from skills.tasks import generate_tree_task
        generate_tree_task.delay(str(tree.id), topic, depth, user.id)

        logger.info(f"[TREE] Queued tree generation: tree={tree.id} topic={topic!r} depth={depth}")

        return {
            'tree_id': str(tree.id),
            'status': 'generating',
            'topic': topic,
            'depth': depth,
        }

    def execute_generation(self, tree_id: str, topic: str, depth: int, user_id: int) -> Dict:
        """
        Main generation pipeline — runs inside a Celery task.

        Args:
            tree_id: UUID of GeneratedSkillTree
            topic: Topic for tree generation
            depth: Tree depth (1-5)
            user_id: User ID (kept for logging / future use)

        Returns:
            Generation result with status and skill count
        """
        logger.info(f"[TREE] Starting tree generation: topic={topic!r} depth={depth} tree={tree_id}")

        try:
            tree = GeneratedSkillTree.objects.get(id=tree_id)

            # Step 1: Generate skills with LM Studio
            logger.info("[TREE] Calling LM Studio for tree generation")
            ai_response = self._call_lm_studio(topic, depth)

            # Step 2: Parse and validate response
            # Returns (skills_data_list, top_level_prerequisites_list)
            logger.info("[TREE] Parsing AI response")
            skills_data, prerequisites_data = self._parse_ai_response(ai_response)

            # Step 3: Create Skill objects
            # Returns (skills_list, ai_id → Skill map)
            logger.info(f"[TREE] Creating {len(skills_data)} skills")
            skills, skill_id_map = self._create_skills(skills_data, topic)

            # Step 4: Calculate and store tree depths (uses ai_id map)
            logger.info("[TREE] Calculating tree depths")
            self._calculate_and_store_depths(skills_data, prerequisites_data, skill_id_map)

            # Step 5: Create prerequisite edges (uses ai_id map + top-level prereqs)
            logger.info("[TREE] Creating prerequisite edges")
            self._create_prerequisites(prerequisites_data, skill_id_map)

            # Step 6: Create stub quests for every skill
            logger.info("[TREE] Creating stub quests")
            self._create_stub_quests(skills)

            # Step 7: Update tree metadata
            tree.skills_created.set(skills)
            tree.raw_ai_response = ai_response
            tree.depth = depth
            tree.status = 'ready'
            tree.save()

            logger.info(f"[TREE] Generation complete: {len(skills)} skills, tree={tree_id}")

            return {
                'status': 'success',
                'tree_id': str(tree_id),
                'skills_count': len(skills),
                'depth': depth,
            }

        except Exception as e:
            logger.error(f"[TREE] Generation failed: {str(e)}", exc_info=True)
            try:
                tree = GeneratedSkillTree.objects.get(id=tree_id)
                tree.status = 'failed'
                tree.save(update_fields=['status'])
            except Exception:
                pass
            raise

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _call_lm_studio(self, topic: str, depth: int) -> Dict:
        """
        Call LM Studio to generate the skill tree structure.
        Prerequisites are at the TOP LEVEL of the JSON response, not nested
        inside each skill object.
        """
        skill_count_hint = {1: "6-8", 2: "8-10", 3: "10-12", 4: "12-15", 5: "15-20"}.get(depth, "10-12")

        prompt = f"""Generate a comprehensive, progressive skill tree for "{topic}" with depth level {depth}.

REQUIREMENTS
- Generate {skill_count_hint} skills ordered from foundational to advanced.
- Each skill must have: id (e.g. "skill_1"), title, description (2 sentences), difficulty (1-5 int), category.
- Difficulty must increase as the tree deepens (root nodes difficulty 1-2, leaf nodes up to 5).
- Define prerequisite relationships at the TOP LEVEL "prerequisites" array.
- Every non-root skill must have at least one prerequisite.
- Ensure NO circular dependencies — this is a directed acyclic graph (DAG).

DEPTH GUIDELINES
- Depth 1: 6-8 skills, 1 layer of prerequisites
- Depth 2: 8-10 skills, 2 layers
- Depth 3: 10-12 skills, 3 layers
- Depth 4: 12-15 skills, 4 layers
- Depth 5: 15-20 skills, 5 layers

Return ONLY valid JSON with this EXACT structure:
{{
  "skills": [
    {{"id": "skill_1", "title": "...", "description": "...", "difficulty": 1, "category": "..."}},
    {{"id": "skill_2", "title": "...", "description": "...", "difficulty": 2, "category": "..."}}
  ],
  "prerequisites": [
    {{"from": "skill_1", "to": "skill_2"}},
    {{"from": "skill_2", "to": "skill_3"}}
  ]
}}"""

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert curriculum designer. Generate skill trees that are "
                    "well-structured, progressive, and comprehensive. Always return valid JSON only."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        try:
            response = self.lm.chat_completion(
                messages=messages,
                max_tokens=3000,
                temperature=0.3,
            )

            response_text = self.lm.extract_content(response)
            logger.debug(f"[TREE] LM Studio raw response (first 300 chars): {response_text[:300]}")

            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON object found in LM Studio response")

            return json.loads(json_match.group())

        except ExecutionServiceUnavailable as e:
            logger.error(f"[TREE] LM Studio unavailable: {str(e)}")
            raise

    def _parse_ai_response(self, response: Dict) -> Tuple[List[Dict], List[Dict]]:
        """
        Parse and validate AI response.

        Returns:
            (skills_list, prerequisites_list)  — prerequisites are the top-level list.
        """
        if not isinstance(response, dict):
            raise ValueError("AI response must be a JSON object (dict)")

        skills = response.get('skills', [])
        if not isinstance(skills, list) or len(skills) == 0:
            raise ValueError("AI response must contain a non-empty 'skills' array")

        # Build valid AI IDs for cross-referencing
        valid_ids = set()
        for skill in skills:
            required = {'id', 'title', 'description', 'difficulty', 'category'}
            missing = required - skill.keys()
            if missing:
                raise ValueError(f"Skill missing required fields {missing}: {skill}")

            difficulty = skill.get('difficulty')
            if not isinstance(difficulty, int) or not (1 <= difficulty <= 5):
                raise ValueError(f"Skill difficulty must be int 1-5, got {difficulty!r}: {skill}")

            valid_ids.add(skill['id'])

        # Top-level prerequisites (the correct location in the response)
        prerequisites = response.get('prerequisites', [])
        if not isinstance(prerequisites, list):
            logger.warning("[TREE] 'prerequisites' key is not a list — defaulting to []")
            prerequisites = []

        # Filter out any prereqs referencing unknown IDs
        valid_prereqs = []
        for prereq in prerequisites:
            from_id = prereq.get('from')
            to_id = prereq.get('to')
            if from_id in valid_ids and to_id in valid_ids and from_id != to_id:
                valid_prereqs.append(prereq)
            else:
                logger.warning(f"[TREE] Skipping invalid prerequisite edge: {prereq}")

        logger.info(f"[TREE] Parsed {len(skills)} skills and {len(valid_prereqs)} prerequisite edges")
        return skills, valid_prereqs

    @transaction.atomic
    def _create_skills(self, skills_data: List[Dict], topic: str) -> Tuple[List[Skill], Dict[str, Skill]]:
        """
        Create Skill objects from AI response.

        Returns:
            (skills_list, ai_string_id → Skill map)
            The ai_string_id map is essential — it lets _create_prerequisites
            and _calculate_and_store_depths look up Skills by the AI's own IDs
            ("skill_1", "skill_2", …) rather than the DB integer PKs.
        """
        skills: List[Skill] = []
        # KEY FIX: map AI string ID → Skill, not DB int ID → Skill
        skill_id_map: Dict[str, Skill] = {}

        category_slug = f"custom_{topic.lower().replace(' ', '_')[:30]}"

        for skill_data in skills_data:
            skill = Skill.objects.create(
                title=skill_data['title'],
                description=skill_data['description'],
                difficulty=skill_data['difficulty'],
                category=category_slug,
                tree_depth=0,  # calculated in _calculate_and_store_depths
                xp_required_to_unlock=skill_data['difficulty'] * 50,
            )
            skills.append(skill)
            skill_id_map[skill_data['id']] = skill  # ai string id → DB Skill
            logger.debug(f"[TREE] Created skill {skill.id}: {skill.title!r}")

        return skills, skill_id_map

    def _calculate_and_store_depths(
        self,
        skills_data: List[Dict],
        prerequisites_data: List[Dict],
        skill_id_map: Dict[str, Skill],
    ):
        """
        Calculate tree depth for each skill using BFS on the prerequisite DAG.
        Root nodes (no incoming edges) get depth 0; each hop adds 1.

        Args:
            skills_data: Raw skill dicts from AI (used for ID list)
            prerequisites_data: Top-level prerequisite edges [{from, to}, ...]
            skill_id_map: ai_string_id → Skill (correct map from _create_skills)
        """
        all_ai_ids = [s['id'] for s in skills_data]

        # Build set of IDs that appear as "to" (i.e. have incoming edges)
        has_incoming = {p['to'] for p in prerequisites_data}

        # Root nodes = no incoming edges
        roots = [ai_id for ai_id in all_ai_ids if ai_id not in has_incoming]

        # Build adjacency list: from_id → [to_id, ...]
        adjacency: Dict[str, List[str]] = {ai_id: [] for ai_id in all_ai_ids}
        for prereq in prerequisites_data:
            adjacency[prereq['from']].append(prereq['to'])

        # BFS from roots
        depths: Dict[str, int] = {ai_id: 0 for ai_id in all_ai_ids}
        queue = list(roots)

        while queue:
            current_id = queue.pop(0)
            current_depth = depths[current_id]

            for child_id in adjacency.get(current_id, []):
                if depths[child_id] <= current_depth:
                    depths[child_id] = current_depth + 1
                    queue.append(child_id)

        # Persist depths using the correct ai_id → Skill map
        skills_to_update = []
        for ai_id, skill in skill_id_map.items():
            skill.tree_depth = depths.get(ai_id, 0)
            skills_to_update.append(skill)

        Skill.objects.bulk_update(skills_to_update, ['tree_depth'])
        logger.debug(f"[TREE] Stored depths: {[(s.title, s.tree_depth) for s in skills_to_update]}")

    @transaction.atomic
    def _create_prerequisites(
        self,
        prerequisites_data: List[Dict],
        skill_id_map: Dict[str, Skill],
    ):
        """
        Create SkillPrerequisite (DAG edge) records.

        Args:
            prerequisites_data: Top-level prerequisite edges [{from, to}, ...]
            skill_id_map: ai_string_id → Skill (correct map from _create_skills)
        """
        created = 0
        skipped = 0

        for prereq in prerequisites_data:
            from_ai_id = prereq.get('from')
            to_ai_id = prereq.get('to')

            from_skill = skill_id_map.get(from_ai_id)
            to_skill = skill_id_map.get(to_ai_id)

            if not from_skill or not to_skill:
                logger.warning(f"[TREE] Prerequisite references unknown skill id: {prereq}")
                skipped += 1
                continue

            if from_skill == to_skill:
                skipped += 1
                continue

            # Guard against cycles before inserting
            if self._would_create_cycle(from_skill, to_skill):
                logger.warning(f"[TREE] Skipping cycle-inducing edge: {from_skill.title} → {to_skill.title}")
                skipped += 1
                continue

            _, edge_created = SkillPrerequisite.objects.get_or_create(
                from_skill=from_skill,
                to_skill=to_skill,
            )
            if edge_created:
                created += 1
                logger.debug(f"[TREE] Edge: {from_skill.title!r} → {to_skill.title!r}")

        logger.info(f"[TREE] Prerequisites: {created} created, {skipped} skipped")

    def _would_create_cycle(self, from_skill: Skill, to_skill: Skill) -> bool:
        """
        DFS check: would adding edge (from_skill → to_skill) create a cycle?
        A cycle exists if to_skill already has a path back to from_skill.
        """
        visited: set = set()

        def has_path(current: Skill, target: Skill) -> bool:
            if current.id == target.id:
                return True
            if current.id in visited:
                return False
            visited.add(current.id)
            # Follow existing outgoing edges (skills that current unlocks)
            for dependent in current.unlocks.all():
                if has_path(dependent, target):
                    return True
            return False

        return has_path(to_skill, from_skill)

    @transaction.atomic
    def _create_stub_quests(self, skills: List[Skill]):
        """
        Create 2 stub quests per skill (one coding, one debugging).
        Stubs are marked with is_stub=True so the autofill service can
        reliably find and populate them later.
        """
        quests_to_create = []
        for skill in skills:
            for i, quest_type in enumerate(['coding', 'debugging']):
                quests_to_create.append(
                    Quest(
                        skill=skill,
                        type=quest_type,
                        title=f"{skill.title} – {quest_type.title()} Challenge",
                        description='',
                        starter_code='',
                        test_cases=[],
                        xp_reward=50 * skill.difficulty,
                        estimated_minutes=15 + (10 * i),
                        difficulty_multiplier=1.0 + (0.5 * i),
                        is_stub=True,
                    )
                )

        Quest.objects.bulk_create(quests_to_create)
        logger.info(f"[TREE] Created {len(quests_to_create)} stub quests for {len(skills)} skills")


# ---------------------------------------------------------------------------
# Celery task — canonical definition lives in skills/tasks.py.
# This is only kept here so the import in the _updated copy doesn't break;
# the task in tasks.py takes precedence at Celery autodiscovery time.
# ---------------------------------------------------------------------------

def generate_skill_map(topic: str, depth: int, user) -> Dict:
    """
    Synchronous helper used by management commands (e.g. full_reset)
    to pre-warm demo user data without going through Celery.
    """
    if isinstance(user, int):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=user)

    tree = GeneratedSkillTree.objects.create(
        topic=topic,
        created_by=user,
        depth=depth,
        status='generating',
    )

    service = SkillTreeGeneratorService()
    result = service.execute_generation(
        tree_id=str(tree.id),
        topic=topic,
        depth=depth,
        user_id=user.id,
    )

    return result
