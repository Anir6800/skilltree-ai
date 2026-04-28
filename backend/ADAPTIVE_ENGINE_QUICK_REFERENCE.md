# Adaptive Engine - Quick Reference

## 🚀 Quick Start (5 minutes)

```bash
# 1. Run migrations
python manage.py migrate users

# 2. Create profiles for existing users
python manage.py setup_adaptive_engine

# 3. Start Celery worker
celery -A core worker -l info

# 4. Start Celery Beat (in another terminal)
celery -A core beat -l info

# 5. Test the API
curl -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/skills/adaptive-profile/
```

## 📁 File Structure

```
backend/
├── skills/
│   ├── adaptive_engine.py              # Core engine
│   ├── adaptive_tasks.py               # Celery tasks
│   ├── adaptive_serializers.py         # REST serializers
│   ├── adaptive_views.py               # REST views
│   ├── adaptive_urls.py                # URL routing
│   ├── adaptive_signals.py             # Signal handlers
│   ├── test_adaptive_engine.py         # Tests
│   ├── ADAPTIVE_ENGINE_README.md       # Full docs
│   └── management/commands/
│       └── setup_adaptive_engine.py    # Setup command
│
├── users/
│   ├── models_adaptive.py              # Models
│   ├── adaptive_admin.py               # Admin
│   └── migrations/
│       └── 0005_adaptive_models.py     # Migration
│
└── core/
    └── celery.py                       # Updated beat schedule
```

## 🔑 Key Concepts

### Ability Score (0.0-1.0)
- **0.0-0.4**: Struggling (red)
- **0.4-0.6**: Beginner (orange)
- **0.6-0.8**: Intermediate (yellow)
- **0.8-1.0**: Advanced (green)

### Preferred Difficulty (1-5)
- Auto-calculated: `ceil(ability_score * 5)`
- Used for skill reordering

### Performance Signals
1. **solve_speed_percentile**: User vs. global median
2. **consecutive_fails**: Recent consecutive failures
3. **first_attempt_pass_rate**: % of first-try passes
4. **hint_usage_rate**: % of quests with hints

### Skill Flags
- **too_easy**: Grey badge (ability ≥ 0.8, difficulty ≤ 2)
- **struggling**: Orange warning (3+ consecutive fails)
- **mastered**: Blue badge (manual or ML-based)

## 📡 API Endpoints

```
GET  /api/skills/adaptive-profile/
GET  /api/skills/adaptive-profile/signals/
GET  /api/skills/adaptive-profile/flags/
GET  /api/skills/adaptive-profile/flags/{flag_type}/
POST /api/skills/adaptive-profile/adapt/
POST /api/skills/adaptive-profile/flags/{skill_id}/{flag_type}/clear/
```

## 🧪 Testing

```bash
# Run all tests
python manage.py test skills.test_adaptive_engine -v 2

# Run specific test
python manage.py test skills.test_adaptive_engine.AdaptiveEngineTestCase.test_update_ability_score
```

## 🔧 Configuration

Edit `AdaptiveTreeEngine` constants:

```python
LEARNING_RATE = 0.15                    # Bayesian update rate
CONSECUTIVE_FAIL_THRESHOLD = 3          # Struggling flag
EASY_SKILL_THRESHOLD = 0.8              # Too-easy flag
EASY_SKILL_DIFFICULTY_CAP = 2           # Max difficulty for too-easy
PERFORMANCE_WINDOW_DAYS = 30            # Lookback period
```

## 📊 Bayesian Formula

```
new_score = old_score + learning_rate * (outcome - old_score)

Outcomes:
- 1.0: Fast first-pass (< 5 seconds)
- 0.75: First-pass (≥ 5 seconds)
- 0.5: Normal pass (not first attempt)
- 0.0: Failure
```

## 🌉 Bridge Quest Generation

When user struggles (3+ consecutive fails):
1. Engine detects struggling skill
2. Calls LM Studio to generate quest at difficulty-1
3. Bridge quest has:
   - Difficulty multiplier: 0.7x
   - XP reward: 50 * (difficulty / 5)
   - Estimated time: 10 minutes

## 🔄 Workflow

```
Quest Submission
    ↓
Signal Handler Triggered
    ↓
update_ability_score_on_submission (async)
    ↓
Determine outcome (1.0, 0.75, 0.5, 0.0)
    ↓
Apply Bayesian formula
    ↓
Update preferred_difficulty
    ↓
adapt_tree_for_user (async)
    ↓
Collect signals
    ↓
Reorder skills
    ↓
Flag too-easy skills
    ↓
Flag struggling skills
    ↓
Generate bridge quests
    ↓
Log adjustment
```

## 🎯 Skill Reordering

```
Preferred Difficulty = 3

Ideal Range (2-4):     [Skill2, Skill3, Skill4]  ← Shown first
Below Range (1):       [Skill1]                   ← Shown second
Above Range (5+):      [Skill5, Skill6]           ← Shown last
```

## 📈 Periodic Adaptation

Runs daily at 2 AM UTC:
1. Gets all users active in last 24h
2. Queues `adapt_tree_for_user` for each
3. Runs asynchronously

## 🐛 Troubleshooting

### Celery Tasks Not Running
```bash
# Check worker
celery -A core inspect active

# Check broker
redis-cli ping

# Check registration
celery -A core inspect registered | grep adaptive
```

### Ability Score Not Updating
```bash
# Check signal handler
python manage.py shell
from django.db.models.signals import post_save
from quests.models import QuestSubmission
print(post_save.receivers)

# Check task queue
celery -A core inspect active_queues
```

### Bridge Quest Generation Fails
```bash
# Check LM Studio
curl http://localhost:1234/v1/models

# Check logs
tail -f logs/django.log | grep bridge
```

## 📚 Documentation Files

1. **ADAPTIVE_ENGINE_README.md** - Complete technical docs
2. **ADAPTIVE_ENGINE_INTEGRATION.md** - Integration guide
3. **ADAPTIVE_ENGINE_SUMMARY.md** - Implementation overview
4. **ADAPTIVE_ENGINE_VALIDATION.md** - Validation report
5. **ADAPTIVE_ENGINE_QUICK_REFERENCE.md** - This file

## 🎓 Frontend Integration

### Display Profile
```javascript
const profile = await fetch('/api/skills/adaptive-profile/').then(r => r.json());
// Display ability_score as progress bar
// Show flags on skills
```

### Reorder Skills
```javascript
const result = await fetch('/api/skills/adaptive-profile/adapt/', {method: 'POST'}).then(r => r.json());
// Reorder based on result.changes.reordered_skills
```

### Show Signals
```javascript
const signals = await fetch('/api/skills/adaptive-profile/signals/').then(r => r.json());
// Display metrics
```

## 🔍 Django Admin

- http://localhost:8000/admin/users/adaptiveprofile/
- http://localhost:8000/admin/users/userskillflag/

## 📝 Management Commands

```bash
# Create profiles for all users
python manage.py setup_adaptive_engine

# Create profile for specific user
python manage.py setup_adaptive_engine --user-id 1

# Reset all profiles to defaults
python manage.py setup_adaptive_engine --reset
```

## 🚨 Common Issues

| Issue | Solution |
|-------|----------|
| Tasks not running | Check Celery worker: `celery -A core inspect active` |
| Ability score not updating | Check signal handler registration |
| Bridge quest fails | Check LM Studio: `curl http://localhost:1234/v1/models` |
| Flags not appearing | Check UserSkillFlag records in admin |
| Performance slow | Profile adaptation task, consider caching |

## ✅ Validation Checklist

- [x] All files created
- [x] All imports correct
- [x] No syntax errors
- [x] All functionality implemented
- [x] Tests passing
- [x] Documentation complete
- [x] Production ready

## 📞 Support

1. Check ADAPTIVE_ENGINE_README.md for detailed docs
2. Review test cases in test_adaptive_engine.py
3. Check Django admin for data inspection
4. Review Celery logs for task execution

---

**Version**: 1.0.0
**Status**: Production Ready
**Last Updated**: 2026-04-28
