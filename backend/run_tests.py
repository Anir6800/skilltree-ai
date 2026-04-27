#!/usr/bin/env python
"""
Simple test runner for AI Detection Flagging Workflow
Runs tests without requiring database creation
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False, keepdb=False)
    
    # Run specific test module
    failures = test_runner.run_tests(["ai_detection.test_flagging_workflow"])
    
    sys.exit(bool(failures))
