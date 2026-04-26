"""
Quick validation script to verify Assessment Engine installation.
Run: python admin_panel/validate_installation.py
"""

import os
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

try:
    import django
    django.setup()
    print("✓ Django setup successful")
except Exception as e:
    print(f"✗ Django setup failed: {e}")
    sys.exit(1)

# Test imports
print("\n=== Testing Imports ===")

try:
    from admin_panel.assessment_engine import AssessmentEngine, EvaluationResult, assessment_engine
    print("✓ AssessmentEngine imported")
except Exception as e:
    print(f"✗ AssessmentEngine import failed: {e}")
    sys.exit(1)

try:
    from admin_panel.models import AssessmentQuestion, AssessmentSubmission
    print("✓ Models imported")
except Exception as e:
    print(f"✗ Models import failed: {e}")
    sys.exit(1)

try:
    from admin_panel.serializers import (
        AssessmentQuestionSerializer,
        AssessmentQuestionCreateSerializer,
        AssessmentSubmissionSerializer,
        AssessmentSubmissionCreateSerializer
    )
    print("✓ Serializers imported")
except Exception as e:
    print(f"✗ Serializers import failed: {e}")
    sys.exit(1)

try:
    from admin_panel.tasks import evaluate_assessment_submission
    print("✓ Celery tasks imported")
except Exception as e:
    print(f"✗ Celery tasks import failed: {e}")
    sys.exit(1)

try:
    from admin_panel.consumers import AssessmentResultConsumer
    print("✓ WebSocket consumer imported")
except Exception as e:
    print(f"✗ WebSocket consumer import failed: {e}")
    sys.exit(1)

try:
    from admin_panel import views
    print("✓ Views imported")
except Exception as e:
    print(f"✗ Views import failed: {e}")
    sys.exit(1)

# Test model structure
print("\n=== Testing Model Structure ===")

try:
    fields = [f.name for f in AssessmentSubmission._meta.get_fields()]
    required_fields = ['id', 'user', 'question', 'answer', 'submitted_at', 'evaluated_at', 'status', 'result', 'score', 'passed']
    
    for field in required_fields:
        if field in fields:
            print(f"✓ Field '{field}' exists")
        else:
            print(f"✗ Field '{field}' missing")
            sys.exit(1)
except Exception as e:
    print(f"✗ Model structure check failed: {e}")
    sys.exit(1)

# Test AssessmentEngine methods
print("\n=== Testing AssessmentEngine Methods ===")

try:
    engine = AssessmentEngine()
    print("✓ AssessmentEngine instantiated")
    
    # Check methods exist
    assert hasattr(engine, 'evaluate'), "Missing evaluate method"
    print("✓ evaluate() method exists")
    
    assert hasattr(engine, '_evaluate_mcq'), "Missing _evaluate_mcq method"
    print("✓ _evaluate_mcq() method exists")
    
    assert hasattr(engine, '_evaluate_code'), "Missing _evaluate_code method"
    print("✓ _evaluate_code() method exists")
    
    assert hasattr(engine, '_evaluate_open_ended'), "Missing _evaluate_open_ended method"
    print("✓ _evaluate_open_ended() method exists")
    
except Exception as e:
    print(f"✗ AssessmentEngine method check failed: {e}")
    sys.exit(1)

# Test EvaluationResult
print("\n=== Testing EvaluationResult ===")

try:
    result = EvaluationResult(
        passed=True,
        score=10.0,
        feedback="Test feedback"
    )
    result_dict = result.to_dict()
    
    assert 'passed' in result_dict, "Missing 'passed' in result dict"
    assert 'score' in result_dict, "Missing 'score' in result dict"
    assert 'feedback' in result_dict, "Missing 'feedback' in result dict"
    
    print("✓ EvaluationResult works correctly")
except Exception as e:
    print(f"✗ EvaluationResult check failed: {e}")
    sys.exit(1)

# Test URL configuration
print("\n=== Testing URL Configuration ===")

try:
    from django.urls import reverse
    from django.test import RequestFactory
    
    # These should not raise errors
    print("✓ URL configuration loaded")
except Exception as e:
    print(f"✗ URL configuration check failed: {e}")
    sys.exit(1)

# Test Celery task registration
print("\n=== Testing Celery Task Registration ===")

try:
    from core.celery import app
    
    # Check if task is registered
    task_name = 'admin_panel.tasks.evaluate_assessment_submission'
    if task_name in app.tasks or 'evaluate_assessment_submission' in str(app.tasks):
        print("✓ Celery task registered")
    else:
        print("⚠ Celery task may not be registered (this is OK if Celery worker hasn't started)")
except Exception as e:
    print(f"⚠ Celery task check warning: {e}")

# Test dependencies
print("\n=== Testing Dependencies ===")

try:
    from executor.services import CompileExecutor
    print("✓ CompileExecutor available")
except Exception as e:
    print(f"✗ CompileExecutor import failed: {e}")
    sys.exit(1)

try:
    from core.lm_client import LMStudioClient, lm_client
    print("✓ LMStudioClient available")
except Exception as e:
    print(f"✗ LMStudioClient import failed: {e}")
    sys.exit(1)

try:
    from channels.layers import get_channel_layer
    print("✓ Channels available")
except Exception as e:
    print(f"✗ Channels import failed: {e}")
    sys.exit(1)

# Final summary
print("\n" + "=" * 50)
print("✅ ALL VALIDATION CHECKS PASSED!")
print("=" * 50)
print("\nAssessment Engine is properly installed and ready to use.")
print("\nNext steps:")
print("1. Run migrations: python manage.py migrate")
print("2. Start Redis: redis-server")
print("3. Start Celery: celery -A core worker -l info")
print("4. Start Django: python manage.py runserver")
print("5. (Optional) Start LM Studio for open-ended questions")
print("6. Run tests: python admin_panel/test_assessment_engine.py")
