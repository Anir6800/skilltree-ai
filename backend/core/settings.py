import os
from pathlib import Path
from datetime import timedelta
import dj_database_url
from dotenv import load_dotenv

# Load environment variables from .env file at the top
load_dotenv()

# [Paths]
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# [Security]
# SECRET_KEY is loaded from environment; MUST be long and random in production.
SECRET_KEY = os.getenv('SECRET_KEY', 'django-skilltree-ai-immersive-platform-v1-production-ready-key-replace-this')

# DEBUG mode is controlled via environment variable. 
# WARNING: NEVER run with DEBUG=True in a production environment.
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# ALLOWED_HOSTS is a list of host/domain names that this Django site can serve.
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# [Security Policy for Production]
# These settings follow the .env configuration
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False').lower() == 'true'

if not DEBUG and SECURE_SSL_REDIRECT:
    # HTTP Strict Transport Security (HSTS)
    # Set to 1 year (31536000 seconds)
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Trust the X-Forwarded-Proto header from the proxy (e.g. Nginx, Load Balancer)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # Browser security headers
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

# [Auth User Model]
# SkillTree AI uses a custom User model for immersive profile and XP tracking.
AUTH_USER_MODEL = 'users.User'

# [Application Definition]
INSTALLED_APPS = [
    # ASGI server for Channels
    'daphne',
    'channels',
    
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party extensions
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    
    # SkillTree AI Custom Apps
    'auth_app',
    'skills',
    'quests',
    'executor',
    'ai_evaluation',
    'ai_detection',
    'multiplayer',
    'leaderboard',
    'users',
    'mentor',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', # Must be at the top
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

# [Database]
# PostgreSQL configuration via DATABASE_URL. Falls back to sqlite for safety if missing.
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL', 'sqlite:///db.sqlite3'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# [Redis & Channels]
# REDIS_URL is used for Channels layers and Celery tasks.
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
    },
}

# [Celery]
# Async task processing for AI evaluation and skill tree updates.
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = os.getenv('TIME_ZONE', 'UTC')

# [REST Framework]
# Global settings for SkillTree AI APIs.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# [Simple JWT]
# Configurable token lifetimes for immersive session management.
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv('JWT_ACCESS_LIFETIME_MINUTES', 60))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('JWT_REFRESH_LIFETIME_DAYS', 7))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# [CORS]
# Allowed origins defined via environment variable (comma-separated).
CORS_ALLOWED_ORIGINS = [
    origin.strip() 
    for origin in os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',') 
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = os.getenv('CORS_ALLOW_CREDENTIALS', 'True').lower() == 'true'

# [CSRF]
# Required for Django 4.0+ to allow cross-origin POST requests
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# [Password Validation]
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# [Internationalization]
LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('TIME_ZONE', 'Asia/Kolkata')
USE_I18N = True
USE_TZ = os.getenv('USE_TZ', 'True').lower() == 'true'

# [Static & Media]
# Static files (CSS, JavaScript, Images) and User-uploaded media.
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# [Default Primary Key]
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# [SkillTree AI Integration Settings]
# These settings are used by the AI Evaluation and Docker Executor services.
LM_STUDIO_URL = os.getenv('LM_STUDIO_URL', 'http://localhost:1234/v1')
LM_STUDIO_MODEL = os.getenv('LM_STUDIO_MODEL', 'openai/gpt-oss-20b')
CHROMA_PATH = os.getenv('CHROMA_PATH', './chroma_db')

EXECUTION_TIMEOUT = int(os.getenv('EXECUTION_TIMEOUT_SECONDS', 10))
EXECUTION_MEMORY = int(os.getenv('EXECUTION_MEMORY_MB', 128))
EXECUTION_CPU_QUOTA = int(os.getenv('EXECUTION_CPU_QUOTA', 50000))

# [Email]
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 1025))
