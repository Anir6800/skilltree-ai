# Adaptive Engine Integration Guide

## Quick Start

### 1. Run Migrations
```bash
python manage.py migrate users
```

This creates:
- `users_adaptiveprofile` table
- `users_userskillflag` table

### 2. Update Django Settings
The adaptive engine is already configured in `core/settings.py`:
- Celery broker and result backend configured
- Redis channel layer configured
- All required apps installed

### 3. Start Celery Worker
```bash
celery -A core worker -l info
```

### 4. Start Celery Beat (for periodic adaptation)
```bash
celery -A core beat -l info
```

### 5. Test the Implementation

#### Create a test user and skill
```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from skills.models import Skill, SkillProgress
from skills.adaptive_engine import AdaptiveTreeEngine
from users.models_adaptive import AdaptiveProfile

User = get_user_model()

# Create user
user = User.objects.create_user(username='testuser', password='test123')

# Create skill
skill = Skill.objects.create(
    title='Python Basics',
    description='Learn Python',
    category='programming',
    difficulty=1
)

# Create skill progress
SkillProgress.objects.create(user=user, skill=skill, status='available')

# Initialize engine
engine = AdaptiveTreeEngine(user.id)

# Collect signals
signals = engine.collect_performance_signals()
print(f"Signals: {signals}")

# Update ability score
new_score = engine.update_ability_score(0.75)
print(f"New ability score: {new_score}")

# Adapt tree
changes = engine.adapt_tree_for_user()
print(f"Changes: {changes}")

# Check profile
profile = AdaptiveProfile.objects.get(user=user)
print(f"Profile: {profile}")
```

### 6. Access API Endpoints

#### Get adaptive profile
```bash
curl -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/skills/adaptive-profile/
```

#### Get performance signals
```bash
curl -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/skills/adaptive-profile/signals/
```

#### Get skill flags
```bash
curl -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/skills/adaptive-profile/flags/
```

#### Trigger manual adaptation
```bash
curl -X POST -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/skills/adaptive-profile/adapt/
```

## File Structure

```
backend/
├── skills/
│   ├── adaptive_engine.py          # Core engine logic
│   ├── adaptive_tasks.py           # Celery tasks
│   ├── adaptive_serializers.py     # REST serializers
│   ├── adaptive_views.py           # REST views
│   ├── adaptive_urls.py            # URL routing
│   ├── adaptive_signals.py         # Django signals
│   ├── test_adaptive_engine.py     # Test suite
│   ├── ADAPTIVE_ENGINE_README.md   # Full documentation
│   └── apps.py                     # Updated with signal registration
│
├── users/
│   ├── models_adaptive.py          # AdaptiveProfile & UserSkillFlag models
│   ├── adaptive_admin.py           # Django admin configuration
│   ├── admin.py                    # Updated to import adaptive admin
│   └── migrations/
│       └── 0005_adaptive_models.py # Migration file
│
└── core/
    ├── celery.py                   # Updated with periodic task
    └── settings.py                 # Already configured
```

## Key Features Implemented

✅ **AdaptiveTreeEngine**
- Performance signal collection (solve_speed_percentile, consecutive_fails, first_attempt_pass_rate, hint_usage_rate)
- Bayesian ability score updates
- Preferred difficulty auto-calculation
- Skill reordering by difficulty
- Too-easy skill flagging
- Struggling skill flagging
- Bridge quest generation

✅ **AdaptiveProfile Model**
- ability_score (0.0-1.0)
- preferred_difficulty (1-5)
- adjustment_history (JSON log)
- last_adjusted timestamp

✅ **UserSkillFlag Model**
- Flags: too_easy, struggling, mastered
- Reason tracking
- Unique constraint per user-skill-flag

✅ **Celery Tasks**
- adapt_tree_for_user (event-driven)
- update_ability_score_on_submission (event-driven)
- periodic_tree_adaptation (24h schedule)

✅ **REST API**
- GET /api/skills/adaptive-profile/
- GET /api/skills/adaptive-profile/signals/
- GET /api/skills/adaptive-profile/flags/
- GET /api/skills/adaptive-profile/flags/{flag_type}/
- POST /api/skills/adaptive-profile/adapt/
- POST /api/skills/adaptive-profile/flags/{skill_id}/{flag_type}/clear/

✅ **Django Admin**
- AdaptiveProfile admin with color-coded ability scores
- UserSkillFlag admin with flag visualization
- Adjustment history display

✅ **Signal Integration**
- Automatic trigger on quest submission
- Non-blocking async execution

✅ **Comprehensive Tests**
- 20+ test cases
- Model tests
- Engine logic tests
- Edge case coverage

## Configuration

### Bayesian Learning Rate
Edit `AdaptiveTreeEngine.LEARNING_RATE` (default: 0.15)
- Higher = faster learning
- Lower = more conservative updates

### Difficulty Thresholds
Edit constants in `AdaptiveTreeEngine`:
- `CONSECUTIVE_FAIL_THRESHOLD = 3` (struggling flag)
- `EASY_SKILL_THRESHOLD = 0.8` (too_easy flag)
- `EASY_SKILL_DIFFICULTY_CAP = 2` (max difficulty for too_easy)

### Performance Window
Edit `PERFORMANCE_WINDOW_DAYS = 30` to change lookback period

### Periodic Adaptation Schedule
Edit `core/celery.py` beat_schedule:
```python
'periodic-tree-adaptation-daily': {
    'task': 'skills.adaptive_tasks.periodic_tree_adaptation',
    'schedule': crontab(hour=2, minute=0),  # 2 AM UTC daily
},
```

## Frontend Integration

### Display Adaptive Profile
```javascript
const response = await fetch('/api/skills/adaptive-profile/', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const profile = await response.json();

// Display ability score as progress bar
const abilityPercent = profile.ability_score * 100;

// Display flags on skills
profile.flags.forEach(flag => {
  const skillElement = document.querySelector(`[data-skill-id="${flag.skill_id}"]`);
  if (flag.flag === 'too_easy') {
    skillElement.classList.add('flag-too-easy');  // Grey
  } else if (flag.flag === 'struggling') {
    skillElement.classList.add('flag-struggling');  // Orange
  }
});
```

### Reorder Skills
```javascript
const response = await fetch('/api/skills/adaptive-profile/adapt/', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` }
});
const result = await response.json();

// Reorder skills based on result.changes.reordered_skills
const skillOrder = result.changes.reordered_skills;
```

### Show Performance Signals
```javascript
const response = await fetch('/api/skills/adaptive-profile/signals/', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const signals = await response.json();

// Display metrics
console.log(`Speed: ${(signals.signals.solve_speed_percentile * 100).toFixed(0)}%`);
console.log(`First attempt rate: ${(signals.signals.first_attempt_pass_rate * 100).toFixed(0)}%`);
console.log(`Consecutive fails: ${signals.signals.consecutive_fails}`);
console.log(`Hint usage: ${(signals.signals.hint_usage_rate * 100).toFixed(0)}%`);
```

## Monitoring

### Check Celery Tasks
```bash
celery -A core inspect active
celery -A core inspect stats
celery -A core inspect registered
```

### View Logs
```bash
# Adaptive engine logs
tail -f logs/django.log | grep adaptive_engine

# Celery task logs
tail -f logs/celery.log
```

### Django Admin
- http://localhost:8000/admin/users/adaptiveprofile/
- http://localhost:8000/admin/users/userskillflag/

## Troubleshooting

### Celery Tasks Not Running
1. Check worker is running: `celery -A core inspect active`
2. Check broker connection: `redis-cli ping` (should return PONG)
3. Check task is registered: `celery -A core inspect registered | grep adaptive`

### Ability Score Not Updating
1. Check signal handler: `python manage.py shell`
   ```python
   from django.db.models.signals import post_save
   from quests.models import QuestSubmission
   print(post_save.receivers)
   ```
2. Check task queue: `celery -A core inspect active_queues`
3. Check logs for errors

### Bridge Quest Generation Fails
1. Check LM Studio: `curl http://localhost:1234/v1/models`
2. Check logs: `tail -f logs/django.log | grep bridge`
3. Fallback: Create bridge quests manually

### Performance Issues
1. Profile adaptation: `celery -A core inspect stats`
2. Check database indexes: `python manage.py sqlsequencereset users | python manage.py dbshell`
3. Consider caching signals in Redis

## Next Steps

1. **Frontend Integration**: Update React components to display flags and reordered skills
2. **Analytics**: Track adaptation effectiveness (do flagged skills improve?)
3. **A/B Testing**: Test different learning rates and thresholds
4. **ML Enhancement**: Use ML to predict optimal difficulty
5. **Spaced Repetition**: Recommend review timing based on ability score
6. **Peer Comparison**: Show percentile vs. other users

## Support

For issues or questions:
1. Check ADAPTIVE_ENGINE_README.md for detailed documentation
2. Review test cases in test_adaptive_engine.py
3. Check Django admin for data inspection
4. Review Celery logs for task execution details
