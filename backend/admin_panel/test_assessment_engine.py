"""
Test script for AssessmentEngine functionality.
Demonstrates MCQ, code, and open-ended evaluation.
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from admin_panel.models import AssessmentQuestion, AssessmentSubmission
from admin_panel.assessment_engine import assessment_engine
from quests.models import Quest
from users.models import User


def test_mcq_evaluation():
    """Test MCQ instant scoring."""
    print("\n=== Testing MCQ Evaluation ===")
    
    # Create test question
    quest = Quest.objects.first()
    if not quest:
        print("No quest found. Please create a quest first.")
        return
    
    question = AssessmentQuestion.objects.create(
        quest=quest,
        question_type='mcq',
        prompt='What is the time complexity of binary search?',
        correct_answer='1',
        mcq_options=['O(n)', 'O(log n)', 'O(n^2)', 'O(1)'],
        points=10
    )
    
    user = User.objects.first()
    if not user:
        print("No user found. Please create a user first.")
        return
    
    # Test correct answer
    submission_correct = AssessmentSubmission.objects.create(
        user=user,
        question=question,
        answer='1',
        status='pending'
    )
    
    result_correct = assessment_engine.evaluate(submission_correct)
    print(f"Correct Answer Test:")
    print(f"  Passed: {result_correct.passed}")
    print(f"  Score: {result_correct.score}/{question.points}")
    print(f"  Feedback: {result_correct.feedback}")
    
    # Test incorrect answer
    submission_incorrect = AssessmentSubmission.objects.create(
        user=user,
        question=question,
        answer='0',
        status='pending'
    )
    
    result_incorrect = assessment_engine.evaluate(submission_incorrect)
    print(f"\nIncorrect Answer Test:")
    print(f"  Passed: {result_incorrect.passed}")
    print(f"  Score: {result_incorrect.score}/{question.points}")
    print(f"  Feedback: {result_incorrect.feedback}")
    
    # Cleanup
    question.delete()


def test_code_evaluation():
    """Test code execution with test cases."""
    print("\n=== Testing Code Evaluation ===")
    
    quest = Quest.objects.first()
    if not quest:
        print("No quest found. Please create a quest first.")
        return
    
    # Create code challenge
    question = AssessmentQuestion.objects.create(
        quest=quest,
        question_type='code',
        prompt='Write a function that returns the sum of two numbers.',
        correct_answer='def add(a, b):\n    return a + b',
        language='python',
        test_cases=[
            {'input': '2\n3', 'expected': '5'},
            {'input': '10\n20', 'expected': '30'},
            {'input': '-5\n5', 'expected': '0'},
        ],
        points=20
    )
    
    user = User.objects.first()
    if not user:
        print("No user found. Please create a user first.")
        return
    
    # Test correct solution
    correct_code = """
a = int(input())
b = int(input())
print(a + b)
"""
    
    submission_correct = AssessmentSubmission.objects.create(
        user=user,
        question=question,
        answer=correct_code,
        status='pending'
    )
    
    result_correct = assessment_engine.evaluate(submission_correct)
    print(f"Correct Code Test:")
    print(f"  Passed: {result_correct.passed}")
    print(f"  Score: {result_correct.score}/{question.points}")
    print(f"  Feedback: {result_correct.feedback}")
    print(f"  Tests Passed: {sum(1 for t in result_correct.test_results if t['passed'])}/{len(result_correct.test_results)}")
    
    # Test incorrect solution
    incorrect_code = """
a = int(input())
b = int(input())
print(a - b)
"""
    
    submission_incorrect = AssessmentSubmission.objects.create(
        user=user,
        question=question,
        answer=incorrect_code,
        status='pending'
    )
    
    result_incorrect = assessment_engine.evaluate(submission_incorrect)
    print(f"\nIncorrect Code Test:")
    print(f"  Passed: {result_incorrect.passed}")
    print(f"  Score: {result_incorrect.score}/{question.points}")
    print(f"  Feedback: {result_incorrect.feedback}")
    print(f"  Tests Passed: {sum(1 for t in result_incorrect.test_results if t['passed'])}/{len(result_incorrect.test_results)}")
    
    # Cleanup
    question.delete()


def test_open_ended_evaluation():
    """Test LM Studio semantic evaluation."""
    print("\n=== Testing Open-Ended Evaluation ===")
    
    quest = Quest.objects.first()
    if not quest:
        print("No quest found. Please create a quest first.")
        return
    
    # Create open-ended question
    question = AssessmentQuestion.objects.create(
        quest=quest,
        question_type='open_ended',
        prompt='Explain the difference between a list and a tuple in Python.',
        validation_criteria='Answer should mention: 1) Lists are mutable, tuples are immutable. 2) Lists use [], tuples use (). 3) Performance differences.',
        points=15
    )
    
    user = User.objects.first()
    if not user:
        print("No user found. Please create a user first.")
        return
    
    # Test good answer
    good_answer = """
Lists and tuples are both sequence types in Python, but they have key differences:
1. Mutability: Lists are mutable (can be changed after creation), while tuples are immutable (cannot be changed).
2. Syntax: Lists use square brackets [], tuples use parentheses ().
3. Performance: Tuples are generally faster than lists because of their immutability.
4. Use cases: Lists are used when data needs to change, tuples for fixed data.
"""
    
    submission_good = AssessmentSubmission.objects.create(
        user=user,
        question=question,
        answer=good_answer,
        status='pending'
    )
    
    result_good = assessment_engine.evaluate(submission_good)
    print(f"Good Answer Test:")
    print(f"  Passed: {result_good.passed}")
    print(f"  Score: {result_good.score}/{question.points}")
    print(f"  Criteria Met: {result_good.criteria_met}")
    print(f"  Feedback: {result_good.feedback}")
    if result_good.missing_points:
        print(f"  Missing Points: {result_good.missing_points}")
    
    # Test weak answer
    weak_answer = "Lists and tuples are similar but lists can be changed."
    
    submission_weak = AssessmentSubmission.objects.create(
        user=user,
        question=question,
        answer=weak_answer,
        status='pending'
    )
    
    result_weak = assessment_engine.evaluate(submission_weak)
    print(f"\nWeak Answer Test:")
    print(f"  Passed: {result_weak.passed}")
    print(f"  Score: {result_weak.score}/{question.points}")
    print(f"  Criteria Met: {result_weak.criteria_met}")
    print(f"  Feedback: {result_weak.feedback}")
    if result_weak.missing_points:
        print(f"  Missing Points: {result_weak.missing_points}")
    
    # Cleanup
    question.delete()


if __name__ == '__main__':
    print("SkillTree AI - AssessmentEngine Test Suite")
    print("=" * 50)
    
    try:
        test_mcq_evaluation()
        test_code_evaluation()
        test_open_ended_evaluation()
        
        print("\n" + "=" * 50)
        print("All tests completed!")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
