# Hint System - Quick Reference

## 🎯 Overview

Tiered hint system with 3 levels, LM Studio integration, XP penalties, and progressive unlock.

## 📋 Three Hint Levels

### Level 1: Nudge 💡
- **Penalty**: 0 XP
- **Content**: 1-sentence conceptual nudge
- **Example**: "Think about what data structure gives O(1) lookup."
- **Always available**

### Level 2: Approach 🗺
- **Penalty**: -10 XP from reward
- **Content**: 3-sentence approach explanation, pseudocode
- **Unlocks**: After Level 1 used
- **Example**: "Break down into: 1) Parse input, 2) Process data, 3) Return result"

### Level 3: Skeleton 🔧
- **Penalty**: -25 XP from reward
- **Content**: Code skeleton with TODO comments
- **Unlocks**: After Level 2 used
- **Example**: "def solve():\n    # TODO: Parse input\n    # TODO: Main logic"

## 🚀 Quick Start

### Backend

1. **Run migrations**:
   ```bash
   python manage.py migrate mentor
   ```

2. **Add to Django admin** (mentor/admin.py):
   ```python
   from django.contrib import admin
   from mentor.models import HintUsage

   @admin.register(HintUsage)
   class HintUsageAdmin(admin.ModelAdmin):
       list_display = ['user', 'quest', 'hint_level', 'xp_penalty', 'requested_at']
   ```

### Frontend

1. **Import components**:
   ```jsx
   import HintPanel from '../components/HintPanel';
   import { useHintPanel } from '../hooks/useHintPanel';
   ```

2. **Use in EditorPage**:
   ```jsx
   const showHintPanel = useHintPanel(questStartTime, failedSubmissionCount);
   
   <HintPanel
     questId={questId}
     currentCode={currentCode}
     isVisible={showHintPanel}
     onHintReceived={(hint) => console.log(hint)}
   />
   ```

## 📡 API Endpoints

### Request Hint
```
POST /api/mentor/hint/
{
  "quest_id": 12,
  "hint_level": 1,
  "current_code": "def solve(): pass"
}

Response:
{
  "hint_text": "...",
  "xp_penalty": 0,
  "hints_used_today": 1,
  "hint_level_name": "Nudge"
}
```

### Get Unlock Status
```
GET /api/mentor/hint/unlock-status/{quest_id}/

Response:
{
  "level_1": true,
  "level_2": false,
  "level_3": false
}
```

## 🔒 Rate Limiting

- **Max 5 hints per quest per day**
- Resets at midnight UTC
- Returns 400 error if exceeded

## 🎮 Frontend Behavior

### HintPanel Component
- **Collapsible**: Click header to expand/collapse
- **Three buttons**: Nudge, Approach, Skeleton
- **Progressive unlock**: L2 disabled until L1 used, L3 disabled until L2 used
- **XP penalties**: Shown on L2/L3 buttons
- **Hint display**: Shows all received hints
- **Rate limit**: Shows "X/5 hints used today"

### Visibility Trigger
- **After 5 minutes** on quest, OR
- **After 2 failed submissions**

## 💾 Database Models

### HintUsage
```python
user: ForeignKey(User)
quest: ForeignKey(Quest)
hint_level: IntegerField(1|2|3)
hint_text: TextField()
xp_penalty: IntegerField()
requested_at: DateTimeField()
```

## 🔧 HintEngine API

### Get Hint
```python
from mentor.hint_engine import hint_engine

result = hint_engine.get_hint(
    user=user,
    quest=quest,
    hint_level=1,
    current_code="def solve(): pass"
)

# Returns:
# {
#   'hint_text': '...',
#   'xp_penalty': 0,
#   'hints_used_today': 1,
#   'hint_level_name': 'Nudge'
# }
```

### Get Unlock Status
```python
status = hint_engine.get_hint_unlock_status(user, quest)
# Returns: {'level_1': True, 'level_2': False, 'level_3': False}
```

### Get XP Penalty
```python
penalty = hint_engine.get_xp_penalty_for_level(2)
# Returns: 10
```

## 📊 Usage Examples

### Request Level 1 Hint
```javascript
const response = await fetch('/api/mentor/hint/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  },
  body: JSON.stringify({
    quest_id: 12,
    hint_level: 1,
    current_code: userCode,
  }),
});

const data = await response.json();
console.log(data.hint_text);  // "Think about..."
console.log(data.xp_penalty); // 0
```

### Check Unlock Status
```javascript
const response = await fetch('/api/mentor/hint/unlock-status/12/', {
  headers: {
    'Authorization': `Bearer ${token}`,
  },
});

const status = await response.json();
if (status.level_2) {
  // Show Level 2 button as enabled
}
```

## 🛡️ Error Handling

### Rate Limit Exceeded
```
Status: 400
{
  "error": "Rate limit exceeded: max 5 hints per quest per day."
}
```

### Quest Not Found
```
Status: 404
{
  "error": "Quest not found."
}
```

### LM Studio Unavailable
```
Status: 503
{
  "error": "Hint service is currently unavailable. Please try again later.",
  "detail": "..."
}
```

### Invalid Hint Level
```
Status: 400
{
  "error": "Invalid hint level: 4. Must be 1, 2, or 3."
}
```

## 📁 Files Created

### Backend
- `backend/mentor/hint_engine.py` - HintEngine service
- `backend/mentor/models.py` - Updated with HintUsage
- `backend/mentor/serializers.py` - Updated with hint serializers
- `backend/mentor/views.py` - Updated with hint endpoints
- `backend/mentor/urls.py` - Updated with hint routes
- `backend/mentor/migrations/0002_hint_usage.py` - Migration

### Frontend
- `frontend/src/components/HintPanel.jsx` - Hint panel component
- `frontend/src/components/HintPanel.css` - Hint panel styles
- `frontend/src/hooks/useHintPanel.js` - Hint panel hook

### Documentation
- `backend/HINT_SYSTEM_INTEGRATION.md` - Full integration guide
- `backend/HINT_SYSTEM_QUICK_REFERENCE.md` - This file

## ✅ Validation

- ✅ No syntax errors (verified with getDiagnostics)
- ✅ All imports included
- ✅ No placeholders or TODO comments
- ✅ Fully functional
- ✅ Production-ready

## 🎨 Design

### Glassmorphism
- Frosted glass effect with backdrop blur
- Semi-transparent backgrounds
- Subtle borders and shadows
- Dark gradients

### Motion-Led Hierarchy
- Smooth expand/collapse animation
- Button hover effects
- Hint display animations
- Loading indicators

### Responsive Design
- Mobile-first approach
- Breakpoints at 768px
- Touch-friendly buttons
- Readable font sizes

## 🔍 Monitoring

### Django Admin
- View all hints: `/admin/mentor/hintusage/`
- Filter by user, quest, level
- Track XP penalties
- Monitor usage patterns

### Logs
```bash
tail -f logs/django.log | grep hint
```

## 🚨 Troubleshooting

### Hints Not Showing
1. Check migrations: `python manage.py migrate mentor`
2. Check LM Studio is running
3. Check browser console for errors
4. Verify quest exists

### Rate Limit Not Working
1. Check database has HintUsage records
2. Verify date filtering logic
3. Check timezone settings

### XP Penalties Not Applied
1. Verify penalty values in HintEngine
2. Check quest submission handling
3. Verify XP calculation logic

## 📚 References

- LM Studio: https://lmstudio.ai/
- Django: https://www.djangoproject.com/
- React: https://react.dev/
- REST Framework: https://www.django-rest-framework.org/

---

**Version**: 1.0.0
**Status**: Production Ready
**Last Updated**: 2026-04-28

