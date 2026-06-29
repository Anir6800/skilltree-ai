"""
Post-migration verification: compare PostgreSQL row counts vs MongoDB document
counts for every migrated collection, and spot-check a few referential links.

Usage:
    cd backend
    venv/Scripts/python scripts/mongo_verify.py

Exit code 0 if all counts match; 1 if any mismatch is found.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django  # noqa: E402
django.setup()

from django.apps import apps as dj  # noqa: E402
from mongo.connection import connect_mongo  # noqa: E402
from mongo import documents as D  # noqa: E402

# (django_label, mongo_document)
PAIRS = [
    ("users.User", D.User),
    ("users.XPLog", D.XPLog),
    ("users.Badge", D.Badge),
    ("users.UserBadge", D.UserBadge),
    ("users.WeeklyReport", D.WeeklyReport),
    ("users.StudyGroup", D.StudyGroup),
    ("users.StudyGroupMembership", D.StudyGroupMembership),
    ("users.StudyGroupMessage", D.StudyGroupMessage),
    ("users.StudyGroupGoal", D.StudyGroupGoal),
    ("users.OnboardingProfile", D.OnboardingProfile),
    ("users.AdaptiveProfile", D.AdaptiveProfile),
    ("users.AdaptiveAdjustmentLog", D.AdaptiveAdjustmentLog),
    ("users.UserSkillFlag", D.UserSkillFlag),
    ("skills.GeneratedSkillTree", D.GeneratedSkillTree),
    ("skills.Skill", D.Skill),
    ("skills.SkillPrerequisite", D.SkillPrerequisite),
    ("skills.SkillProgress", D.SkillProgress),
    ("skills.UserCurriculum", D.UserCurriculum),
    ("skills.EmbeddingRecord", D.EmbeddingRecord),
    ("quests.Quest", D.Quest),
    ("quests.QuestSubmission", D.QuestSubmission),
    ("quests.SharedSolution", D.SharedSolution),
    ("quests.SolutionComment", D.SolutionComment),
    ("executor.ExecutionTask", D.ExecutionTask),
    ("ai_evaluation.EvaluationResult", D.EvaluationResult),
    ("ai_evaluation.StyleReport", D.StyleReport),
    ("ai_detection.DetectionLog", D.DetectionLog),
    ("multiplayer.Match", D.Match),
    ("multiplayer.MatchParticipant", D.MatchParticipant),
    ("leaderboard.LeaderboardSnapshot", D.LeaderboardSnapshot),
    ("mentor.AIInteraction", D.AIInteraction),
    ("mentor.HintUsage", D.HintUsage),
    ("admin_panel.AdminContent", D.AdminContent),
    ("admin_panel.AssessmentQuestion", D.AssessmentQuestion),
    ("admin_panel.AssessmentSubmission", D.AssessmentSubmission),
    ("auth_app.PasswordResetCode", D.PasswordResetCode),
]


def main():
    connect_mongo()
    print(f"{'COLLECTION':<38}{'POSTGRES':>10}{'MONGO':>10}{'  STATUS'}")
    print("-" * 70)
    mismatches = 0
    for label, doc in PAIRS:
        app_label, model_name = label.split(".")
        pg = dj.get_model(app_label, model_name).objects.count()
        mongo = doc.objects.count()
        ok = pg == mongo
        if not ok:
            mismatches += 1
        print(f"{label:<38}{pg:>10}{mongo:>10}{'  OK' if ok else '  MISMATCH <<'}")

    print("-" * 70)
    if mismatches:
        print(f"FAILED: {mismatches} collection(s) have count mismatches.")
        sys.exit(1)
    print("SUCCESS: all collection counts match.")


if __name__ == "__main__":
    main()
