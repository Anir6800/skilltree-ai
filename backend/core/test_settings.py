"""
Test Settings for SkillTree AI
Uses in-memory SQLite database and disables external services for testing.
"""

from .settings import *

# ─── Database ────────────────────────────────────────────────────────────────
# Use in-memory SQLite for tests (no file I/O, no permission issues)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# ─── Channels ────────────────────────────────────────────────────────────────
# Use in-memory channel layer for tests (no Redis required)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

# ─── Celery ──────────────────────────────────────────────────────────────────
# Run Celery tasks synchronously for tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ─── Email ───────────────────────────────────────────────────────────────────
# Use console email backend for tests
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ─── Logging ─────────────────────────────────────────────────────────────────
# Suppress logging during tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'level': 'DEBUG',
        },
    },
}

# ─── Password Validation ──────────────────────────────────────────────────────
# Disable password validation for faster tests
AUTH_PASSWORD_VALIDATORS = []

# ─── Security ────────────────────────────────────────────────────────────────
# Disable security checks for tests
DEBUG = True
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
