# AdminQuestGenerator Integration Guide

## Overview

The AdminQuestGenerator is a complete AI-powered quest generation system for SkillTree AI's admin panel. It leverages LM Studio to generate original, engaging coding quests with full test cases, starter code, and XP rewards.

## Architecture

### Backend Components

#### 1. `admin_panel/quest_generator.py` - Core Generator
- **AdminQuestGenerator class**: Main generator with single and batch quest generation
- **Key Methods**:
  - `generate_quest()`: Generate a single quest draft
  - `generate_batch_quests()`: Generate multiple quests in parallel using asyncio
  - `save_quest_draft()`: Save generated quest to database
  - `is_available()`: Check LM Studio availability

#### 2. `admin_panel/views.py` - API Endpoints
- `generate_quest()`: POST endpoint for single quest generation
- `generate_batch_quests()`: POST endpoint for batch generation (1-10 quests)
- `save_quest_draft()`: POST endpoint to save generated quest as draft
- `check_lm_studio_status()`: GET endpoint to check LM Studio availability

#### 3. `admin_panel/urls.py` - URL Routing
```
POST   /api/admin/quests/generate/           - Generate single quest
POST   /api/admin/quests/generate-batch/     - Generate batch quests
POST   /api/admin/quests/save-draft/         - Save quest draft
GET    /api/admin/quests/lm-studio-status/   - Check LM Studio status
```

### Frontend Components

#### 1. `QuestGeneratorModal.jsx` - Modal Component
- Reusable modal for quest generation
- Handles skill selection, difficulty, quest type, and batch count
- Shows generated quests in preview cards
- Allows editing and saving as drafts

#### 2. `AssessmentsTab.jsx` - Enhanced Tab
- Integrated "✦ Generate with AI" button
- Maintains existing manual question creation
- Fetches skills for generator modal
- Refreshes quest list after saving

## Features

### Single Quest Generation
```bash
POST /api/admin/quests/generate/
{
  "skill_id": 1,
  "topic_hint": "Two Pointers",
  "difficulty": 3,
  "quest_type": "coding"
}
```

**Response**:
```json
{
  "quest_data": {
    "title": "Container With Most Water",
    "description": "Given an array of integers...",
    "starter_code": "def maxArea(height):\n    # TODO: implement",
    "test_cases": [
      {
        "input": "[1,8,6,2,5,4,8,3,7]",
        "expected_output": "49",
        "hint": "Use two pointers from ends"
      },
      ...
    ],
    "xp_reward": 250,
    "estimated_minutes": 20,
    "difficulty_multiplier": 0.6,
    "type": "coding",
    "ai_generated": true
  },
  "status": "preview"
}
```

### Batch Generation
```bash
POST /api/admin/quests/generate-batch/
{
  "skill_id": 1,
  "topic_hint": "Two Pointers",
  "difficulty": 3,
  "quest_type": "coding",
  "count": 5
}
```

**Response**:
```json
{
  "quests": [
    { quest_data_1 },
    { quest_data_2 },
    ...
  ],
  "count": 5,
  "status": "preview"
}
```

### Save Quest Draft
```bash
POST /api/admin/quests/save-draft/
{
  "skill_id": 1,
  "quest_data": { ...generated quest data... }
}
```

**Response**:
```json
{
  "quest_id": 42,
  "title": "Container With Most Water",
  "status": "draft"
}
```

## LM Studio Integration

### Prompt Structure
The generator uses a carefully crafted system and user prompt:

**System Prompt**:
- Establishes role as expert CS educator
- Requires JSON-only response
- Specifies exact output format

**User Prompt**:
- Includes skill title, topic hint, difficulty level
- Specifies quest type (coding, debugging, mcq)
- Lists all required fields with examples
- Difficulty-based XP reward ranges

### Response Format
LM Studio returns JSON with:
- `title`: Engaging quest title (5-10 words)
- `description`: Problem statement with example (3-5 sentences)
- `starter_code`: Python code with TODO comments
- `test_cases`: Array of 5 test cases with input/output/hint
- `xp_reward`: 100-500 based on difficulty
- `estimated_minutes`: Time estimate
- `difficulty_multiplier`: 0.2-1.0 based on difficulty
- `type`: Quest type (coding, debugging, mcq)

## Validation

### Quest Data Validation
The generator validates all generated quests:
- Title: Non-empty string, min 5 chars
- Description: Non-empty string, min 20 chars
- Test cases: Exactly 5 with input/output pairs
- XP reward: 100-500 range
- Estimated minutes: At least 5 minutes

### Error Handling
- **ExecutionServiceUnavailable**: LM Studio is down or unreachable
- **ValueError**: Invalid parameters or missing skill
- **JSONDecodeError**: Invalid JSON from LM Studio
- **ValidationError**: Generated data doesn't meet requirements

## Performance

### Batch Generation
- Uses `asyncio.gather()` for parallel requests
- Runs up to 10 quests concurrently
- Timeout: 60 seconds per quest
- Graceful error handling for partial failures

### Caching
- LM Studio availability check cached in Redis
- Quest generation results not cached (always fresh)

## Security

### Access Control
- Requires `IsAuthenticated` and `IsAdminUser` permissions
- All endpoints protected by admin-only decorators

### Input Validation
- Skill ID validation (must exist)
- Difficulty range validation (1-5)
- Quest type validation (coding, debugging, mcq)
- Batch count validation (1-10)
- Topic hint sanitization

### Data Sanitization
- All user inputs validated before LM Studio call
- Generated data validated before saving
- No direct execution of generated code

## Configuration

### Environment Variables
```bash
LM_STUDIO_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=openai/gpt-oss-20b
```

### Django Settings
- Uses existing `lm_client` singleton from `core.lm_client`
- Respects `settings.LM_STUDIO_URL` and `settings.LM_STUDIO_MODEL`

## Usage Examples

### Generate Single Quest
```python
from admin_panel.quest_generator import quest_generator

quest_data = quest_generator.generate_quest(
    skill_id=1,
    topic_hint="Two Pointers",
    difficulty=3,
    quest_type="coding"
)

quest = quest_generator.save_quest_draft(1, quest_data)
print(f"Created quest: {quest.title} (ID: {quest.id})")
```

### Generate Batch Quests
```python
import asyncio

async def generate_batch():
    quests = await quest_generator.generate_batch_quests(
        skill_id=1,
        topic_hint="Two Pointers",
        difficulty=3,
        quest_type="coding",
        count=5
    )
    return quests

quests = asyncio.run(generate_batch())
print(f"Generated {len(quests)} quests")
```

### Check LM Studio Status
```python
if quest_generator.is_available():
    print("LM Studio is ready for quest generation")
else:
    print("LM Studio is unavailable")
```

## Frontend Usage

### Using QuestGeneratorModal
```jsx
import QuestGeneratorModal from './QuestGeneratorModal';

function MyComponent() {
  const [showModal, setShowModal] = useState(false);
  const [skills, setSkills] = useState([]);

  return (
    <>
      <button onClick={() => setShowModal(true)}>
        Generate Quests
      </button>
      
      <QuestGeneratorModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        skills={skills}
        onQuestSaved={() => {
          // Refresh quests list
        }}
      />
    </>
  );
}
```

## Troubleshooting

### LM Studio Unavailable
- Check if LM Studio is running: `curl http://localhost:1234/v1/models`
- Verify `LM_STUDIO_URL` environment variable
- Check network connectivity

### Invalid JSON Response
- Ensure LM Studio model supports JSON mode
- Check model compatibility with `response_format` parameter
- Review LM Studio logs for errors

### Generation Timeout
- Increase `QUEST_GENERATION_TIMEOUT` if needed
- Check LM Studio performance
- Reduce batch size if generating multiple quests

### Validation Failures
- Review generated quest data in LM Studio response
- Check if model is producing valid JSON
- Verify prompt is being sent correctly

## Future Enhancements

1. **ContentValidator Integration**: Auto-review generated quests
2. **Caching**: Cache frequently generated quest types
3. **Templates**: Support quest templates for consistency
4. **Feedback Loop**: Track which generated quests are most popular
5. **Multi-language**: Support quest generation in multiple languages
6. **Custom Prompts**: Allow admins to customize generation prompts

## Testing

### Unit Tests
```bash
python manage.py test admin_panel.tests.TestAdminQuestGenerator
```

### Integration Tests
```bash
python manage.py test admin_panel.tests.TestQuestGenerationAPI
```

### Manual Testing
1. Start LM Studio: `lm-studio`
2. Run Django: `python manage.py runserver`
3. Navigate to Admin Panel → Assessments
4. Click "✦ Generate with AI"
5. Select skill, difficulty, and quest type
6. Click "Generate"
7. Review preview and save as draft

## API Reference

### POST /api/admin/quests/generate/
Generate a single quest.

**Request**:
```json
{
  "skill_id": 1,
  "topic_hint": "Two Pointers",
  "difficulty": 3,
  "quest_type": "coding"
}
```

**Response** (200 OK):
```json
{
  "quest_data": { ...quest data... },
  "status": "preview"
}
```

**Errors**:
- 400: Invalid parameters
- 503: LM Studio unavailable
- 500: Generation failed

### POST /api/admin/quests/generate-batch/
Generate multiple quests in parallel.

**Request**:
```json
{
  "skill_id": 1,
  "topic_hint": "Two Pointers",
  "difficulty": 3,
  "quest_type": "coding",
  "count": 5
}
```

**Response** (200 OK):
```json
{
  "quests": [ ...quest data... ],
  "count": 5,
  "status": "preview"
}
```

### POST /api/admin/quests/save-draft/
Save a generated quest as draft.

**Request**:
```json
{
  "skill_id": 1,
  "quest_data": { ...quest data... }
}
```

**Response** (201 Created):
```json
{
  "quest_id": 42,
  "title": "Quest Title",
  "status": "draft"
}
```

### GET /api/admin/quests/lm-studio-status/
Check LM Studio availability.

**Response** (200 OK):
```json
{
  "available": true,
  "status": "ready"
}
```

## License

Part of SkillTree AI platform. All rights reserved.
