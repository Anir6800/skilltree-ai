#!/bin/bash
# Run tests with proper settings

export DJANGO_SETTINGS_MODULE=core.test_settings
python manage.py test "$@"
