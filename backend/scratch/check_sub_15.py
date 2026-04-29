
import os
import sys
sys.path.append(os.getcwd())
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from quests.models import QuestSubmission

try:
    s = QuestSubmission.objects.get(id=15)
    print(f"Status: {s.status}")
    print(f"AI Feedback: {s.ai_feedback}")
    print(f"Execution Result: {s.execution_result}")
except QuestSubmission.DoesNotExist:
    print("Submission 15 not found.")
except Exception as e:
    print(f"Error: {e}")
