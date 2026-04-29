"""
Destructive, deterministic reset/rebuild for SkillTree AI.

This command is intentionally guarded. It clears the application database,
runtime caches, queues, websocket/channel state, local AI/vector runtime state,
and then rebuilds the schema from migrations and seeds the base catalogue.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction


class Command(BaseCommand):
    help = "Reset PostgreSQL/SQLite, Redis runtime state, local AI cache, then migrate, seed, and validate."

    def add_arguments(self, parser):
        parser.add_argument("--confirm", action="store_true", help="Required confirmation for destructive reset.")
        parser.add_argument("--no-input", action="store_true", help="Do not prompt before running.")
        parser.add_argument(
            "--allow-production",
            action="store_true",
            help="Allow reset when DEBUG=False. Use only in disposable environments.",
        )
        parser.add_argument(
            "--skip-schema-rebuild",
            action="store_true",
            help="Use Django flush instead of dropping/recreating the database schema.",
        )
        parser.add_argument("--skip-runtime-clean", action="store_true", help="Do not clear Redis/local runtime files.")
        parser.add_argument(
            "--skip-redis-validation",
            action="store_true",
            help="Validate database/schema only after reset. Use when Redis is intentionally offline.",
        )
        parser.add_argument(
            "--strict-runtime-validation",
            action="store_true",
            help="Fail the reset when Redis/cache runtime validation reports warnings.",
        )
        parser.add_argument("--skip-seed", action="store_true", help="Do not run seed_all after migrations.")
        parser.add_argument("--with-demo-users", action="store_true", help="Create demo users after seeding.")
        parser.add_argument(
            "--admin-email",
            default=os.getenv("RESET_ADMIN_EMAIL", "admin@skilltree.ai"),
            help="Admin email to create/update after reset.",
        )
        parser.add_argument(
            "--admin-password",
            default=os.getenv("RESET_ADMIN_PASSWORD", "Admin1234!"),
            help="Admin password to set after reset.",
        )

    def handle(self, *args, **options):
        self._guard(options)
        self._print_reset_scope(options)

        if not options["no_input"]:
            input("Type Enter to permanently reset this local system, or Ctrl+C to abort: ")

        report = {
            "database": "not started",
            "migrations": "not started",
            "runtime": "not started",
            "seed": "not started",
            "admin": "not started",
            "validation": "not started",
        }

        try:
            if options["skip_schema_rebuild"]:
                self._flush_database()
                report["database"] = "flushed with schema preserved"
            else:
                self._rebuild_database_schema()
                report["database"] = "schema dropped and recreated"

            call_command("migrate", interactive=False, verbosity=1)
            report["migrations"] = "applied"

            if options["skip_runtime_clean"]:
                report["runtime"] = "skipped"
            else:
                runtime_report = self._clean_runtime_state()
                report["runtime"] = runtime_report

            if options["skip_seed"]:
                report["seed"] = "skipped"
            else:
                call_command("seed_all", verbosity=1)
                report["seed"] = "seed_all complete"

            self._create_or_update_admin(options["admin_email"], options["admin_password"])
            report["admin"] = f"admin ready: {options['admin_email']}"

            if options["with_demo_users"]:
                self._create_demo_users()

            call_command(
                "validate_system_state",
                strict=options["strict_runtime_validation"],
                skip_redis=options["skip_redis_validation"],
                verbosity=1,
            )
            report["validation"] = "passed"
        except Exception as exc:
            self._print_report(report, failed=True)
            raise CommandError(f"Full reset failed: {exc}") from exc

        self._print_report(report, failed=False)

    def _guard(self, options):
        if not options["confirm"]:
            raise CommandError("Refusing to reset. Re-run with --confirm.")
        if not settings.DEBUG and not options["allow_production"]:
            raise CommandError("Refusing to reset with DEBUG=False. Add --allow-production only for disposable systems.")

    def _print_reset_scope(self, options):
        database = connection.settings_dict.get("NAME", "")
        self.stdout.write(self.style.WARNING("FULL SYSTEM RESET"))
        self.stdout.write(f"Database vendor: {connection.vendor}")
        self.stdout.write(f"Database name:   {database}")
        self.stdout.write(f"Redis URL:       {getattr(settings, 'REDIS_URL', '')}")
        self.stdout.write(f"Chroma path:     {getattr(settings, 'CHROMA_PATH', '')}")
        self.stdout.write(f"Schema rebuild:  {not options['skip_schema_rebuild']}")
        self.stdout.write(f"Seed base data:  {not options['skip_seed']}")

    def _rebuild_database_schema(self):
        self.stdout.write(self.style.MIGRATE_HEADING("Rebuilding database schema..."))
        vendor = connection.vendor

        if vendor == "postgresql":
            with connection.cursor() as cursor:
                cursor.execute("DROP SCHEMA IF EXISTS public CASCADE;")
                cursor.execute("CREATE SCHEMA public;")
                cursor.execute("GRANT ALL ON SCHEMA public TO public;")
                db_user = connection.settings_dict.get("USER")
                if db_user:
                    cursor.execute(f'GRANT ALL ON SCHEMA public TO "{db_user}";')
            connection.close()
            return

        if vendor == "sqlite":
            db_name = connection.settings_dict.get("NAME")
            connection.close()
            if db_name and db_name != ":memory:":
                db_path = Path(db_name)
                if db_path.exists():
                    db_path.unlink()
            return

        raise CommandError(f"Unsupported schema rebuild for database vendor: {vendor}")

    def _flush_database(self):
        self.stdout.write(self.style.MIGRATE_HEADING("Flushing database rows..."))
        call_command("flush", interactive=False, verbosity=1)

    def _clean_runtime_state(self):
        self.stdout.write(self.style.MIGRATE_HEADING("Cleaning runtime state..."))
        report = {}
        report["redis"] = self._flush_redis_databases()
        report["local_files"] = self._clear_local_runtime_paths()
        return report

    def _flush_redis_databases(self):
        urls = {
            getattr(settings, "REDIS_URL", ""),
            getattr(settings, "CELERY_BROKER_URL", ""),
            getattr(settings, "CELERY_RESULT_BACKEND", ""),
        }
        cleaned = []
        skipped = []

        for url in sorted(filter(None, urls)):
            if not url.startswith("redis://") and not url.startswith("rediss://"):
                skipped.append(f"{url}: unsupported")
                continue
            try:
                import redis

                client = redis.Redis.from_url(url)
                client.flushdb()
                parsed = urlparse(url)
                cleaned.append(f"{parsed.hostname}:{parsed.port or 6379}/{(parsed.path or '/0').lstrip('/')}")
            except Exception as exc:
                skipped.append(f"{url}: {exc}")

        for item in cleaned:
            self.stdout.write(self.style.SUCCESS(f"  cleared Redis DB {item}"))
        for item in skipped:
            self.stdout.write(self.style.WARNING(f"  Redis cleanup skipped: {item}"))
        return {"cleaned": cleaned, "skipped": skipped}

    def _clear_local_runtime_paths(self):
        paths = []
        chroma_path = Path(getattr(settings, "CHROMA_PATH", "") or "chroma_db")
        if not chroma_path.is_absolute():
            chroma_path = Path(settings.BASE_DIR) / chroma_path
        paths.append(chroma_path)

        media_root = Path(settings.MEDIA_ROOT)
        paths.extend([media_root / "reports", media_root / "uploads"])

        temp_root = Path(os.environ.get("TEMP", "C:\\temp" if sys.platform == "win32" else "/tmp"))
        paths.append(temp_root / "skilltree")

        paths.extend(Path(settings.BASE_DIR).glob("celerybeat-schedule*"))

        cleared = []
        for path in paths:
            try:
                if path.is_file():
                    path.unlink()
                    cleared.append(str(path))
                elif path.is_dir():
                    shutil.rmtree(path)
                    path.mkdir(parents=True, exist_ok=True)
                    cleared.append(str(path))
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"  Could not clear {path}: {exc}"))

        for item in cleared:
            self.stdout.write(self.style.SUCCESS(f"  cleared {item}"))
        return cleared

    def _create_or_update_admin(self, email, password):
        User = get_user_model()
        username = email.split("@", 1)[0] or "admin"
        with transaction.atomic():
            user, _ = User.objects.update_or_create(
                email=email,
                defaults={
                    "username": username,
                    "is_staff": True,
                    "is_superuser": True,
                    "role": "admin",
                    "xp": 0,
                    "streak_days": 0,
                    "last_active": None,
                },
            )
            user.set_password(password)
            user.save()
        self.stdout.write(self.style.SUCCESS(f"Admin account ready: {email}"))

    def _create_demo_users(self):
        User = get_user_model()
        for email, username in [
            ("student@skilltree.ai", "student"),
            ("demo@skilltree.ai", "demo"),
        ]:
            user, _ = User.objects.update_or_create(
                email=email,
                defaults={"username": username, "is_staff": False, "is_superuser": False, "role": "student"},
            )
            user.set_password("Demo1234!")
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Demo user ready: {email}"))

    def _print_report(self, report, failed):
        status = "FAILED" if failed else "COMPLETE"
        style = self.style.ERROR if failed else self.style.SUCCESS
        self.stdout.write(style(f"\nSYSTEM RESET {status}"))
        for key, value in report.items():
            self.stdout.write(f"- {key}: {value}")
        if not failed:
            counts = self._model_counts()
            self.stdout.write("- cleanup report:")
            for label, count in counts.items():
                self.stdout.write(f"  {label}: {count}")

    def _model_counts(self):
        wanted = [
            ("users.User", "users"),
            ("skills.Skill", "skills"),
            ("skills.SkillPrerequisite", "skill prerequisites"),
            ("quests.Quest", "quests"),
            ("users.Badge", "badges"),
            ("quests.QuestSubmission", "quest submissions"),
            ("skills.SkillProgress", "skill progress"),
            ("users.OnboardingProfile", "onboarding profiles"),
            ("users.UserBadge", "earned badges"),
            ("multiplayer.Match", "matches"),
        ]
        counts = {}
        for model_label, label in wanted:
            model = apps.get_model(model_label)
            counts[label] = model.objects.count()
        return counts
