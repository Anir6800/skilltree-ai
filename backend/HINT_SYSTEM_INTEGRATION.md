# Hint System - Integration Guide

## Overview

The tiered hint system provides three levels of hints for coding quests using LM Studio integration. Hints are generated contextually based on the user's current code, attempt count, and quest difficulty.

## Architecture

### Backend Components

#### HintEngine (mentor/hint_engine.py)
- `get_hint(user, quest, hint_level, current_code)` - Generate tiered hint
- `get_hint_unlock_status(user, quest)` - Check which hint levels are unlocked
- `get_xp_penalty_for_level(hint_level)` - Get XP penalty for hint level

#### HintUsage Model (mentor/models.py)
- Tracks hint usage per user per quest
- Enforces rate limiting (max 5 hints per quest per day)
- Stores hint text and XP penalties
- Provides helper methods for checking usage

#### API Endpoints (mentor/views.py)
- `POST /api/mentor/hint/` - Request a hint
- `GET /api/mentor/hint/unlock-status/{quest_id}/` - Get unlock status

### Frontend Components

#### HintPanel (frontend/src/components/HintPanel.jsx)
- Collapsible panel with three hint buttons
- Progressive unlock (L2 after L1, L3 after L2)
- Shows XP penalties on L2/L3
- Displays received hints
- Rate limit indicator

#### useHintPanel Hook (frontend/src/hooks/useHintPanel.js)
- Manages panel visibility
- Shows after 5 minutes OR 2 failed submissions
- Timer-based activation

## Hint Levels

### Level 1: Nudge (0 XP penalty)
- Conceptual nudge only (1 sentence)
- Algorithmic direction without code
- Example: "Think about what data structure gives O(1) lookup."

### Level 2: Approach (-10 XP penalty)
- Approach explanation (3 sentences)
- Pseudocode-level explanation
- No actual code
- Focus on algorithm and data structures

### Level 3: Near-Solution (-25 XP penalty)
- Working skeleton code
- Key logic replaced by TODO comments
- Student fills in TODOs to complete
- Never reveals full solution

## Integration Steps

### 1. Backend Setup

#### Run Migrations
```bash
python manage.py migrate mentor
```

#### Update Django Admin (mentor/admin.py)
```python
from django.contrib import admin
from mentor.models import HintUsage

@admin.register(HintUsage)
class HintUsageAdmin(admin.ModelAdmin):
    list_display = ['user', 'quest', 'hint_level', 'xp_penalty', 'requested_at']
    list_filter = ['hint_level', 'requested_at']
    search_fields = ['user__username', 'quest__title']
    readonly_fields = ['requested_at']
```

### 2. Frontend Setup

#### Import HintPanel in EditorPage
```jsx
import HintPanel from '../components/HintPanel';
import { useHintPanel } from '../hooks/useHintPanel';

function EditorPage() {
  const [questStartTime, setQuestStartTime] = useState(Date.now());
  const [failedSubmissionCount, setFailedSubmissionCount] = useState(0);
  const [currentCode, setCurrentCode] = useState('');
  
  const showHintPanel = useHintPanel(questStartTime, failedSubmissionCount);

  return (
    <div>
      {/* Editor */}
      <textarea
        value={currentCode}
        onChange={(e) => setCurrentCode(e.target.value)}
      />

      {/* Hint Panel */}
      <HintPanel
        questId={questId}
        currentCode={currentCode}
        isVisible={showHintPanel}
        onHintReceived={(hint) => {
          console.log('Hint received:', hint);
          // Apply XP penalty if needed
        }}
      />
    </div>
  );
}
```

### 3. Update Quest Submission Handling

When a quest submission fails, increment the failed submission count:

```jsx
const handleSubmit = async (code) => {
  try {
    const response = await fetch('/api/quests/submit/', {
      method: 'POST',
      body: JSON.stringify({ quest_id: questId, code }),
    });

    const result = await response.json();

    if (result.status === 'failed') {
      setFailedSubmissionCount((prev) => prev + 1);
    }
  } catch (error) {
    console.error('Submission error:', error);
  }
};
```

## API Reference

### Request Hint

**Endpoint**: `POST /api/mentor/hint/`

**Request Body**:
```json
{
  "quest_id": 12,
  "hint_level": 1,
  "current_code": "def solve():\n    pass"
}
```

**Response**:
```json
{
  "hint_text": "Think about what data structure gives O(1) lookup.",
  "xp_penalty": 0,
  "hints_used_today": 1,
  "hint_level_name": "Nudge"
}
```

**Error Responses**:
- `400 Bad Request` - Invalid hint level or rate limit exceeded
- `404 Not Found` - Quest not found
- `503 Service Unavailable` - LM Studio unavailable

### Get Hint Unlock Status

**Endpoint**: `GET /api/mentor/hint/unlock-status/{quest_id}/`

**Response**:
```json
{
  "level_1": true,
  "level_2": false,
  "level_3": false
}
```

## Rate Limiting

- **Max 5 hints per quest per day**
- Enforced in `HintUsage.can_request_hint()`
- Resets daily at midnight UTC
- Returns 400 error if limit exceeded

## XP Penalties

- **Level 1 (Nudge)**: 0 XP penalty
- **Level 2 (Approach)**: -10 XP from quest reward
- **Level 3 (Near-Solution)**: -25 XP from quest reward

Penalties are applied when hint is requested, not when quest is completed.

## Progressive Unlock

- **Level 1**: Always available
- **Level 2**: Unlocks after Level 1 is used
- **Level 3**: Unlocks after Level 2 is used

Frontend enforces this with disabled buttons and lock icons.

## LM Studio Integration

### Prompt Template

```
You are a coding mentor. The student is solving '{quest.title}' 
(skill: {skill.title}, difficulty: {difficulty}/5). 
Their current code: {current_code[:500]}. 
They have failed {attempt_count} times.

Generate a Level {hint_level} hint:
- Level 1: Conceptual nudge only (1 sentence)
- Level 2: Approach explanation (3 sentences, no code)
- Level 3: Skeleton code with TODO markers
```

### Fallback Hints

If LM Studio is unavailable, fallback hints are provided:

```python
def _get_fallback_hint(self, hint_level, quest):
    if hint_level == 1:
        return "Think about the problem requirements..."
    elif hint_level == 2:
        return "Break down the problem into steps..."
    else:
        return "Here's a skeleton for {quest.title}..."
```

## Error Handling

### LM Studio Unavailable
- Returns 503 Service Unavailable
- Provides fallback hint
- Logs error for debugging

### Rate Limit Exceeded
- Returns 400 Bad Request
- Message: "Rate limit exceeded: max 5 hints per quest per day."

### Invalid Quest
- Returns 404 Not Found
- Message: "Quest not found."

### Invalid Hint Level
- Returns 400 Bad Request
- Message: "Invalid hint level: {level}. Must be 1, 2, or 3."

## Performance Considerations

### Caching
- Hint unlock status cached in frontend state
- Hints stored in component state to avoid re-fetching

### Database Queries
- Indexed on (user, quest) for fast lookups
- Indexed on (user, requested_at) for rate limit checks
- Efficient date-based filtering for daily limits

### LM Studio
- Max tokens adjusted per level (150, 300, 500)
- Temperature set to 0.3 for consistency
- Timeout: 30 seconds

## Testing

### Unit Tests
```python
from django.test import TestCase
from mentor.hint_engine import hint_engine
from users.models import User
from quests.models import Quest

class HintEngineTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pass')
        self.quest = Quest.objects.create(title='Test Quest')

    def test_get_hint_level_1(self):
        result = hint_engine.get_hint(
            user=self.user,
            quest=self.quest,
            hint_level=1,
            current_code='def solve(): pass'
        )
        self.assertIn('hint_text', result)
        self.assertEqual(result['xp_penalty'], 0)

    def test_rate_limit(self):
        # Request 5 hints
        for i in range(5):
            hint_engine.get_hint(self.user, self.quest, 1, '')
        
        # 6th should fail
        with self.assertRaises(ValueError):
            hint_engine.get_hint(self.user, self.quest, 1, '')
```

### Integration Tests
```python
def test_hint_api_endpoint(self):
    response = self.client.post('/api/mentor/hint/', {
        'quest_id': self.quest.id,
        'hint_level': 1,
        'current_code': 'def solve(): pass'
    })
    self.assertEqual(response.status_code, 200)
    self.assertIn('hint_text', response.json())
```

## Monitoring

### Django Admin
- View all hints: `/admin/mentor/hintusage/`
- Filter by user, quest, hint level
- Track XP penalties
- Monitor usage patterns

### Logs
```bash
tail -f logs/django.log | grep hint
```

## Future Enhancements

1. **Hint Customization** - Allow users to set hint preferences
2. **Hint Analytics** - Track which hints are most helpful
3. **Adaptive Hints** - Adjust hint difficulty based on user level
4. **Hint Caching** - Cache generated hints for common quests
5. **Hint Feedback** - Let users rate hint helpfulness
6. **Hint Variations** - Generate multiple hints per level
7. **Hint Scheduling** - Suggest hints at optimal times
8. **Hint Chains** - Link related hints across quests

## References

- LM Studio: https://lmstudio.ai/
- Django Models: https://docs.djangoproject.com/en/stable/topics/db/models/
- Django REST Framework: https://www.django-rest-framework.org/
- React Hooks: https://react.dev/reference/react/hooks

---

**Version**: 1.0.0
**Status**: Production Ready
**Last Updated**: 2026-04-28

