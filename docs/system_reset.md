# SkillTree AI System Reset

This reset path is destructive and intended for local/disposable environments where database, progression, onboarding, AI content, queues, websocket state, and runtime cache must be rebuilt from scratch.

## Reset Command

PowerShell wrapper:

```powershell
.\scripts\reset_system_state.ps1 -Confirm -NoInput
```

By default, unavailable Redis is reported as a validation warning but does not fail a completed database rebuild. If Redis is intentionally offline and you want to hide Redis validation entirely:

```powershell
.\scripts\reset_system_state.ps1 -Confirm -NoInput -SkipRedisValidation
```

Direct Django command:

```powershell
cd backend
python manage.py full_reset --confirm --no-input
```

## What It Clears

- PostgreSQL `public` schema, or the local SQLite database file.
- Redis DBs referenced by `REDIS_URL`, `CELERY_BROKER_URL`, and `CELERY_RESULT_BACKEND`.
- Django cache, Channels websocket group state, Celery queues/results, leaderboard sorted sets, and rate-limit keys through Redis DB flushes.
- ChromaDB runtime directory from `CHROMA_PATH`.
- Weekly report/upload media folders.
- Celery beat schedule files.
- Executor sandbox temp directory.
- User progression, onboarding, adaptive state, quest submissions, earned badges, arena/matchmaking records, AI evaluation records, detection logs, mentor hints, leaderboard snapshots, study groups, and generated skill trees through schema rebuild.

## What It Rebuilds

- Runs all Django migrations from a clean schema.
- Runs `seed_all` for base skills, prerequisites, quests, and badge definitions.
- Recreates a system admin account.

Defaults:

```env
RESET_ADMIN_EMAIL=admin@skilltree.ai
RESET_ADMIN_PASSWORD=Admin1234!
```

Override those environment variables before running the reset if needed.

## Validation Command

```powershell
cd backend
python manage.py validate_system_state --strict
```

For database-only validation while Redis is offline:

```powershell
python manage.py validate_system_state --strict --skip-redis
```

The validation report checks:

- all migrations are applied;
- all managed model tables exist;
- skills, prerequisites, quests, and badges are seeded;
- progression/onboarding/runtime DB tables are empty after reset;
- core FK relations are valid;
- Redis DBs are empty when Redis validation is enabled.

To make Redis/cache warnings fail the reset command, run the Django command directly with:

```powershell
python manage.py full_reset --confirm --no-input --strict-runtime-validation
```

## Failure Handling

- Missing `--confirm` aborts before any destructive operation.
- `DEBUG=False` aborts unless `--allow-production` is explicitly provided.
- Migration, seed, or validation failure stops the command and prints the stage report.
- If migrations fail after schema rebuild, rerun the command after fixing migrations. The next run starts from a clean schema again.
- Stop Django, Celery workers, Celery beat, and websocket consumers before reset so they cannot repopulate Redis or write rows during rebuild.
- If `chroma.sqlite3` is locked on Windows, stop any Python/Django process using ChromaDB and rerun the reset. The database rebuild still completes, but that local vector-cache directory cannot be deleted while locked.
