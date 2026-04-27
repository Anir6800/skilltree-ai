@echo off
REM Run tests with proper settings on Windows

set DJANGO_SETTINGS_MODULE=core.test_settings
python manage.py test %*
