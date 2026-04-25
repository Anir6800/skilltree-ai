"""
Test script for AI Evaluation Service
Run: python manage.py shell < ai_evaluation/test_evaluation.py
"""

from ai_evaluation.services import ai_evaluator
from core.chroma_client import chroma_client
from quests.models import Quest, QuestSubmission
from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 60)
print("AI Evaluation Service Test")
print("=" * 60)

# Check ChromaDB stats
print("\n1. ChromaDB Collection Stats:")
stats = chroma_client.get_collection_stats()
for collection, count in stats.items():
    print(f"   • {collection}: {count} documents")

# Check LM Studio availability
print("\n2. LM Studio Availability:")
if ai_evaluator.is_available():
    print("   ✓ LM Studio is available")
else:
    print("   ✗ LM Studio is NOT available")
    print("   → Start LM Studio and load a model")

# Test RAG retrieval
print("\n3. Testing RAG Context Retrieval:")
test_code = """
def binary_search(nums, target):
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
"""

context = ai_evaluator._retrieve_rag_context(
    code=test_code,
    language="python",
    quest_description="Implement binary search algorithm"
)
print(f"   Retrieved {len(context)} characters of context")
if context and context != "No specific skill context available.":
    print("   ✓ RAG retrieval working")
else:
    print("   ✗ No context retrieved")
    print("   → Run: python manage.py seed_skill_knowledge")

# Test evaluation (if quest exists)
print("\n4. Testing Full Evaluation Pipeline:")
quest = Quest.objects.first()
if quest:
    print(f"   Using quest: {quest.title}")
    
    # Create test submission
    user = User.objects.first()
    if not user:
        print("   ✗ No user found. Create a user first.")
    else:
        submission = QuestSubmission.objects.create(
            user=user,
            quest=quest,
            code=test_code,
            language="python",
            status="pending"
        )
        
        print("   Evaluating submission...")
        try:
            feedback = ai_evaluator.evaluate(submission)
            print(f"   ✓ Evaluation complete!")
            print(f"   Score: {feedback.get('score', 'N/A')}/100")
            print(f"   Summary: {feedback.get('summary', 'N/A')[:80]}...")
            
            # Clean up test submission
            submission.delete()
        except Exception as e:
            print(f"   ✗ Evaluation failed: {e}")
            submission.delete()
else:
    print("   ✗ No quests found")
    print("   → Run: python manage.py seed_quests")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
