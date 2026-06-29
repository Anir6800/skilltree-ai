"""
SkillTree AI — MongoEngine persistence layer
=============================================
This package is the MongoDB (MongoEngine ODM) replacement for the Django ORM
models, created during the PostgreSQL -> MongoDB migration.

It is intentionally a *parallel* layer: the legacy Django ORM models remain in
place until cutover so that:
  1. the data-migration ETL can READ from PostgreSQL via the Django ORM, and
  2. the application keeps running while views/serializers are ported.

Public surface:
    from mongo import connect_mongo, documents, auth

See ../../mongodb_migration_report.md for the full migration plan, cutover
checklist, and rollback procedure.
"""

from .connection import connect_mongo, disconnect_mongo, get_db  # noqa: F401

__all__ = ["connect_mongo", "disconnect_mongo", "get_db"]
