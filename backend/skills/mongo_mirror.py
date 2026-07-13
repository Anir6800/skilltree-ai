"""
MongoDB mirror — SkillTree AI
===============================
Best-effort dual-write of generated learning trees into MongoDB, alongside the
relational store (SQLite/Postgres). Uses the existing MongoEngine documents in
mongo/documents.py, matching rows by `legacy_id` (relational PK) so mirroring
is idempotent and safe to re-run.

Callers (skills.personalized_tree) wrap every call in try/except — a Mongo
outage must never break generation.
"""

import logging

logger = logging.getLogger(__name__)


def _upsert(doc_cls, filters: dict, values: dict):
    """Idempotent upsert; returns the (re)fetched document."""
    doc_cls.objects(**filters).update_one(
        upsert=True, **{f"set__{k}": v for k, v in values.items()}
    )
    return doc_cls.objects(**filters).first()


def _connect():
    from mongo.connection import connect_mongo
    connect_mongo()  # idempotent; raises fast (5s) if Mongo is unreachable


def _mirror_skill(skill):
    from mongo.documents import Skill as MSkill
    return _upsert(MSkill, {"legacy_id": skill.id}, {
        "title": skill.title,
        "description": skill.description,
        "category": skill.category,
        "difficulty": skill.difficulty,
        "tree_depth": skill.tree_depth,
        "xp_required_to_unlock": skill.xp_required_to_unlock,
        "xp_reward": skill.xp_reward,
        "estimated_minutes": skill.estimated_minutes,
        "skills_gained": skill.skills_gained,
        "courses": skill.courses,
        "free_resources": skill.free_resources,
    })


def mirror_node(skill, quests):
    """Mirror one generated Skill and its Quests to MongoDB."""
    from mongo.documents import Quest as MQuest

    _connect()
    mskill = _mirror_skill(skill)
    for quest in quests:
        _upsert(MQuest, {"legacy_id": quest.id}, {
            "skill": mskill,
            "type": quest.type,
            "title": quest.title,
            "description": quest.description,
            "starter_code": quest.starter_code,
            "test_cases": quest.test_cases,
            "xp_reward": quest.xp_reward,
            "estimated_minutes": quest.estimated_minutes,
            "difficulty_multiplier": quest.difficulty_multiplier,
            "is_stub": quest.is_stub,
        })
    logger.info("[MIRROR] skill=%d + %d quests mirrored to MongoDB", skill.id, len(quests))


def mirror_tree(tree):
    """Mirror the tree record, its user, DAG edges and initial progress."""
    from mongo.documents import (
        GeneratedSkillTree as MTree,
        SkillPrerequisite as MEdge,
        SkillProgress as MProgress,
        User as MUser,
    )
    from skills.models import SkillPrerequisite, SkillProgress

    _connect()
    user = tree.created_by
    muser = _upsert(MUser, {"legacy_id": user.id}, {
        "username": user.username,
        "email": user.email or None,
        "xp": getattr(user, "xp", 0),
        "level": getattr(user, "level", 1),
    })

    skill_ids = list(tree.skills_created.values_list("id", flat=True))
    mskills = {s.id: _mirror_skill(s) for s in tree.skills_created.all()}

    _upsert(MTree, {"id": tree.id}, {
        "topic": tree.topic,
        "created_by": muser,
        "is_public": tree.is_public,
        "status": tree.status,
        "depth": tree.depth,
        "total_nodes": tree.total_nodes,
        "nodes_completed": tree.nodes_completed,
        "stage": tree.stage,
        "error": tree.error,
        "outline": tree.outline,
        "skills_created": list(mskills.values()),
    })

    for edge in SkillPrerequisite.objects.filter(
        from_skill_id__in=skill_ids, to_skill_id__in=skill_ids
    ):
        _upsert(MEdge, {"legacy_id": edge.id}, {
            "from_skill": mskills[edge.from_skill_id],
            "to_skill": mskills[edge.to_skill_id],
        })

    for prog in SkillProgress.objects.filter(user=user, skill_id__in=skill_ids):
        _upsert(MProgress, {"legacy_id": prog.id}, {
            "user": muser,
            "skill": mskills[prog.skill_id],
            "status": prog.status,
        })

    logger.info("[MIRROR] tree=%s fully mirrored to MongoDB", tree.id)
