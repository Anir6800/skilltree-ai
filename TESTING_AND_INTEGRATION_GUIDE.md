# Testing & Integration Guide

## 🔧 Fix Database Permission Issue

### Problem
```
Got an error creating the test database: permission denied to create database
```

### Solution

The test settings are already configured to use in-memory SQLite. Use these commands:

#### Windows (PowerShell)
```powershell
# Set environment variable
$env:DJANGO_SETTINGS_MODULE = "core.test_settings"

# Run tests
python manage.py test skills.test_quest_autofill
```

#### Windows (Command Prompt)
```cmd
REM Run the batch file
run_tests.bat skills.test_quest_autofill
```

#### Linux/Mac
```bash
# Run the shell script
bash run_tests.sh skills.test_quest_autofill
```

#### Or directly with environment variable
```bash
DJANGO_SETTINGS_MODULE=core.test_settings python manage.py test skills.test_quest_autofill
```

### What This Does
- Uses in-memory SQLite database (no file I/O, no permissions needed)
- Disables Redis requirement (uses in-memory channels)
- Runs Celery tasks synchronously
- Suppresses logging for cleaner output

## ✅ Verify Tests Pass

```bash
# Run all quest autofill tests
DJANGO_SETTINGS_MODULE=core.test_settings python manage.py test skills.test_quest_autofill -v 2

# Expected output:
# Found 20 test(s).
# Creating test database for alias 'default'...
# System check identified no issues (0 silenced).
# test_autofill_quests_for_tree_no_stubs ... ok
# test_autofill_quests_for_tree_not_found ... ok
# test_autofill_quests_for_tree_wrong_status ... ok
# ...
# Ran 20 tests in X.XXXs
# OK
```

## 🔗 Connect SkillTreeMakerPage with Skill Tree View

### What's Been Updated

#### 1. **SkillTreeMakerPage** (`frontend/src/pages/SkillTreeMakerPage.jsx`)
- Auto-Fill button now visible in result state
- Stores generated tree info in sessionStorage
- Passes tree data to skill tree view via navigation state
- Sends onboarding data to backend

#### 2. **Onboarding Model** (`backend/users/onboarding_models.py`)
- Added `generated_tree_id` field (UUID)
- Added `generated_topic` field (string)
- Stores which tree was generated during onboarding

#### 3. **Onboarding Serializer** (`backend/users/onboarding_serializers.py`)
- Updated to include new fields
- Allows reading/writing generated tree info

#### 4. **Onboarding Views** (`backend/users/onboarding_views.py`)
- Added `update_profile()` endpoint
- Added `get_profile()` endpoint
- Stores generated tree info in database

#### 5. **Onboarding URLs** (`backend/users/onboarding_urls.py`)
- Added `/api/onboarding/update-profile/` route
- Added `/api/onboarding/profile/` route

### User Flow

```
1. User completes onboarding
   ↓
2. User navigates to SkillTreeMakerPage
   ↓
3. User generates a skill tree
   ↓
4. Tree generation completes
   ↓
5. User clicks "Auto-Fill Quests" (optional)
   ↓
6. Quests are filled with content
   ↓
7. User clicks "View in Skill Tree"
   ↓
8. Navigates to /skill-tree with:
   - highlightNewSkills: true
   - generatedTreeId: tree-id
   - generatedTopic: topic-name
   ↓
9. Onboarding profile updated with:
   - generated_tree_id
   - generated_topic
   - path_generated: true
   ↓
10. Data persisted in database
```

## 📡 API Endpoints

### Update Onboarding Profile
```
POST /api/onboarding/update-profile/
Authorization: Bearer TOKEN
Content-Type: application/json

{
  "generated_topic": "Python Basics",
  "generated_tree_id": "550e8400-e29b-41d4-a716-446655440000",
  "path_generated": true
}

Response (200 OK):
{
  "status": "updated",
  "profile": {
    "id": "...",
    "primary_goal": "job_prep",
    "generated_tree_id": "550e8400-e29b-41d4-a716-446655440000",
    "generated_topic": "Python Basics",
    "path_generated": true,
    ...
  }
}
```

### Get Onboarding Profile
```
GET /api/onboarding/profile/
Authorization: Bearer TOKEN

Response (200 OK):
{
  "id": "...",
  "primary_goal": "job_prep",
  "target_role": "Full Stack Developer",
  "experience_years": 2,
  "category_levels": {...},
  "selected_interests": [...],
  "weekly_hours": 10,
  "completed_at": "2024-04-27T10:00:00Z",
  "path_generated": true,
  "generated_tree_id": "550e8400-e29b-41d4-a716-446655440000",
  "generated_topic": "Python Basics"
}
```

## 🗄️ Database Migration

### Apply Migration
```bash
python manage.py migrate users
```

### What's Added
- `generated_tree_id` (UUID field, nullable)
- `generated_topic` (CharField, max 200, blank)

### Rollback (if needed)
```bash
python manage.py migrate users 0001
```

## 🧪 Test the Integration

### 1. Create Test User
```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from users.onboarding_models import OnboardingProfile

User = get_user_model()
user = User.objects.create_user('testuser', 'test@example.com', 'pass123')

# Create onboarding profile
profile = OnboardingProfile.objects.create(
    user=user,
    primary_goal='job_prep',
    target_role='Full Stack Developer',
    experience_years=2,
    category_levels={'algorithms': 'beginner', 'ds': 'intermediate'},
    selected_interests=['python', 'react'],
    weekly_hours=10
)

print(f"Profile created: {profile.id}")
```

### 2. Generate Tree
```bash
curl -X POST http://localhost:8000/api/skills/generate/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"topic": "Python Basics", "depth": 2}'

# Response:
# {"tree_id": "550e8400-e29b-41d4-a716-446655440000", "status": "generating", ...}
```

### 3. Wait for Tree Ready
```bash
curl http://localhost:8000/api/skills/generated/550e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check status field until it's "ready"
```

### 4. Update Onboarding Profile
```bash
curl -X POST http://localhost:8000/api/onboarding/update-profile/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "generated_topic": "Python Basics",
    "generated_tree_id": "550e8400-e29b-41d4-a716-446655440000",
    "path_generated": true
  }'

# Response:
# {"status": "updated", "profile": {...}}
```

### 5. Verify Profile Updated
```bash
curl http://localhost:8000/api/onboarding/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Should show:
# {
#   "generated_tree_id": "550e8400-e29b-41d4-a716-446655440000",
#   "generated_topic": "Python Basics",
#   "path_generated": true,
#   ...
# }
```

## 🎯 Frontend Integration

### SkillTreeMakerPage Updates

The page now:
1. Stores tree info in sessionStorage
2. Sends onboarding data to backend
3. Passes tree data to skill tree view

```javascript
// When user clicks "View in Skill Tree"
navigate('/skill-tree', { 
  state: { 
    highlightNewSkills: true,
    generatedTreeId: generatedTree?.id,
    generatedTopic: generatedTree?.topic
  } 
});

// Onboarding update
await api.post('/api/onboarding/update-profile/', {
  generated_topic: topic.trim(),
  path_generated: true,
  generated_tree_id: treeId,
});
```

### Skill Tree View Integration

The skill tree view can now:
1. Receive generated tree info from navigation state
2. Highlight newly generated skills
3. Show which tree is being viewed

```javascript
// In SkillTreePage.jsx
const location = useLocation();
const { generatedTreeId, generatedTopic } = location.state || {};

// Use this to highlight new skills or show tree info
```

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    SkillTreeMakerPage                       │
│                                                             │
│  1. Generate Tree                                          │
│     POST /api/skills/generate/                             │
│     → tree_id, status="generating"                         │
│                                                             │
│  2. Poll for Ready                                         │
│     GET /api/skills/generated/{tree_id}/                   │
│     → status="ready"                                       │
│                                                             │
│  3. Update Onboarding                                      │
│     POST /api/onboarding/update-profile/                   │
│     → generated_tree_id, generated_topic stored            │
│                                                             │
│  4. Navigate to Skill Tree                                 │
│     navigate('/skill-tree', { state: {...} })             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    SkillTreePage                            │
│                                                             │
│  1. Receive Navigation State                               │
│     - generatedTreeId                                      │
│     - generatedTopic                                       │
│     - highlightNewSkills                                   │
│                                                             │
│  2. Display Skill Tree                                     │
│     - Highlight new skills from generated tree             │
│     - Show tree metadata                                   │
│                                                             │
│  3. Allow Skill Interaction                                │
│     - Start skills                                         │
│     - View quests                                          │
│     - Track progress                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Database                                 │
│                                                             │
│  OnboardingProfile:                                        │
│  - generated_tree_id (UUID)                                │
│  - generated_topic (string)                                │
│  - path_generated (boolean)                                │
│                                                             │
│  GeneratedSkillTree:                                       │
│  - id (UUID)                                               │
│  - topic (string)                                          │
│  - skills_created (M2M)                                    │
│  - status (ready/generating/failed)                        │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Deployment Checklist

- [ ] Run migrations: `python manage.py migrate users`
- [ ] Run tests: `DJANGO_SETTINGS_MODULE=core.test_settings python manage.py test skills.test_quest_autofill`
- [ ] Verify API endpoints work
- [ ] Test frontend navigation
- [ ] Check database updates
- [ ] Monitor logs for errors
- [ ] Test with real user flow

## 📝 Summary

### What's New
1. ✅ Database permission issue fixed (use test_settings)
2. ✅ SkillTreeMakerPage connects to skill tree view
3. ✅ Onboarding data stored in database
4. ✅ Generated tree info tracked
5. ✅ New API endpoints for profile management

### How to Use
1. Run tests: `DJANGO_SETTINGS_MODULE=core.test_settings python manage.py test skills.test_quest_autofill`
2. Apply migrations: `python manage.py migrate users`
3. Use SkillTreeMakerPage to generate trees
4. Trees are automatically linked to onboarding profile
5. Navigate to skill tree view with tree context

### Files Modified
- `backend/users/onboarding_models.py` - Added fields
- `backend/users/onboarding_serializers.py` - Updated serializer
- `backend/users/onboarding_views.py` - Added endpoints
- `backend/users/onboarding_urls.py` - Added routes
- `backend/users/migrations/0002_onboarding_generated_fields.py` - New migration
- `frontend/src/pages/SkillTreeMakerPage.jsx` - Updated navigation
- `backend/pytest.ini` - Test configuration
- `backend/run_tests.bat` - Windows test runner
- `backend/run_tests.sh` - Linux/Mac test runner

Ready to go! 🚀
