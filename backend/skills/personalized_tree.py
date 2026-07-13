"""
PersonalizedTreeService — SkillTree AI
========================================
Generates the fully personalized, AI-driven learning roadmap that replaces the
old static skill tree. Driven entirely by the user's OnboardingProfile.

Pipeline (runs inside Celery, chunked and resumable):

  Phase 1  PLAN      One LM Studio call produces an outline of >= MIN_NODES
                     nodes + DAG edges. Saved on tree.outline.
  Phase 2  CHUNKS    Nodes are generated CHUNK_SIZE at a time. Per node:
                       - paid courses   (Apify, DB-cached)
                       - free resources (SERP API, DB-cached)
                       - LM Studio generates full node content:
                         detailed description, 2+ MCQs, coding question when
                         applicable, practical exercise, mini challenge
                       - Skill + Quest rows saved in one transaction
                       - progress counters updated, WS event broadcast,
                         node mirrored to MongoDB (best effort)
  Phase 3  FINALIZE  Prerequisite edges + tree depths (reuses the existing
                     SkillTreeGeneratorService helpers), initial SkillProgress
                     unlock (roots available, rest locked), tree mirrored to
                     MongoDB, status='ready', profile.path_generated=True.

Resume: tree.outline['created'] maps outline node id -> Skill pk. Re-running
the task skips nodes already created, so an interrupted generation loses at
most the node that was in flight. The Celery task heartbeats tree.updated_at
on every node; TreeGenerationStatusView re-dispatches stale generations.
"""

import json
import logging
import re
from typing import Dict, List

from asgiref.sync import async_to_sync
from django.conf import settings
from django.db import transaction

from core.lm_client import lm_client, ExecutionServiceUnavailable
from quests.models import Quest
from skills.course_fetcher import CourseFetcherService
from skills.models import GeneratedSkillTree, Skill, SkillProgress
from skills.resource_fetcher import FreeResourceFetcher, api_cached

logger = logging.getLogger(__name__)

CHUNK_SIZE = 3
MIN_NODES = 20
TARGET_NODES = 22
MIN_PAID_COURSES = 3
MIN_FREE_RESOURCES = 3

_MCQ_LETTERS = ["A", "B", "C", "D"]


def _obj(properties: Dict, **kw) -> Dict:
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties.keys()),
        "additionalProperties": False,
        **kw,
    }


_STR = {"type": "string"}
_INT = {"type": "integer"}

# LM Studio structured-output schemas (grammar-constrained decoding). These
# force the model to emit valid JSON in `content` even when it is a
# reasoning-heavy model, instead of rambling in reasoning_content.
_SCHEMAS = {
    "outline": _obj({
        "nodes": {"type": "array", "minItems": MIN_NODES, "items": _obj({
            "id": _STR, "title": _STR, "difficulty": _INT,
            "category": _STR, "needs_coding_quest": {"type": "boolean"},
        })},
        "edges": {"type": "array", "items": _obj({"from": _STR, "to": _STR})},
    }),
    "lesson": _obj({
        "description": _STR,
        "estimated_minutes": _INT,
        "skills_gained": {"type": "array", "minItems": 2, "items": _STR},
    }),
    "mcqs": _obj({
        "mcqs": {"type": "array", "minItems": 2, "items": _obj({
            "question": _STR,
            "options": {"type": "array", "minItems": 4, "maxItems": 4, "items": _STR},
            "correct_index": _INT,
            "explanation": _STR,
        })},
    }),
    "coding": _obj({
        "title": _STR, "description": _STR, "starter_code": _STR,
        "test_cases": {"type": "array", "minItems": 3, "items": _obj({
            "input": _STR, "expected_output": _STR,
        })},
    }),
    "practice": _obj({
        "exercise": _obj({"title": _STR, "description": _STR}),
        "mini_challenge": _obj({"title": _STR, "description": _STR}),
    }),
}


class PersonalizedTreeService:
    """Chunked, resumable AI roadmap generation from an onboarding profile."""

    def __init__(self):
        self.lm = lm_client
        self.max_retries = getattr(settings, "LM_STUDIO_MAX_RETRIES", 2)
        self.courses = CourseFetcherService()
        self.resources = FreeResourceFetcher()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_tree_for_profile(self, profile) -> GeneratedSkillTree:
        """Create the tree record for a profile and link it. Does NOT generate."""
        topic = (profile.target_role or "").strip() or ", ".join(profile.selected_interests[:3]) or "Software Development"
        tree = GeneratedSkillTree.objects.create(
            topic=topic,
            created_by=profile.user,
            status="generating",
            stage="queued",
        )
        profile.generated_tree = tree
        profile.generated_topic = topic
        profile.save(update_fields=["generated_tree", "generated_topic"])
        return tree

    def run(self, tree_id: str) -> Dict:
        """Main entry point — called by the Celery task. Idempotent."""
        tree = GeneratedSkillTree.objects.select_related("created_by").get(id=tree_id)
        if tree.status == "ready":
            return {"status": "already_ready", "tree_id": str(tree_id)}

        profile = getattr(tree.created_by, "onboarding_profile", None)

        try:
            tree.status = "generating"
            tree.error = ""

            # Phase 1 — plan
            if not tree.outline.get("nodes"):
                self._set_stage(tree, "Designing your personalized roadmap")
                tree.outline = self._generate_outline(tree.topic, profile)
                tree.total_nodes = len(tree.outline["nodes"])
                tree.save()
                self._broadcast(tree)

            outline = tree.outline
            created: Dict[str, int] = outline.setdefault("created", {})
            nodes = outline["nodes"]
            tree.total_nodes = len(nodes)

            # Phase 2 — chunked node generation
            pending = [n for n in nodes if str(n["id"]) not in created]
            for chunk_start in range(0, len(pending), CHUNK_SIZE):
                chunk = pending[chunk_start:chunk_start + CHUNK_SIZE]
                for node in chunk:
                    skill, quests = self._generate_and_save_node(tree, profile, node)
                    created[str(node["id"])] = skill.id
                    tree.outline = outline
                    tree.nodes_completed = len(created)
                    tree.save()
                    self._broadcast(tree)
                    self._mirror_node(skill, quests)

            # Phase 3 — finalize
            self._set_stage(tree, "Connecting your roadmap")
            self._finalize(tree, profile)

            tree.stage = "complete"
            tree.status = "ready"
            tree.save()
            self._broadcast(tree)

            logger.info("[PTREE] Generation complete: tree=%s nodes=%d", tree_id, tree.nodes_completed)
            return {"status": "success", "tree_id": str(tree_id), "nodes": tree.nodes_completed}

        except Exception as exc:
            logger.error("[PTREE] Generation failed for tree=%s: %s", tree_id, exc, exc_info=True)
            GeneratedSkillTree.objects.filter(id=tree_id).update(error=str(exc)[:2000])
            raise

    # ------------------------------------------------------------------
    # Phase 1 — plan
    # ------------------------------------------------------------------

    def _generate_outline(self, topic: str, profile) -> Dict:
        # Headroom for thinking models: reasoning tokens count against
        # max_tokens even though the outline JSON itself is small.
        return self._lm_step(
            self._outline_prompt(topic, profile),
            self._validate_outline,
            max_tokens=4096,
            step_name="outline",
        )

    def _outline_prompt(self, topic: str, profile) -> str:
        # ponytail: outline is deliberately minimal (ids, titles, edges) — local
        # thinking models (e.g. Gemma 4) burn most of the token budget on
        # reasoning, so the full node detail is generated in small per-node
        # calls instead of one giant JSON blob here.
        p = self._profile_summary(profile)
        return f"""You are an expert curriculum designer. Design a personalized learning roadmap for the topic "{topic}".

LEARNER PROFILE
{p}

REQUIREMENTS
- EXACTLY {TARGET_NODES} nodes (NEVER fewer than {MIN_NODES}), ordered foundational -> advanced.
- Nodes must form a directed acyclic graph: every non-root node has at least one prerequisite edge, no cycles.
- Difficulty (1-5) must increase with depth. Tailor node topics to the learner's levels and interests.
- needs_coding_quest: true only when hands-on coding practice makes sense for the node.
- Keep titles short. Do NOT include descriptions or any other fields.

Return ONLY valid JSON with this EXACT structure (no markdown, no commentary):
{{
  "nodes": [
    {{"id": "n1", "title": "...", "difficulty": 1, "category": "...", "needs_coding_quest": true}}
  ],
  "edges": [
    {{"from": "n1", "to": "n2"}}
  ]
}}"""

    def _validate_outline(self, data: Dict) -> Dict:
        nodes = data.get("nodes")
        if not isinstance(nodes, list) or len(nodes) < MIN_NODES:
            raise ValueError(f"outline must contain at least {MIN_NODES} nodes, got {len(nodes or [])}")

        clean_nodes, ids = [], set()
        for n in nodes:
            for field in ("id", "title"):
                if not n.get(field):
                    raise ValueError(f"outline node missing '{field}': {n}")
            nid = str(n["id"])
            if nid in ids:
                raise ValueError(f"duplicate outline node id {nid}")
            ids.add(nid)
            clean_nodes.append({
                "id": nid,
                "title": str(n["title"])[:200],
                "description": str(n.get("description", "")),
                "difficulty": min(5, max(1, int(n.get("difficulty", 2)))),
                "category": str(n.get("category", "general"))[:50],
                "needs_coding_quest": bool(n.get("needs_coding_quest", True)),
            })

        # Keep only valid, cycle-free edges (in-memory DFS on the growing graph)
        adjacency: Dict[str, List[str]] = {i: [] for i in ids}

        def reaches(start: str, target: str, seen=None) -> bool:
            if start == target:
                return True
            seen = seen or set()
            for nxt in adjacency.get(start, []):
                if nxt not in seen:
                    seen.add(nxt)
                    if reaches(nxt, target, seen):
                        return True
            return False

        clean_edges = []
        for e in data.get("edges", []) or []:
            f, t = str(e.get("from", "")), str(e.get("to", ""))
            if f in ids and t in ids and f != t and not reaches(t, f):
                adjacency[f].append(t)
                clean_edges.append({"from": f, "to": t})
            else:
                logger.warning("[PTREE] dropping invalid/cyclic edge %s", e)

        return {"nodes": clean_nodes, "edges": clean_edges, "created": {}}

    # ------------------------------------------------------------------
    # Phase 2 — node generation
    # ------------------------------------------------------------------

    def _generate_and_save_node(self, tree, profile, node: Dict):
        title = node["title"]
        label = f"Node {tree.nodes_completed + 1}/{tree.total_nodes}: {title}"

        self._set_stage(tree, f"{label} — finding courses & resources")
        paid = api_cached(
            f"apify:courses:{title.lower()}",
            lambda: self.courses.fetch_courses_for_skill(title, max_results=5),
        )
        free = api_cached(
            f"serp:free:{title.lower()}",
            lambda: self.resources.fetch_free_resources(title, max_results=6),
        )
        if len(paid) < MIN_PAID_COURSES:
            logger.warning("[PTREE] only %d/%d paid courses for %r", len(paid), MIN_PAID_COURSES, title)
        if len(free) < MIN_FREE_RESOURCES:
            logger.warning("[PTREE] only %d/%d free resources for %r", len(free), MIN_FREE_RESOURCES, title)

        content = self._generate_node_content(tree, profile, node, paid, free, label)
        return self._save_node(tree, node, content, paid, free)

    def _generate_node_content(self, tree, profile, node: Dict, paid: List, free: List, label: str) -> Dict:
        """
        Build the full node one SMALL LM call at a time — thinking models
        (Gemma 4 etc.) reliably complete short JSON answers but truncate large
        ones, which was silently dropping quests. Each step retries
        independently, and the stage line shows exactly what is being written.
        """
        header = self._node_header(profile, node, paid, free)
        content: Dict = {}

        self._set_stage(tree, f"{label} — writing lesson")
        content.update(self._lm_step(
            header + """
Write the lesson summary for this node.
- "description": 3-5 sentences tailored to the learner, mentioning what they'll be able to do afterwards.
- "estimated_minutes": realistic total learning time (15-600).
- "skills_gained": 2-5 concrete skills gained.

Return ONLY valid JSON (no markdown, no commentary):
{"description": "...", "estimated_minutes": 120, "skills_gained": ["...", "..."]}""",
            lambda d: self._validate_lesson(d, node),
            step_name="lesson",
        ))

        self._set_stage(tree, f"{label} — writing quiz questions")
        content["mcqs"] = self._lm_step(
            header + """
Write exactly 2 multiple-choice questions that test understanding of this node.
Each question has exactly 4 options and exactly one correct answer. Distractors must be plausible.

Return ONLY valid JSON (no markdown, no commentary):
{"mcqs": [
  {"question": "...", "options": ["...", "...", "...", "..."], "correct_index": 0, "explanation": "..."},
  {"question": "...", "options": ["...", "...", "...", "..."], "correct_index": 2, "explanation": "..."}
]}""",
            self._validate_mcqs,
            step_name="mcqs",
        )["mcqs"]

        content["coding_question"] = None
        if node.get("needs_coding_quest"):
            self._set_stage(tree, f"{label} — creating coding challenge")
            try:
                content["coding_question"] = self._lm_step(
                    header + """
Write one coding challenge for this node, solvable in 15-30 minutes.

Return ONLY valid JSON (no markdown, no commentary):
{"title": "...", "description": "problem statement with examples", "starter_code": "...",
 "test_cases": [{"input": "...", "expected_output": "..."}, {"input": "...", "expected_output": "..."},
                {"input": "...", "expected_output": "..."}]}""",
                    self._validate_coding,
                    step_name="coding",
                )
            except ValueError as exc:
                # ponytail: a stubborn coding step must not stall the whole
                # roadmap — the node still ships with MCQs/exercise/challenge.
                logger.warning("[PTREE] skipping coding quest for %r: %s", node["title"], exc)

        self._set_stage(tree, f"{label} — designing practice tasks")
        content.update(self._lm_step(
            header + """
Write one practical exercise (hands-on, concrete steps) and one mini challenge
(small self-contained task that proves mastery) for this node.

Return ONLY valid JSON (no markdown, no commentary):
{"exercise": {"title": "...", "description": "step-by-step practical exercise"},
 "mini_challenge": {"title": "...", "description": "..."}}""",
            self._validate_practice,
            step_name="practice",
        ))

        return content

    def _node_header(self, profile, node: Dict, paid: List, free: List) -> str:
        course_titles = "; ".join(c.get("title", "") for c in paid[:5]) or "none found"
        free_titles = "; ".join(r.get("title", "") for r in free[:6]) or "none found"
        return f"""You are creating content for roadmap node "{node['title']}" (difficulty {node['difficulty']}/5).

LEARNER PROFILE
{self._profile_summary(profile)}

CONTEXT
- Available paid courses: {course_titles}
- Available free resources: {free_titles}
"""

    # ── per-step validators ────────────────────────────────────────────

    @staticmethod
    def _validate_lesson(data: Dict, node: Dict) -> Dict:
        if not isinstance(data, dict) or not data.get("description"):
            raise ValueError("missing 'description'")
        try:
            minutes = min(600, max(15, int(data.get("estimated_minutes", 90))))
        except (TypeError, ValueError):
            minutes = 90
        gained = data.get("skills_gained") or [node["title"]]
        return {
            "description": str(data["description"]),
            "estimated_minutes": minutes,
            "skills_gained": [str(s) for s in gained][:10],
        }

    @staticmethod
    def _validate_mcqs(data: Dict) -> Dict:
        mcqs = data.get("mcqs") if isinstance(data, dict) else None
        if not isinstance(mcqs, list) or len(mcqs) < 2:
            raise ValueError("need at least 2 MCQs")
        for q in mcqs:
            opts = q.get("options")
            if not q.get("question") or not isinstance(opts, list) or len(opts) != 4:
                raise ValueError(f"MCQ must have a question and exactly 4 options: {q}")
            ci = q.get("correct_index", q.get("correctAnswer"))
            if not isinstance(ci, int) or not (0 <= ci <= 3):
                raise ValueError(f"MCQ needs integer correct_index 0-3: {q}")
            q["correct_index"] = ci
        return {"mcqs": mcqs}

    @staticmethod
    def _validate_coding(data: Dict) -> Dict:
        if not isinstance(data, dict):
            raise ValueError("coding challenge must be a JSON object")
        tcs = data.get("test_cases")
        if not data.get("description") or not isinstance(tcs, list) or len(tcs) < 3:
            raise ValueError("coding challenge needs description and >= 3 test_cases")
        for tc in tcs:
            if "input" not in tc or ("expected_output" not in tc and "expectedOutput" not in tc):
                raise ValueError(f"test case needs input and expected_output: {tc}")
        return data

    @staticmethod
    def _validate_practice(data: Dict) -> Dict:
        for key in ("exercise", "mini_challenge"):
            block = data.get(key) if isinstance(data, dict) else None
            if not isinstance(block, dict) or not block.get("description"):
                raise ValueError(f"'{key}' object with a description is required")
        return {"exercise": data["exercise"], "mini_challenge": data["mini_challenge"]}

    @transaction.atomic
    def _save_node(self, tree, node: Dict, content: Dict, paid: List, free: List):
        skill = Skill.objects.create(
            title=node["title"],
            description=content["description"],
            difficulty=node["difficulty"],
            category=node["category"],
            tree_depth=0,  # set in _finalize once all edges exist
            xp_required_to_unlock=0,  # ponytail: unlock is prerequisite-gated, not XP-gated
            xp_reward=min(500, max(50, node["difficulty"] * 100)),
            estimated_minutes=content["estimated_minutes"],
            skills_gained=content["skills_gained"],
            courses=paid,
            free_resources=free,
        )
        tree.skills_created.add(skill)

        quests = []
        mult = 1.0 + 0.25 * (node["difficulty"] - 1)
        for i, q in enumerate(content["mcqs"], start=1):
            options = "\n".join(f"{_MCQ_LETTERS[j]}) {opt}" for j, opt in enumerate(q["options"]))
            quests.append(Quest(
                skill=skill, type="mcq",
                title=f"{skill.title} – Quiz {i}"[:200],
                description=f"{q['question']}\n\n{options}",
                test_cases=[{
                    "expected_output": _MCQ_LETTERS[q["correct_index"]],
                    "explanation": q.get("explanation", ""),
                }],
                xp_reward=50, estimated_minutes=5, difficulty_multiplier=mult,
            ))

        coding = content.get("coding_question")
        if isinstance(coding, dict):
            quests.append(Quest(
                skill=skill, type="coding",
                title=(coding.get("title") or f"{skill.title} – Coding Challenge")[:200],
                description=coding["description"],
                starter_code=coding.get("starter_code", ""),
                test_cases=[
                    {"input": tc.get("input", ""),
                     "expected_output": tc.get("expected_output", tc.get("expectedOutput", ""))}
                    for tc in coding["test_cases"]
                ],
                xp_reward=100, estimated_minutes=30, difficulty_multiplier=mult,
            ))

        for qtype, key, xp, minutes in (
            ("exercise", "exercise", 75, 30),
            ("challenge", "mini_challenge", 100, 45),
        ):
            block = content[key]
            quests.append(Quest(
                skill=skill, type=qtype,
                title=(block.get("title") or f"{skill.title} – {qtype.title()}")[:200],
                description=block["description"],
                xp_reward=xp, estimated_minutes=minutes, difficulty_multiplier=mult,
            ))

        Quest.objects.bulk_create(quests)
        return skill, quests

    # ------------------------------------------------------------------
    # Phase 3 — finalize
    # ------------------------------------------------------------------

    def _finalize(self, tree, profile):
        from skills.ai_tree_generator import SkillTreeGeneratorService

        outline = tree.outline
        skills_by_pk = {s.id: s for s in tree.skills_created.all()}
        id_map = {
            nid: skills_by_pk[pk]
            for nid, pk in outline.get("created", {}).items()
            if pk in skills_by_pk
        }

        helper = SkillTreeGeneratorService()
        helper._calculate_and_store_depths(outline["nodes"], outline["edges"], id_map)
        helper._create_prerequisites(outline["edges"], id_map)

        # Initial unlock state for the owner: roots available, everything else locked.
        has_incoming = {e["to"] for e in outline["edges"]}
        for nid, skill in id_map.items():
            SkillProgress.objects.update_or_create(
                user=tree.created_by,
                skill=skill,
                defaults={"status": "locked" if nid in has_incoming else "available"},
            )

        self._mirror_tree(tree)

        if profile is not None:
            profile.path_generated = True
            profile.save(update_fields=["path_generated"])

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _profile_summary(profile) -> str:
        if profile is None:
            return "- No profile available; assume a motivated beginner."
        return (
            f"- Primary goal: {profile.get_primary_goal_display()}\n"
            f"- Target role: {profile.target_role}\n"
            f"- Experience: {profile.experience_years} years\n"
            f"- Self-assessed levels: {json.dumps(profile.category_levels)}\n"
            f"- Interests: {', '.join(profile.selected_interests)}\n"
            f"- Weekly study hours: {profile.weekly_hours}"
        )

    def _lm_step(self, prompt: str, validate, max_tokens: int = 2048, step_name: str = "step") -> Dict:
        """
        One small LM call with validation and retries. On rejection the retry
        prompt includes the reason so the model can correct itself.
        Output is grammar-constrained via the step's JSON schema when one exists.
        """
        schema = _SCHEMAS.get(step_name)
        last_err = None
        for attempt in range(self.max_retries + 1):
            full = prompt if attempt == 0 else (
                prompt + f"\n\nIMPORTANT: Your previous answer was rejected ({last_err}). "
                "Return ONLY valid JSON in the exact structure requested."
            )
            try:
                return validate(self._lm_json(full, max_tokens=max_tokens, schema=schema, name=step_name))
            except Exception as exc:
                last_err = exc
                logger.warning("[PTREE] %s attempt %d failed: %s", step_name, attempt + 1, exc)
        raise ValueError(f"{step_name} generation failed after retries: {last_err}")

    def _lm_json(self, prompt: str, max_tokens: int, schema: Dict = None, name: str = "step") -> Dict:
        messages = [
            {"role": "system", "content": (
                "You are an expert curriculum designer and technical educator. "
                "Always return valid JSON only — no markdown, no commentary. "
                "Answer directly without extended step-by-step deliberation. /no_think"
            )},
            {"role": "user", "content": prompt},
        ]
        response_format = None
        if schema is not None:
            response_format = {
                "type": "json_schema",
                "json_schema": {"name": name, "strict": True, "schema": schema},
            }
        try:
            response = self.lm.chat_completion(
                messages=messages, max_tokens=max_tokens, temperature=0.3,
                response_format=response_format,
            )
        except ExecutionServiceUnavailable as exc:
            # Some LM Studio builds/models reject structured output with a 400
            # — retry unconstrained rather than failing the step outright.
            if response_format is None or "status 400" not in str(exc):
                raise
            logger.warning("[PTREE] %s: response_format rejected, retrying unconstrained", name)
            response = self.lm.chat_completion(
                messages=messages, max_tokens=max_tokens, temperature=0.3,
            )
        return self._parse_json(self.lm.extract_content(response))

    @staticmethod
    def _parse_json(text: str) -> Dict:
        """
        Extract the JSON object from an LM response. Thinking models (Gemma 4,
        Qwen, ...) may wrap output in <think> blocks or markdown fences, or put
        the JSON at the end of their reasoning — strip all of that first.
        """
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        text = re.sub(r"```(?:json)?", "", text)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("no JSON object found in LM response")
        return json.loads(match.group())

    def _set_stage(self, tree, stage: str):
        """Persist + broadcast the stage. Also serves as the liveness
        heartbeat (updated_at) that TreeGenerationStatusView watches."""
        tree.stage = stage[:100]
        tree.save(update_fields=["stage", "updated_at"])
        self._broadcast(tree)

    def _broadcast(self, tree):
        """Push progress to ws/skills/generation/ (best effort)."""
        try:
            from channels.layers import get_channel_layer
            layer = get_channel_layer()
            if layer is None:
                return
            total = tree.total_nodes or 1
            async_to_sync(layer.group_send)(
                f"tree_generation_{tree.created_by_id}",
                {
                    "type": "generation_progress",
                    "tree_id": str(tree.id),
                    "status": tree.status,
                    "stage": tree.stage,
                    "nodes_completed": tree.nodes_completed,
                    "total_nodes": tree.total_nodes,
                    "percent": round(100 * tree.nodes_completed / total),
                },
            )
        except Exception as exc:
            logger.debug("[PTREE] WS broadcast skipped: %s", exc)

    def _mirror_node(self, skill, quests):
        try:
            from skills.mongo_mirror import mirror_node
            mirror_node(skill, quests)
        except Exception as exc:
            logger.warning("[PTREE] Mongo node mirror skipped: %s", exc)

    def _mirror_tree(self, tree):
        try:
            from skills.mongo_mirror import mirror_tree
            mirror_tree(tree)
        except Exception as exc:
            logger.warning("[PTREE] Mongo tree mirror skipped: %s", exc)
