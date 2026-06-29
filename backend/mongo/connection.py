"""
MongoEngine connection management.

A single global connection ("default" alias) is used by all documents.
Configuration is read from environment variables so it works both inside
Django (settings import os.environ) and from standalone scripts (ETL, cron).

Environment variables (see .env.example):
    MONGODB_URI   Full connection string. Examples:
                    mongodb://localhost:27017
                    mongodb+srv://user:pass@cluster0.xxx.mongodb.net
    MONGODB_DB    Database name (default: skilltree_ai)

Usage:
    from mongo import connect_mongo
    connect_mongo()          # idempotent; safe to call more than once
"""

import os
import logging

import mongoengine

logger = logging.getLogger(__name__)

DEFAULT_ALIAS = "default"
_connected = False


def connect_mongo(alias: str = DEFAULT_ALIAS):
    """
    Establish the global MongoEngine connection. Idempotent.

    Returns the pymongo MongoClient-backed connection object.
    """
    global _connected

    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB", "skilltree_ai")

    if _connected:
        return mongoengine.get_connection(alias)

    # `connect` accepts a full host URI; the db kwarg sets the default database.
    conn = mongoengine.connect(
        db=db_name,
        host=uri,
        alias=alias,
        # Fail fast instead of hanging if Mongo is unreachable.
        serverSelectionTimeoutMS=int(os.getenv("MONGODB_TIMEOUT_MS", "5000")),
        uuidRepresentation="standard",
        tz_aware=True,
    )
    _connected = True
    logger.info("Connected to MongoDB db=%s alias=%s", db_name, alias)
    return conn


def disconnect_mongo(alias: str = DEFAULT_ALIAS):
    """Tear down the connection (used by tests / scripts)."""
    global _connected
    try:
        mongoengine.disconnect(alias=alias)
    finally:
        _connected = False


def get_db(alias: str = DEFAULT_ALIAS):
    """Return the underlying pymongo Database object."""
    return mongoengine.connection.get_db(alias)
