# AdminQuestGenerator - Quick Reference

## What It Does
Generates complete coding quests using LM Studio with:
- Engaging titles and problem statements
- Python starter code with TODO comments
- Exactly 5 test cases with input/output pairs
- XP rewards (100-500 based on difficulty)
- One-line hints for each test case

## Files Created/Modified

### Backend
- `admin_panel/quest_generator.py` - Core generator (NEW)
- `admin_panel/views.py` - API endpoints (MODIFIED)
- `admin_panel/urls.py` - URL routing (MODIFIED)

### Frontend
- `components/admin/QuestGeneratorModal.jsx` - Modal component (NEW)
- `components/admin/AssessmentsTab.jsx` - Enhanced tab (MODIFIED)

## API Endpoints

```
POST   /api/admin/quests/generate/           Single quest
POST   /api/admin/quests/generate-batch/     Batch quests (1-10)
POST   /api/admin/quests/save-draft/         Save as draft
GET    /api/admin/quests/lm-studio-status/   Check LM Studio
```

## Single Quest Generation

```bash
curl -X POST http://localhost:8000/api/admin/quests/generate/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": 1,
    "topic_hint": "Two Pointers",
    "difficulty": 3,
    "quest_type": "coding"
  }'
```

## Batch Generation (5 Quests)

```bash
curl -X POST http://localhost:8000/api/admin/quests/generate-batch/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": 1,
    "topic_hint": "Two Pointers",
    "difficulty": 3,
    "quest_type": "coding",
    "count": 5
  }'
```

## Save Generated Quest

```bash
curl -X POST http://localhost:8000/api/admin/quests/save-draft/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": 1,
    "quest_data": { ...generated quest data... }
  }'
```

## Python Usage

```python
from admin_panel.quest_generator import quest_generator

# Single quest
quest_data = quest_generator.generate_quest(
    skill_id=1,
    topic_hint="Two Pointers",
    difficulty=3,
    quest_type="coding"
)

# Save to database
quest = quest_generator.save_quest_draft(1, quest_data)

# Check LM Studio
if quest_generator.is_available():
    print("Ready to generate!")
```

## Frontend Usage

```jsx
import QuestGeneratorModal from './QuestGeneratorModal';

<QuestGeneratorModal
  isOpen={showModal}
  onClose={() => setShowModal(false)}
  skills={skillsList}
  onQuestSaved={() => refreshQuests()}
/>
```

## Parameters

### Difficulty Levels
- 1: Beginner (100-150 XP)
- 2: Intermediate (150-250 XP)
- 3: Advanced (250-350 XP)
- 4: Expert (350-450 XP)
- 5: Master (450-500 XP)

### Quest Types
- `coding` - Write code to solve problem
- `debugging` - Fix buggy code
- `mcq` - Multiple choice question

## Generated Quest Structure

```json
{
  "title": "Container With Most Water",
  "description": "Given an array of integers...",
  "starter_code": "def maxArea(height):\n    # TODO: implement",
  "test_cases": [
    {
      "input": "[1,8,6,2,5,4,8,3,7]",
      "expected_output": "49",
      "hint": "Use two pointers from ends"
    }
  ],
  "xp_reward": 250,
  "estimated_minutes": 20,
  "difficulty_multiplier": 0.6,
  "type": "coding",
  "ai_generated": true
}
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 503 Service Unavailable | LM Studio down | Start LM Studio |
| 400 Bad Request | Invalid parameters | Check skill_id, difficulty (1-5), quest_type |
| 500 Internal Error | Generation failed | Check LM Studio logs |

## Requirements

- LM Studio running on `http://localhost:1234/v1`
- Admin user permissions
- Valid skill ID in database
- Difficulty 1-5
- Valid quest type

## Performance

- Single quest: ~10-30 seconds
- Batch (5 quests): ~50-150 seconds (parallel)
- Batch (10 quests): ~100-300 seconds (parallel)

## Security

- Admin-only access
- Input validation on all parameters
- Generated data validated before saving
- No code execution

## Troubleshooting

**LM Studio not found**
```bash
# Check if running
curl http://localhost:1234/v1/models

# Start LM Studio
lm-studio
```

**Invalid JSON response**
- Ensure model supports JSON mode
- Check LM Studio version compatibility

**Generation timeout**
- Increase timeout in settings
- Check LM Studio performance
- Reduce batch size

## Next Steps

1. Start LM Studio
2. Go to Admin Panel → Assessments
3. Click "✦ Generate with AI"
4. Select skill and parameters
5. Review generated quests
6. Save as draft
7. Edit and publish

## Documentation

- Full guide: `QUEST_GENERATOR_INTEGRATION.md`
- API reference: See full guide
- Examples: See full guide
