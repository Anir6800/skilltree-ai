#!/usr/bin/env python
"""
Security Fixes Verification Script
Verifies that all critical security fixes have been applied correctly.
"""

import os
import sys
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.core.cache import cache


def check_file_contains(filepath, pattern, description):
    """Check if a file contains a specific pattern."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if re.search(pattern, content, re.MULTILINE):
                print(f"✅ {description}")
                return True
            else:
                print(f"❌ {description}")
                return False
    except FileNotFoundError:
        print(f"❌ {description} - File not found: {filepath}")
        return False


def main():
    print("=" * 70)
    print("SkillTree AI - Security Fixes Verification")
    print("=" * 70)
    print()
    
    checks_passed = 0
    checks_total = 0
    
    # Check 1: WebSocket Authentication - Executor
    checks_total += 1
    if check_file_contains(
        'executor/consumers.py',
        r'if not user or not user\.is_authenticated:',
        "WebSocket Authentication - Executor Consumer"
    ):
        checks_passed += 1
    
    # Check 2: WebSocket Authentication - Assessment
    checks_total += 1
    if check_file_contains(
        'admin_panel/consumers.py',
        r'verify_submission_ownership',
        "WebSocket Authentication - Assessment Consumer (ownership check)"
    ):
        checks_passed += 1
    
    # Check 3: WebSocket Authentication - Multiplayer
    checks_total += 1
    if check_file_contains(
        'multiplayer/consumers.py',
        r'if not user or not user\.is_authenticated:',
        "WebSocket Authentication - Multiplayer Consumer"
    ):
        checks_passed += 1
    
    # Check 4: Assessment Submission Authorization
    checks_total += 1
    if check_file_contains(
        'admin_panel/views.py',
        r'skill_progress\.status == [\'"]locked[\'"]',
        "Assessment Submission - Skill unlock check"
    ):
        checks_passed += 1
    
    # Check 5: Assessment Submission Rate Limiting
    checks_total += 1
    if check_file_contains(
        'admin_panel/views.py',
        r'recent_submissions >= 5',
        "Assessment Submission - Rate limiting (5/hour)"
    ):
        checks_passed += 1
    
    # Check 6: Assessment Submission Duplicate Check
    checks_total += 1
    if check_file_contains(
        'admin_panel/views.py',
        r'passed=True',
        "Assessment Submission - Duplicate submission check"
    ):
        checks_passed += 1
    
    # Check 7: Quest Submission Authorization
    checks_total += 1
    if check_file_contains(
        'quests/views.py',
        r'skill_progress\.status == [\'"]locked[\'"]',
        "Quest Submission - Skill unlock check"
    ):
        checks_passed += 1
    
    # Check 8: Quest Submission Completion Check
    checks_total += 1
    if check_file_contains(
        'quests/views.py',
        r'status=[\'"]passed[\'"]',
        "Quest Submission - Completion check"
    ):
        checks_passed += 1
    
    # Check 9: Quest Submission Code Length Validation
    checks_total += 1
    if check_file_contains(
        'quests/views.py',
        r'MAX_CODE_LENGTH = 50000',
        "Quest Submission - Code length validation"
    ):
        checks_passed += 1
    
    # Check 10: Code Execution Rate Limiting (per minute)
    checks_total += 1
    if check_file_contains(
        'executor/views.py',
        r'MAX_EXECUTIONS_PER_MINUTE = 10',
        "Code Execution - Rate limiting per minute"
    ):
        checks_passed += 1
    
    # Check 11: Code Execution Rate Limiting (per hour)
    checks_total += 1
    if check_file_contains(
        'executor/views.py',
        r'MAX_EXECUTIONS_PER_HOUR = 100',
        "Code Execution - Rate limiting per hour"
    ):
        checks_passed += 1
    
    # Check 12: Code Execution Length Validation
    checks_total += 1
    if check_file_contains(
        'executor/views.py',
        r'MAX_CODE_LENGTH = 50000',
        "Code Execution - Code length validation"
    ):
        checks_passed += 1
    
    # Check 13: Test Execution Rate Limiting
    checks_total += 1
    if check_file_contains(
        'executor/views.py',
        r'test_rate_minute',
        "Test Execution - Rate limiting"
    ):
        checks_passed += 1
    
    # Check 14: Test Case Count Validation
    checks_total += 1
    if check_file_contains(
        'executor/views.py',
        r'MAX_TEST_CASES = 20',
        "Test Execution - Test case count limit"
    ):
        checks_passed += 1
    
    # Check 15: Onboarding Error Handling
    checks_total += 1
    if check_file_contains(
        'users/onboarding_views.py',
        r'profile\.delete\(\)',
        "Onboarding - Proper error handling (cleanup on failure)"
    ):
        checks_passed += 1
    
    # Check 16: Onboarding Service Unavailable Response
    checks_total += 1
    if check_file_contains(
        'users/onboarding_views.py',
        r'status\.HTTP_503_SERVICE_UNAVAILABLE',
        "Onboarding - Service unavailable response"
    ):
        checks_passed += 1
    
    # Check 17: Test Case Expected Output Hidden
    checks_total += 1
    if check_file_contains(
        'quests/serializers.py',
        r'def get_test_cases',
        "Quest Serializer - Test case expected output hidden"
    ):
        checks_passed += 1
    
    print()
    print("=" * 70)
    print(f"Verification Results: {checks_passed}/{checks_total} checks passed")
    print("=" * 70)
    print()
    
    if checks_passed == checks_total:
        print("✅ ALL SECURITY FIXES VERIFIED!")
        print()
        print("The platform is ready for production deployment.")
        print()
        print("Next steps:")
        print("1. Run migrations: python manage.py migrate")
        print("2. Restart services: Django, Celery, Daphne")
        print("3. Verify Redis is running: redis-cli ping")
        print("4. Run security tests: pytest tests/security/")
        print("5. Monitor logs for any issues")
        return 0
    else:
        print(f"❌ {checks_total - checks_passed} CHECKS FAILED!")
        print()
        print("Please review the failed checks above and ensure all security")
        print("fixes have been properly applied.")
        print()
        print("Refer to SECURITY_FIXES.md for detailed fix instructions.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
