"""
Pipeline check for PersonalizedTreeService: plan -> chunks -> save -> finalize,
plus crash-resume idempotency. LM Studio, Apify and SERP are faked.
"""

import pytest
from django.contrib.auth import get_user_model

from quests.models import Quest
from skills.models import GeneratedSkillTree, SkillPrerequisite, SkillProgress
from skills.personalized_tree import MIN_NODES, PersonalizedTreeService

User = get_user_model()

N_NODES = 21

FAKE_COURSES = [
    {"title": f"Course {i}", "provider": "Udemy", "url": f"https://u.example/{i}",
     "price": "$10", "rating": 4.5, "instructor": "Jane"} for i in range(3)
]
FAKE_RESOURCES = [
    {"title": f"Resource {i}", "url": f"https://r.example/{i}", "type": "tutorial",
     "source": "example", "snippet": ""} for i in range(3)
]


def fake_outline():
    # Slim outline contract: detail fields live in the per-node content call.
    nodes = [{
        "id": f"n{i}",
        "title": f"Node {i}",
        "difficulty": min(5, 1 + i // 5),
        "category": "webdev",
        "needs_coding_quest": i % 2 == 0,
    } for i in range(N_NODES)]
    edges = [{"from": f"n{i}", "to": f"n{i + 1}"} for i in range(N_NODES - 1)]
    return {"nodes": nodes, "edges": edges}


FAKE_STEPS = {
    "lesson summary": {
        "description": "Detailed personalized description of this node.",
        "estimated_minutes": 120,
        "skills_gained": ["skill-a", "skill-b"],
    },
    "multiple-choice questions": {
        "mcqs": [
            {"question": "Q1?", "options": ["a", "b", "c", "d"], "correct_index": 1, "explanation": "b"},
            {"question": "Q2?", "options": ["a", "b", "c", "d"], "correct_index": 0, "explanation": "a"},
        ],
    },
    "coding challenge": {
        "title": "Code it", "description": "Write a function.", "starter_code": "def f(): pass",
        "test_cases": [{"input": "1", "expected_output": "1"}] * 3,
    },
    "practical exercise": {
        "exercise": {"title": "Do it", "description": "Practical steps."},
        "mini_challenge": {"title": "Prove it", "description": "Small challenge."},
    },
}


def make_service(monkeypatch, fail_on_node_call=None):
    svc = PersonalizedTreeService()
    monkeypatch.setattr(svc.courses, "fetch_courses_for_skill", lambda *a, **k: FAKE_COURSES)
    monkeypatch.setattr(svc.resources, "fetch_free_resources", lambda *a, **k: FAKE_RESOURCES)

    calls = {"node": 0}

    def lm_json(prompt, max_tokens, schema=None, name="step"):
        if "Design a personalized learning roadmap" in prompt:
            return fake_outline()
        if "lesson summary" in prompt:
            calls["node"] += 1  # first step of every node — counts node attempts
            if fail_on_node_call and calls["node"] == fail_on_node_call:
                raise RuntimeError("simulated worker crash")
        for marker, payload in FAKE_STEPS.items():
            if marker in prompt:
                return payload
        raise AssertionError(f"unexpected LM prompt: {prompt[:120]}")

    monkeypatch.setattr(svc, "_lm_json", lm_json)
    return svc


@pytest.fixture
def tree(db):
    user = User.objects.create_user(username="learner", password="x")
    return GeneratedSkillTree.objects.create(topic="Full Stack Developer", created_by=user)


@pytest.mark.django_db
def test_full_generation(monkeypatch, tree):
    result = make_service(monkeypatch).run(str(tree.id))
    assert result["status"] == "success"

    tree.refresh_from_db()
    assert tree.status == "ready"
    assert tree.total_nodes == N_NODES >= MIN_NODES
    assert tree.nodes_completed == N_NODES

    skills = list(tree.skills_created.all())
    assert len(skills) == N_NODES
    for s in skills:
        assert s.courses and s.free_resources and s.skills_gained
        quests = Quest.objects.filter(skill=s)
        assert quests.filter(type="mcq").count() >= 2
        assert quests.filter(type="exercise").exists()
        assert quests.filter(type="challenge").exists()
        mcq = quests.filter(type="mcq").first()
        assert mcq.test_cases[0]["expected_output"] in "ABCD"

    # every outline node flagged needs_coding_quest (even indices) got a coding quest
    coding_flagged = sum(1 for i in range(N_NODES) if i % 2 == 0)
    assert Quest.objects.filter(skill__in=skills, type="coding").count() == coding_flagged

    # chain DAG: N-1 edges; root available, everything else locked
    skill_ids = [s.id for s in skills]
    assert SkillPrerequisite.objects.filter(from_skill_id__in=skill_ids).count() == N_NODES - 1
    progress = SkillProgress.objects.filter(user=tree.created_by, skill_id__in=skill_ids)
    assert progress.filter(status="available").count() == 1
    assert progress.filter(status="locked").count() == N_NODES - 1


def test_parse_json_strips_thinking_and_fences():
    wrapped = '<think>long reasoning here...</think>\n```json\n{"nodes": [1]}\n```'
    assert PersonalizedTreeService._parse_json(wrapped) == {"nodes": [1]}


@pytest.mark.django_db
def test_resume_after_crash_is_idempotent(monkeypatch, tree):
    # every node retries max_retries+1 times, so fail all attempts of node 5
    svc = make_service(monkeypatch, fail_on_node_call=5)
    svc.max_retries = 0
    with pytest.raises(ValueError):
        svc.run(str(tree.id))

    tree.refresh_from_db()
    assert 0 < tree.nodes_completed < N_NODES
    partial = tree.nodes_completed

    result = make_service(monkeypatch).run(str(tree.id))
    assert result["status"] == "success"
    tree.refresh_from_db()
    assert tree.nodes_completed == N_NODES
    assert tree.skills_created.count() == N_NODES  # no duplicates from the re-run
    assert partial < N_NODES


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
