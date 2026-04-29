"""
Validate SkillTree AI after a reset/rebuild.

The checks intentionally cover schema, seed data, progression state,
AI/runtime state references, and Redis cache/queue residue.
"""

from __future__ import annotations

from urllib.parse import urlparse

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


class Command(BaseCommand):
    help = "Validate reset schema, base seed data, progression tables, and Redis runtime state."

    def add_arguments(self, parser):
        parser.add_argument("--strict", action="store_true", help="Fail on warnings as well as errors.")
        parser.add_argument("--skip-redis", action="store_true", help="Do not inspect Redis cache/queue state.")

    def handle(self, *args, **options):
        checks = []
        checks.extend(self._check_migrations())
        checks.extend(self._check_tables())
        checks.extend(self._check_seed_data())
        checks.extend(self._check_progression_cleanliness())
        checks.extend(self._check_model_relations())
        if not options["skip_redis"]:
            checks.extend(self._check_redis_state())

        errors = [check for check in checks if check["level"] == "error"]
        warnings = [check for check in checks if check["level"] == "warning"]

        self.stdout.write(self.style.MIGRATE_HEADING("Schema validation report"))
        for check in checks:
            style = self.style.SUCCESS
            if check["level"] == "warning":
                style = self.style.WARNING
            if check["level"] == "error":
                style = self.style.ERROR
            self.stdout.write(style(f"[{check['level'].upper()}] {check['name']}: {check['detail']}"))

        if errors or (options["strict"] and warnings):
            raise CommandError(f"Validation failed: {len(errors)} errors, {len(warnings)} warnings")

        self.stdout.write(self.style.SUCCESS("Validation passed. Schema, seed data, and reset state are aligned."))

    def _ok(self, name, detail):
        return {"level": "ok", "name": name, "detail": detail}

    def _warning(self, name, detail):
        return {"level": "warning", "name": name, "detail": detail}

    def _error(self, name, detail):
        return {"level": "error", "name": name, "detail": detail}

    def _check_migrations(self):
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if plan:
            pending = ", ".join(f"{migration.app_label}.{migration.name}" for migration, _ in plan[:10])
            return [self._error("migrations", f"{len(plan)} pending migrations: {pending}")]
        return [self._ok("migrations", "all migrations applied")]

    def _check_tables(self):
        existing = set(connection.introspection.table_names())
        missing = []
        for model in apps.get_models():
            if model._meta.managed and model._meta.db_table not in existing:
                missing.append(model._meta.db_table)
        if missing:
            return [self._error("tables", f"missing managed tables: {', '.join(sorted(missing))}")]
        return [self._ok("tables", f"{len(existing)} tables visible to Django")]

    def _check_seed_data(self):
        Skill = apps.get_model("skills", "Skill")
        SkillPrerequisite = apps.get_model("skills", "SkillPrerequisite")
        Quest = apps.get_model("quests", "Quest")
        Badge = apps.get_model("users", "Badge")

        results = []
        results.append(self._ok("skills", f"{Skill.objects.count()} seeded") if Skill.objects.exists() else self._error("skills", "no skills seeded"))
        results.append(
            self._ok("skill prerequisites", f"{SkillPrerequisite.objects.count()} linked")
            if SkillPrerequisite.objects.exists()
            else self._warning("skill prerequisites", "no prerequisite edges found")
        )
        results.append(self._ok("quests", f"{Quest.objects.count()} seeded") if Quest.objects.exists() else self._error("quests", "no quests seeded"))
        results.append(self._ok("badges", f"{Badge.objects.count()} seeded") if Badge.objects.exists() else self._error("badges", "no badges seeded"))
        return results

    def _check_progression_cleanliness(self):
        expected_empty = [
            ("quests.QuestSubmission", "quest completion/submission state"),
            ("executor.ExecutionTask", "execution task state"),
            ("ai_evaluation.EvaluationResult", "AI evaluation cache records"),
            ("ai_evaluation.StyleReport", "style report records"),
            ("ai_detection.DetectionLog", "AI detection records"),
            ("mentor.AIInteraction", "mentor interaction records"),
            ("mentor.HintUsage", "hint usage records"),
            ("multiplayer.Match", "arena/matchmaking state"),
            ("multiplayer.MatchParticipant", "arena participant state"),
            ("leaderboard.LeaderboardSnapshot", "leaderboard snapshots"),
            ("skills.SkillProgress", "user skill progression"),
            ("skills.UserCurriculum", "user curriculum state"),
            ("skills.GeneratedSkillTree", "AI-generated skill trees"),
            ("users.XPLog", "XP log state"),
            ("users.UserBadge", "earned badge state"),
            ("users.OnboardingProfile", "onboarding state"),
            ("users.AdaptiveProfile", "adaptive progression state"),
            ("users.UserSkillFlag", "adaptive skill flags"),
            ("users.WeeklyReport", "weekly reports"),
            ("users.StudyGroup", "study groups"),
        ]

        results = []
        for model_label, label in expected_empty:
            model = apps.get_model(model_label)
            count = model.objects.count()
            if count:
                results.append(self._warning(label, f"{count} records present after reset"))
            else:
                results.append(self._ok(label, "empty"))
        return results

    def _check_model_relations(self):
        checks = []
        checks.extend(self._check_no_null_fk("quests.Quest", "skill", "quest-skill relation"))
        checks.extend(self._check_no_null_fk("skills.SkillPrerequisite", "from_skill", "prerequisite source relation"))
        checks.extend(self._check_no_null_fk("skills.SkillPrerequisite", "to_skill", "prerequisite target relation"))
        checks.extend(self._check_no_null_fk("admin_panel.AssessmentQuestion", "quest", "assessment-question relation"))
        return checks

    def _check_no_null_fk(self, model_label, field_name, check_name):
        model = apps.get_model(model_label)
        query = {f"{field_name}__isnull": True}
        count = model.objects.filter(**query).count()
        if count:
            return [self._error(check_name, f"{count} rows have null {field_name}")]
        return [self._ok(check_name, "valid")]

    def _check_redis_state(self):
        urls = {
            getattr(settings, "REDIS_URL", ""),
            getattr(settings, "CELERY_BROKER_URL", ""),
            getattr(settings, "CELERY_RESULT_BACKEND", ""),
        }
        results = []
        for url in sorted(filter(None, urls)):
            if not url.startswith("redis://") and not url.startswith("rediss://"):
                continue
            try:
                import redis

                client = redis.Redis.from_url(url)
                db_size = client.dbsize()
                parsed = urlparse(url)
                label = f"Redis {parsed.hostname}:{parsed.port or 6379}/{(parsed.path or '/0').lstrip('/')}"
                if db_size:
                    sample = [key.decode("utf-8", "replace") for key in client.scan_iter(count=10)]
                    results.append(self._warning(label, f"{db_size} keys remain; sample={sample[:10]}"))
                else:
                    results.append(self._ok(label, "empty"))
            except Exception as exc:
                results.append(self._warning("Redis", f"unavailable: {exc}"))
        return results
