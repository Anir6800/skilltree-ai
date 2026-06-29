"""
Optional, non-breaking MongoEngine bootstrap.

This is intentionally NOT imported by core/settings.py so that the existing
Django app keeps booting even if mongoengine isn't installed yet. Wire it at
cutover from one of:

  • core/asgi.py / core/wsgi.py  (add after get_asgi_application()):
        from mongo.bootstrap import init_mongo_if_enabled
        init_mongo_if_enabled()

  • or an AppConfig.ready() of a small 'mongo' Django app.

Controlled by env var USE_MONGODB (default False) so it is a safe no-op until
you flip the flag.
"""

import os
import logging

logger = logging.getLogger(__name__)


def init_mongo_if_enabled():
    if os.getenv("USE_MONGODB", "False").lower() != "true":
        logger.debug("USE_MONGODB is not enabled; skipping Mongo bootstrap.")
        return False
    try:
        from .connection import connect_mongo
        connect_mongo()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Mongo bootstrap failed: %s", exc, exc_info=True)
        return False
