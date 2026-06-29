"""
PostgreSQL -> MongoDB data migration (ETL)
==========================================
Reads every legacy Django ORM row and writes the equivalent MongoEngine
document, remapping relational foreign keys to document references.

Design:
  - READ side uses the still-intact Django ORM (that is why we keep the legacy
    models until cutover).
  - WRITE side uses mongo.documents.
  - IDEMPOTENT: every migrated doc stores `legacy_id` (or the original UUID);
    re-running updates instead of duplicating. Safe to run repeatedly.
  - ORDERED by dependency so references always resolve.

Usage:
    cd backend
    # 1. Ensure Mongo is reachable and env is set (MONGODB_URI, MONGODB_DB)
    # 2. Ensure PostgreSQL/SQLite source is reachable (DATABASE_URL)
    venv/Scripts/python scripts/migrate_pg_to_mongo.py            # full run
    venv/Scripts/python scripts/migrate_pg_to_mongo.py --dry-run  # counts only
    venv/Scripts/python scripts/migrate_pg_to_mongo.py --only users skills

Exit code 0 on success; non-zero on any model failure (details logged).
"""

import os
import sys
import argparse
import logging

# --- Django bootstrap -------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django  # noqa: E402
django.setup()

from django.apps import apps as django_apps  # noqa: E402

from mongo.connection import connect_mongo  # noqa: E402
from mongo import documents as D  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("pg2mongo")

# In-memory remap caches: legacy pk -> mongo document
MAPS = {
    "user": {}, "skill": {}, "tree": {}, "quest": {}, "submission": {},
    "badge": {}, "group": {}, "shared_solution": {}, "match": {},
    "adaptive_profile": {}, "assessment_question": {},
}

DRY_RUN = False


def _get(model_label):
    app_label, model_name = model_label.split(".")
    return django_apps.get_model(app_label, model_name)


def _aware(dt):
    return dt  # Django already returns tz-aware datetimes when USE_TZ=True


def _upsert(doc_cls, legacy_id, **fields):
    """Create-or-update a document by legacy_id. Returns the saved document."""
    if DRY_RUN:
        return None
    existing = doc_cls.objects(legacy_id=legacy_id).first() if legacy_id is not None else None
    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
        existing.legacy_id = legacy_id
        existing.save()
        return existing
    doc = doc_cls(legacy_id=legacy_id, **fields)
    doc.save()
    return doc


# ---------------------------------------------------------------------------
# Per-domain migrators
# ---------------------------------------------------------------------------

def migrate_users():
    Model = _get("users.User")
    count = 0
    for u in Model.objects.all().iterator():
        if DRY_RUN:
            count += 1
            continue
        doc = D.User.objects(legacy_id=u.id).first() or D.User(legacy_id=u.id)
        doc.username = u.username
        doc.email = u.email or None
        doc.password = u.password          # copy Django hash verbatim
        doc.xp = u.xp
        doc.streak_days = u.streak_days
        doc.last_active = _aware(u.last_active) if u.last_active else None
        doc.role = getattr(u, "role", "student")
        doc.avatar_url = getattr(u, "avatar_url", "") or ""
        doc.is_active = u.is_active
        doc.is_staff = u.is_staff
        doc.is_superuser = u.is_superuser
        doc.date_joined = _aware(u.date_joined)
        doc.save()  # save() recomputes level from xp
        MAPS["user"][u.id] = doc
        count += 1
    logger.info("users: %s", count)


def migrate_badges():
    Model = _get("users.Badge")
    count = 0
    for b in Model.objects.all().iterator():
        if not DRY_RUN:
            doc = _upsert(
                D.Badge, b.id, slug=b.slug, name=b.name, description=b.description,
                icon_emoji=b.icon_emoji, rarity=b.rarity,
                unlock_condition=b.unlock_condition or {}, created_at=_aware(b.created_at),
            )
            MAPS["badge"][b.id] = doc
        count += 1
    logger.info("badges: %s", count)


def migrate_skills():
    Model = _get("skills.Skill")
    count = 0
    for s in Model.objects.all().iterator():
        if not DRY_RUN:
            doc = _upsert(
                D.Skill, s.id, title=s.title, description=s.description, category=s.category,
                difficulty=s.difficulty, tree_depth=s.tree_depth,
                xp_required_to_unlock=s.xp_required_to_unlock,
                created_at=_aware(s.created_at), updated_at=_aware(s.updated_at),
            )
            MAPS["skill"][s.id] = doc
        count += 1
    logger.info("skills: %s", count)


def migrate_skill_prereqs():
    Model = _get("skills.SkillPrerequisite")
    count = 0
    for e in Model.objects.all().iterator():
        if not DRY_RUN:
            _upsert(
                D.SkillPrerequisite, e.id,
                from_skill=MAPS["skill"].get(e.from_skill_id),
                to_skill=MAPS["skill"].get(e.to_skill_id),
                created_at=_aware(e.created_at),
            )
        count += 1
    logger.info("skill_prerequisites: %s", count)


def migrate_trees():
    Model = _get("skills.GeneratedSkillTree")
    count = 0
    for t in Model.objects.all().iterator():
        if not DRY_RUN:
            doc = D.GeneratedSkillTree.objects(id=t.id).first() or D.GeneratedSkillTree(id=t.id)
            doc.topic = t.topic
            doc.created_by = MAPS["user"].get(t.created_by_id)
            doc.is_public = t.is_public
            doc.raw_ai_response = t.raw_ai_response or {}
            doc.status = t.status
            doc.depth = t.depth
            doc.skills_created = [MAPS["skill"][s.id] for s in t.skills_created.all() if s.id in MAPS["skill"]]
            doc.created_at = _aware(t.created_at)
            doc.updated_at = _aware(t.updated_at)
            doc.save()
            MAPS["tree"][t.id] = doc
        count += 1
    logger.info("generated_skill_trees: %s", count)


def migrate_skill_progress():
    Model = _get("skills.SkillProgress")
    count = 0
    for sp in Model.objects.all().iterator():
        if not DRY_RUN:
            _upsert(
                D.SkillProgress, sp.id,
                user=MAPS["user"].get(sp.user_id), skill=MAPS["skill"].get(sp.skill_id),
                status=sp.status, completed_at=_aware(sp.completed_at) if sp.completed_at else None,
                quest_completion_count=sp.quest_completion_count,
                time_spent_minutes=sp.time_spent_minutes, attempts_count=sp.attempts_count,
                updated_at=_aware(sp.updated_at),
            )
        count += 1
    logger.info("skill_progress: %s", count)


def migrate_curricula():
    Model = _get("skills.UserCurriculum")
    count = 0
    for c in Model.objects.all().iterator():
        if not DRY_RUN:
            _upsert(
                D.UserCurriculum, c.id, user=MAPS["user"].get(c.user_id), weeks=c.weeks or [],
                created_at=_aware(c.created_at), updated_at=_aware(c.updated_at),
                target_completion_date=_aware(c.target_completion_date) if c.target_completion_date else None,
                weekly_hours=c.weekly_hours, total_quests=c.total_quests,
            )
        count += 1
    logger.info("user_curricula: %s", count)


def migrate_embedding_records():
    Model = _get("skills.EmbeddingRecord")
    count = 0
    for r in Model.objects.all().iterator():
        if not DRY_RUN:
            _upsert(
                D.EmbeddingRecord, r.id, content_type=r.content_type, object_id=r.object_id,
                collection_name=r.collection_name, chroma_id=r.chroma_id,
                embedded_at=_aware(r.embedded_at), updated_at=_aware(r.updated_at), checksum=r.checksum,
            )
        count += 1
    logger.info("embedding_records: %s", count)


def migrate_quests():
    Model = _get("quests.Quest")
    count = 0
    for q in Model.objects.all().iterator():
        if not DRY_RUN:
            doc = _upsert(
                D.Quest, q.id, skill=MAPS["skill"].get(q.skill_id), type=q.type, title=q.title,
                description=q.description, starter_code=q.starter_code, test_cases=q.test_cases or [],
                xp_reward=q.xp_reward, estimated_minutes=q.estimated_minutes,
                difficulty_multiplier=q.difficulty_multiplier, is_stub=q.is_stub,
                created_at=_aware(q.created_at), updated_at=_aware(q.updated_at),
            )
            MAPS["quest"][q.id] = doc
        count += 1
    logger.info("quests: %s", count)


def migrate_submissions():
    Model = _get("quests.QuestSubmission")
    count = 0
    for s in Model.objects.all().iterator():
        if not DRY_RUN:
            doc = _upsert(
                D.QuestSubmission, s.id, user=MAPS["user"].get(s.user_id),
                quest=MAPS["quest"].get(s.quest_id), code=s.code, language=s.language,
                status=s.status, execution_result=s.execution_result or {},
                ai_feedback=s.ai_feedback or {}, ai_detection_score=s.ai_detection_score,
                explanation=s.explanation, celery_task_id=s.celery_task_id,
                created_at=_aware(s.created_at), updated_at=_aware(s.updated_at),
            )
            MAPS["submission"][s.id] = doc
        count += 1
    logger.info("quest_submissions: %s", count)


def migrate_shared_solutions():
    Model = _get("quests.SharedSolution")
    count = 0
    for ss in Model.objects.all().iterator():
        if not DRY_RUN:
            doc = _upsert(
                D.SharedSolution, ss.id, submission=MAPS["submission"].get(ss.submission_id),
                shared_at=_aware(ss.shared_at),
                upvotes=[MAPS["user"][u.id] for u in ss.upvotes.all() if u.id in MAPS["user"]],
                views_count=ss.views_count, is_anonymous=ss.is_anonymous,
            )
            MAPS["shared_solution"][ss.id] = doc
        count += 1
    logger.info("shared_solutions: %s", count)


def migrate_solution_comments():
    Model = _get("quests.SolutionComment")
    # order by id so parents (lower id) migrate before children
    local = {}
    count = 0
    for c in Model.objects.all().order_by("id").iterator():
        if not DRY_RUN:
            doc = _upsert(
                D.SolutionComment, c.id, solution=MAPS["shared_solution"].get(c.solution_id),
                author=MAPS["user"].get(c.author_id), text=c.text,
                parent=local.get(c.parent_id) if c.parent_id else None,
                created_at=_aware(c.created_at),
            )
            local[c.id] = doc
        count += 1
    logger.info("solution_comments: %s", count)


def migrate_execution_tasks():
    Model = _get("executor.ExecutionTask")
    count = 0
    for t in Model.objects.all().iterator():
        if not DRY_RUN:
            _upsert(
                D.ExecutionTask, t.id, submission=MAPS["submission"].get(t.submission_id),
                task_id=t.task_id, status=t.status, worker_node=t.worker_node,
                started_at=_aware(t.started_at) if t.started_at else None,
                finished_at=_aware(t.finished_at) if t.finished_at else None,
                created_at=_aware(t.created_at),
            )
        count += 1
    logger.info("execution_tasks: %s", count)


def migrate_evaluations():
    Eval = _get("ai_evaluation.EvaluationResult")
    Style = _get("ai_evaluation.StyleReport")
    ce = 0
    for e in Eval.objects.all().iterator():
        if not DRY_RUN:
            _upsert(
                D.EvaluationResult, e.id, submission=MAPS["submission"].get(e.submission_id),
                score=e.score, summary=e.summary, pros=e.pros or [], cons=e.cons or [],
                suggestions=e.suggestions or [], evaluated_at=_aware(e.evaluated_at),
            )
        ce += 1
    cs = 0
    for s in Style.objects.all().iterator():
        if not DRY_RUN:
            _upsert(
                D.StyleReport, s.id, submission=MAPS["submission"].get(s.submission_id),
                readability_score=s.readability_score, naming_quality=s.naming_quality,
                idiomatic_patterns=s.idiomatic_patterns, style_issues=s.style_issues or [],
                positive_patterns=s.positive_patterns or [], generated_at=_aware(s.generated_at),
            )
        cs += 1
    logger.info("evaluation_results: %s | style_reports: %s", ce, cs)


def migrate_detection_logs():
    Model = _get("ai_detection.DetectionLog")
    count = 0
    for d in Model.objects.all().iterator():
        if not DRY_RUN:
            _upsert(
                D.DetectionLog, d.id, submission=MAPS["submission"].get(d.submission_id),
                embedding_score=d.embedding_score, llm_score=d.llm_score,
                heuristic_score=d.heuristic_score, final_score=d.final_score,
                llm_reasoning=d.llm_reasoning or {}, analyzed_at=_aware(d.analyzed_at),
            )
        count += 1
    logger.info("detection_logs: %s", count)


def migrate_matches():
    Match = _get("multiplayer.Match")
    Part = _get("multiplayer.MatchParticipant")
    cm = 0
    for m in Match.objects.all().iterator():
        if not DRY_RUN:
            doc = _upsert(
                D.Match, m.id, quest=MAPS["quest"].get(m.quest_id), status=m.status,
                winner=MAPS["user"].get(m.winner_id) if m.winner_id else None,
                created_at=_aware(m.created_at),
                started_at=_aware(m.started_at) if m.started_at else None,
                ended_at=_aware(m.ended_at) if m.ended_at else None,
            )
            MAPS["match"][m.id] = doc
        cm += 1
    cp = 0
    for p in Part.objects.all().iterator():
        if not DRY_RUN:
            _upsert(
                D.MatchParticipant, p.id, match=MAPS["match"].get(p.match_id),
                user=MAPS["user"].get(p.user_id), score=p.score, joined_at=_aware(p.joined_at),
            )
        cp += 1
    logger.info("matches: %s | match_participants: %s", cm, cp)


def migrate_leaderboard_snapshots():
    Model = _get("leaderboard.LeaderboardSnapshot")
    count = 0
    for s in Model.objects.all().iterator():
        if not DRY_RUN:
            _upsert(
                D.LeaderboardSnapshot, s.id, user=MAPS["user"].get(s.user_id),
                total_xp=s.total_xp, rank=s.rank, streak_days=s.streak_days,
                snapshot_at=_aware(s.snapshot_at),
            )
        count += 1
    logger.info("leaderboard_snapshots: %s", count)


def migrate_xp_logs():
    Model = _get("users.XPLog")
    count = 0
    for x in Model.objects.all().iterator():
        if not DRY_RUN:
            _upsert(
                D.XPLog, x.id, user=MAPS["user"].get(x.user_id), amount=x.amount,
                source=x.source, created_at=_aware(x.created_at),
            )
        count += 1
    logger.info("xp_logs: %s", count)


def migrate_user_badges():
    Model = _get("users.UserBadge")
    count = 0
    for ub in Model.objects.all().iterator():
        if not DRY_RUN:
            _upsert(
                D.UserBadge, ub.id, user=MAPS["user"].get(ub.user_id),
                badge=MAPS["badge"].get(ub.badge_id), earned_at=_aware(ub.earned_at), seen=ub.seen,
            )
        count += 1
    logger.info("user_badges: %s", count)


def migrate_weekly_reports():
    Model = _get("users.WeeklyReport")
    count = 0
    for w in Model.objects.all().iterator():
        if not DRY_RUN:
            _upsert(
                D.WeeklyReport, w.id, user=MAPS["user"].get(w.user_id), week_number=w.week_number,
                year=w.year, pdf_path=w.pdf_path, data=w.data or {}, narrative=w.narrative or {},
                generated_at=_aware(w.generated_at), viewed_at=_aware(w.viewed_at) if w.viewed_at else None,
            )
        count += 1
    logger.info("weekly_reports: %s", count)


def migrate_groups():
    Group = _get("users.StudyGroup")
    Mem = _get("users.StudyGroupMembership")
    Msg = _get("users.StudyGroupMessage")
    Goal = _get("users.StudyGroupGoal")
    cg = 0
    for g in Group.objects.all().iterator():
        if not DRY_RUN:
            doc = _upsert(
                D.StudyGroup, g.id, name=g.name, invite_code=g.invite_code,
                created_by=MAPS["user"].get(g.created_by_id), max_members=g.max_members,
                created_at=_aware(g.created_at),
            )
            MAPS["group"][g.id] = doc
        cg += 1
    cmem = cmsg = cgoal = 0
    for m in Mem.objects.all().iterator():
        if not DRY_RUN:
            _upsert(D.StudyGroupMembership, m.id, group=MAPS["group"].get(m.group_id),
                    user=MAPS["user"].get(m.user_id), role=m.role, joined_at=_aware(m.joined_at))
        cmem += 1
    for m in Msg.objects.all().iterator():
        if not DRY_RUN:
            _upsert(D.StudyGroupMessage, m.id, group=MAPS["group"].get(m.group_id),
                    sender=MAPS["user"].get(m.sender_id), text=m.text, sent_at=_aware(m.sent_at))
        cmsg += 1
    for g in Goal.objects.all().iterator():
        if not DRY_RUN:
            _upsert(D.StudyGroupGoal, g.id, group=MAPS["group"].get(g.group_id),
                    skill=MAPS["skill"].get(g.skill_id), target_date=_aware(g.target_date),
                    completed=g.completed, created_at=_aware(g.created_at))
        cgoal += 1
    logger.info("groups: %s | memberships: %s | messages: %s | goals: %s", cg, cmem, cmsg, cgoal)


def migrate_onboarding_and_adaptive():
    Onb = _get("users.OnboardingProfile")
    Adp = _get("users.AdaptiveProfile")
    AdpLog = _get("users.AdaptiveAdjustmentLog")
    Flag = _get("users.UserSkillFlag")
    co = 0
    for o in Onb.objects.all().iterator():
        if not DRY_RUN:
            _upsert(
                D.OnboardingProfile, o.id, user=MAPS["user"].get(o.user_id),
                primary_goal=o.primary_goal, target_role=o.target_role,
                experience_years=o.experience_years, category_levels=o.category_levels or {},
                selected_interests=o.selected_interests or [], weekly_hours=o.weekly_hours,
                completed_at=_aware(o.completed_at), updated_at=_aware(o.updated_at),
                path_generated=o.path_generated,
                generation_started_at=_aware(o.generation_started_at) if o.generation_started_at else None,
                generated_tree=MAPS["tree"].get(o.generated_tree_id) if o.generated_tree_id else None,
                generated_topic=o.generated_topic,
            )
        co += 1
    ca = 0
    for a in Adp.objects.all().iterator():
        if not DRY_RUN:
            doc = _upsert(
                D.AdaptiveProfile, a.id, user=MAPS["user"].get(a.user_id),
                ability_score=a.ability_score, preferred_difficulty=a.preferred_difficulty,
                last_adjusted=_aware(a.last_adjusted), created_at=_aware(a.created_at),
            )
            MAPS["adaptive_profile"][a.id] = doc
        ca += 1
    cl = 0
    for l in AdpLog.objects.all().iterator():
        if not DRY_RUN:
            _upsert(
                D.AdaptiveAdjustmentLog, l.id, profile=MAPS["adaptive_profile"].get(l.profile_id),
                ability_before=l.ability_before, ability_after=l.ability_after,
                difficulty_before=l.difficulty_before, difficulty_after=l.difficulty_after,
                reason=l.reason, quest=MAPS["quest"].get(l.quest_id) if l.quest_id else None,
                created_at=_aware(l.created_at),
            )
        cl += 1
    cf = 0
    for f in Flag.objects.all().iterator():
        if not DRY_RUN:
            _upsert(
                D.UserSkillFlag, f.id, user=MAPS["user"].get(f.user_id),
                skill=MAPS["skill"].get(f.skill_id), flag=f.flag, reason=f.reason,
                created_at=_aware(f.created_at), updated_at=_aware(f.updated_at),
            )
        cf += 1
    logger.info("onboarding: %s | adaptive_profiles: %s | adjustment_logs: %s | skill_flags: %s", co, ca, cl, cf)


def migrate_mentor():
    AI = _get("mentor.AIInteraction")
    Hint = _get("mentor.HintUsage")
    ci = 0
    for a in AI.objects.all().iterator():
        if not DRY_RUN:
            _upsert(D.AIInteraction, a.id, user=MAPS["user"].get(a.user_id),
                    interaction_type=a.interaction_type, context_prompt=a.context_prompt,
                    response=a.response, tokens_used=a.tokens_used, created_at=_aware(a.created_at))
        ci += 1
    ch = 0
    for h in Hint.objects.all().iterator():
        if not DRY_RUN:
            _upsert(D.HintUsage, h.id, user=MAPS["user"].get(h.user_id),
                    quest=MAPS["quest"].get(h.quest_id), hint_level=h.hint_level,
                    hint_text=h.hint_text, xp_penalty=h.xp_penalty, requested_at=_aware(h.requested_at))
        ch += 1
    logger.info("ai_interactions: %s | hint_usages: %s", ci, ch)


def migrate_admin_panel():
    Content = _get("admin_panel.AdminContent")
    Question = _get("admin_panel.AssessmentQuestion")
    Sub = _get("admin_panel.AssessmentSubmission")
    cc = 0
    for c in Content.objects.all().iterator():
        if not DRY_RUN:
            _upsert(D.AdminContent, c.id, skill=MAPS["skill"].get(c.skill_id),
                    content_type=c.content_type, title=c.title, body=c.body,
                    code_example=c.code_example, language=c.language, status=c.status,
                    ai_review_notes=c.ai_review_notes,
                    created_by=MAPS["user"].get(c.created_by_id) if c.created_by_id else None,
                    created_at=_aware(c.created_at), updated_at=_aware(c.updated_at))
        cc += 1
    cq = 0
    for q in Question.objects.all().iterator():
        if not DRY_RUN:
            doc = _upsert(D.AssessmentQuestion, q.id, quest=MAPS["quest"].get(q.quest_id),
                          question_type=q.question_type, prompt=q.prompt, correct_answer=q.correct_answer,
                          mcq_options=q.mcq_options or [], test_cases=q.test_cases or [],
                          validation_criteria=q.validation_criteria, language=q.language, points=q.points,
                          created_at=_aware(q.created_at), updated_at=_aware(q.updated_at))
            MAPS["assessment_question"][q.id] = doc
        cq += 1
    cs = 0
    for s in Sub.objects.all().iterator():
        if not DRY_RUN:
            _upsert(D.AssessmentSubmission, s.id, user=MAPS["user"].get(s.user_id),
                    question=MAPS["assessment_question"].get(s.question_id), answer=s.answer,
                    submitted_at=_aware(s.submitted_at),
                    evaluated_at=_aware(s.evaluated_at) if s.evaluated_at else None,
                    status=s.status, result=s.result or {}, score=s.score, passed=s.passed)
        cs += 1
    logger.info("admin_content: %s | assessment_questions: %s | assessment_submissions: %s", cc, cq, cs)


def migrate_password_reset_codes():
    Model = _get("auth_app.PasswordResetCode")
    count = 0
    for p in Model.objects.all().iterator():
        if not DRY_RUN:
            _upsert(D.PasswordResetCode, p.id, user=MAPS["user"].get(p.user_id),
                    code_hash=p.code_hash, expires_at=_aware(p.expires_at),
                    used_at=_aware(p.used_at) if p.used_at else None, created_at=_aware(p.created_at))
        count += 1
    logger.info("password_reset_codes: %s", count)


# Ordered pipeline (dependency-respecting)
PIPELINE = [
    ("users", migrate_users),
    ("badges", migrate_badges),
    ("skills", migrate_skills),
    ("skill_prereqs", migrate_skill_prereqs),
    ("trees", migrate_trees),
    ("skill_progress", migrate_skill_progress),
    ("curricula", migrate_curricula),
    ("embedding_records", migrate_embedding_records),
    ("quests", migrate_quests),
    ("submissions", migrate_submissions),
    ("shared_solutions", migrate_shared_solutions),
    ("solution_comments", migrate_solution_comments),
    ("execution_tasks", migrate_execution_tasks),
    ("evaluations", migrate_evaluations),
    ("detection_logs", migrate_detection_logs),
    ("matches", migrate_matches),
    ("leaderboard_snapshots", migrate_leaderboard_snapshots),
    ("xp_logs", migrate_xp_logs),
    ("user_badges", migrate_user_badges),
    ("weekly_reports", migrate_weekly_reports),
    ("groups", migrate_groups),
    ("onboarding_adaptive", migrate_onboarding_and_adaptive),
    ("mentor", migrate_mentor),
    ("admin_panel", migrate_admin_panel),
    ("password_reset_codes", migrate_password_reset_codes),
]


def main():
    global DRY_RUN
    parser = argparse.ArgumentParser(description="Migrate PostgreSQL data to MongoDB")
    parser.add_argument("--dry-run", action="store_true", help="Count source rows only; write nothing")
    parser.add_argument("--only", nargs="*", help="Run only the named stages")
    args = parser.parse_args()
    DRY_RUN = args.dry_run

    connect_mongo()
    logger.info("Starting migration (dry_run=%s)", DRY_RUN)

    failures = 0
    for name, fn in PIPELINE:
        if args.only and name not in args.only:
            continue
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            failures += 1
            logger.error("Stage %s FAILED: %s", name, exc, exc_info=True)

    if failures:
        logger.error("Migration finished with %s failed stage(s)", failures)
        sys.exit(1)
    logger.info("Migration completed successfully.")


if __name__ == "__main__":
    main()
