# SkillTree AI - Adaptive Learning Engine

## Overview

The Adaptive Learning Engine dynamically adjusts the skill tree based on user performance, implementing Bayesian ability scoring, difficulty-based skill reordering, skill flagging, and bridge quest generation for struggling learners.

## Architecture

### Core Components

1. **AdaptiveTreeEngine** (`adaptive_engine.py`)
   - Main orchestrator for adaptive logic
   - Collects performance signals
   - Updates ability scores using Bayesian formula
   - Manages skill reordering and flagging
   - Generates bridge quests for struggling users

2. **AdaptiveProfile Model** (`models_adaptive.py`)
   - Stores user's ability score (0.0-1.0)
   - Tracks preferred difficulty (1-5)
   - Maintains adjustment history with timestamps and reasons

3. **UserSkillFlag Model** (`models_adaptive.py`)
   - Flags skills as "too_easy", "struggling", or "mastered"
   - Stores reason for flagging
   - Enables UI to show visual indicators (grey for easy, orange for struggling)

4. **Celery Tasks** (`adaptive_tasks.py`)
   - `adapt_tree_for_user`: Main adaptation task
   - `update_ability_score_on_submission`: Updates score after quest completion
   - `periodic_tree_adaptation`: Runs every 24h for active users

5. **Signal Handlers** (`adaptive_signals.py`)
   - Automatically triggers adaptation on quest submission completion
   - Decouples adaptation from quest submission logic

6. **REST API** (`adaptive_views.py`, `adaptive_urls.py`)
   - GET `/api/skills/adaptive-profile/`: Get user's adaptive profile
   - GET `/api/skills/adaptive-profile/signals/`: Get performance signals
   - GET `/api/skills/adaptive-profile/flags/`: Get all skill flags
   - GET `/api/skills/adaptive-profile/flags/{flag_type}/`: Get flags by type
   - POST `/api/skills/adaptive-profile/adapt/`: Manually trigger adaptation
   - POST `/api/skills/adaptive-profile/flags/{skill_id}/{flag_type}/clear/`: Clear a flag

## Performance Signals

The engine collects four key performance metrics:

### 1. Solve Speed Percentile
- Compares user's average solve time vs. global median
- Normalized to [0, 1] range
- 1.0 = faster than median, 0.0 = slower than median

### 2. Consecutive Fails
- Count of consecutive failed submissions from most recent
- Triggers "struggling" flag when ≥ 3

### 3. First Attempt Pass Rate
- Percentage of quests passed on first try (last 10 quests)
- Indicates learning efficiency

### 4. Hint Usage Rate
- Percentage of quests where user requested a hint
- Indicates need for guidance

## Bayesian Ability Scoring

The ability score is updated using the formula:

```
new_score = old_score + learning_rate * (outcome - old_score)
```

Where:
- `learning_rate = 0.15` (configurable)
- `outcome = 1.0` for fast first-pass
- `outcome = 0.75` for first-pass (slower)
- `outcome = 0.5` for normal pass
- `outcome = 0.0` for failure

The score is bounded to [0.0, 1.0]:
- 0.0-0.4: Struggling
- 0.4-0.6: Beginner
- 0.6-0.8: Intermediate
- 0.8-1.0: Advanced

## Difficulty Reordering

Skills are reordered based on preferred difficulty:

1. **Ideal Range** (±1 level): Prioritized first
2. **Below Range**: Acceptable, shown second
3. **Above Range** (2+ levels): Deprioritized, shown last

Example: If preferred_difficulty = 3:
- Difficulty 2-4: Ideal (shown first)
- Difficulty 1: Acceptable (shown second)
- Difficulty 5: Too hard (shown last)

## Skill Flagging

### Too Easy Flag
- **Condition**: `ability_score ≥ 0.8 AND skill.difficulty ≤ 2`
- **UI**: Shown as grey on skill tree
- **Action**: User can skip or review

### Struggling Flag
- **Condition**: `consecutive_fails ≥ 3`
- **UI**: Shown as orange warning on skill tree
- **Action**: Bridge quest generated automatically

### Mastered Flag
- **Condition**: Manual or future ML-based detection
- **UI**: Shown as blue badge on skill tree

## Bridge Quest Generation

When a user struggles (3+ consecutive failures):

1. Engine detects struggling skill
2. Calls LM Studio to generate bridge quest at difficulty-1 level
3. Bridge quest has:
   - Reduced difficulty multiplier (0.7x)
   - Lower XP reward (50 * difficulty/5)
   - Shorter estimated time (10 minutes)
   - Simpler test cases

Example: If user struggles with "Advanced Python" (difficulty 4):
- Bridge quest generated at difficulty 3
- Helps user build confidence before retrying original skill

## Workflow

### On Quest Submission
1. User submits quest code
2. Executor runs tests and evaluates code
3. QuestSubmission saved with status (passed/failed)
4. Signal handler triggers:
   - `update_ability_score_on_submission` task
   - `adapt_tree_for_user` task

### Ability Score Update
1. Determine outcome based on submission status and speed
2. Apply Bayesian formula
3. Update AdaptiveProfile.ability_score
4. Auto-update preferred_difficulty

### Tree Adaptation
1. Collect performance signals
2. Reorder skills by difficulty
3. Flag too-easy skills
4. Flag struggling skills and generate bridge quests
5. Log adjustment to adjustment_history

### Periodic Adaptation (24h)
1. Celery Beat triggers `periodic_tree_adaptation`
2. Gets all users active in last 24h
3. Queues `adapt_tree_for_user` for each user
4. Runs asynchronously without blocking

## Configuration

All constants are defined in `AdaptiveTreeEngine`:

```python
LEARNING_RATE = 0.15                    # Bayesian update rate
ABILITY_MIN = 0.0                       # Minimum ability score
ABILITY_MAX = 1.0                       # Maximum ability score
DIFFICULTY_TIERS = 5                    # Number of difficulty levels
CONSECUTIVE_FAIL_THRESHOLD = 3          # Threshold for struggling flag
EASY_SKILL_THRESHOLD = 0.8              # Threshold for too_easy flag
EASY_SKILL_DIFFICULTY_CAP = 2           # Max difficulty for too_easy
FIRST_ATTEMPT_WINDOW = 10               # Window for first-attempt rate
PERFORMANCE_WINDOW_DAYS = 30            # Days to look back for signals
```

## Database Schema

### AdaptiveProfile
```
- user (OneToOne)
- ability_score (Float, 0.0-1.0)
- preferred_difficulty (Int, 1-5)
- adjustment_history (JSON)
- last_adjusted (DateTime)
- created_at (DateTime)
```

### UserSkillFlag
```
- user (ForeignKey)
- skill (ForeignKey)
- flag (CharField: too_easy, struggling, mastered)
- reason (TextField)
- created_at (DateTime)
- updated_at (DateTime)
- Unique constraint: (user, skill, flag)
```

## API Examples

### Get Adaptive Profile
```bash
curl -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/skills/adaptive-profile/
```

Response:
```json
{
  "ability_score": 0.65,
  "preferred_difficulty": 3,
  "flags": [
    {
      "skill_id": 1,
      "skill_title": "Python Basics",
      "skill_difficulty": 1,
      "flag": "too_easy",
      "reason": "Ability score indicates mastery of this difficulty level",
      "created_at": "2026-04-28T10:30:00Z"
    },
    {
      "skill_id": 5,
      "skill_title": "Advanced Python",
      "skill_difficulty": 4,
      "flag": "struggling",
      "reason": "Consecutive failures: 3",
      "created_at": "2026-04-28T11:00:00Z"
    }
  ],
  "last_adjusted": "2026-04-28T11:15:00Z",
  "adjustment_history_summary": {
    "total_adjustments": 5,
    "recent": [...]
  }
}
```

### Get Performance Signals
```bash
curl -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/skills/adaptive-profile/signals/
```

Response:
```json
{
  "status": "success",
  "signals": {
    "solve_speed_percentile": 0.72,
    "consecutive_fails": 1,
    "first_attempt_pass_rate": 0.8,
    "hint_usage_rate": 0.2
  }
}
```

### Trigger Manual Adaptation
```bash
curl -X POST -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/skills/adaptive-profile/adapt/
```

Response:
```json
{
  "status": "success",
  "message": "Tree adaptation triggered",
  "changes": {
    "reordered_skills": [3, 2, 5, 1],
    "flagged_too_easy": [1],
    "flagged_struggling": [5],
    "bridge_quests_generated": [42]
  }
}
```

## Testing

Run the test suite:

```bash
python manage.py test skills.test_adaptive_engine
```

Tests cover:
- Engine initialization
- Performance signal collection
- Ability score updates
- Difficulty reordering
- Skill flagging
- Bridge quest generation
- Model constraints
- Edge cases

## Integration with Frontend

### Skill Tree Visualization
1. Fetch adaptive profile to get flags
2. Render skills with visual indicators:
   - Grey: too_easy flag
   - Orange: struggling flag
   - Blue: mastered flag
3. Reorder skills based on `reordered_skills` from adaptation

### User Dashboard
1. Display ability_score as progress bar (0-100%)
2. Show preferred_difficulty as target level
3. List recent adjustments from adjustment_history
4. Show performance signals as metrics

### Skill Detail Page
1. Check for flags on this skill
2. If struggling flag: highlight bridge quest
3. If too_easy flag: suggest skipping or reviewing

## Monitoring & Debugging

### Django Admin
- View AdaptiveProfile for each user
- See ability score with color coding
- Browse adjustment history
- Manage UserSkillFlags

### Logs
- Check `skills.adaptive_engine` logger for signal collection
- Check `skills.adaptive_tasks` logger for task execution
- Monitor Celery task queue for failures

### Performance
- Adaptation runs asynchronously (non-blocking)
- Performance signals cached for 30 days
- Bridge quest generation uses LM Studio (may be slow)
- Consider caching bridge quest templates

## Future Enhancements

1. **ML-based Mastery Detection**: Automatically flag mastered skills
2. **Adaptive Learning Paths**: Suggest optimal skill sequences
3. **Peer Comparison**: Show percentile vs. other users
4. **Spaced Repetition**: Recommend review timing
5. **Learning Style Detection**: Adjust difficulty based on learning style
6. **Collaborative Filtering**: Recommend skills based on similar users
7. **A/B Testing**: Test different adaptation strategies
8. **Real-time Feedback**: Update ability score during quest (not just after)

## Troubleshooting

### Bridge Quest Generation Fails
- Check LM Studio is running: `curl http://localhost:1234/v1/models`
- Check logs for LM Studio errors
- Fallback: Create bridge quests manually

### Ability Score Not Updating
- Check Celery worker is running: `celery -A core worker -l info`
- Check signal handler is registered: `python manage.py shell`
  ```python
  from django.db.models.signals import post_save
  from quests.models import QuestSubmission
  print(post_save.receivers)
  ```
- Check task queue: `celery -A core inspect active`

### Flags Not Appearing
- Check UserSkillFlag records in admin
- Verify adaptation ran: check adjustment_history
- Check frontend is fetching flags endpoint

### Performance Issues
- Profile adaptation task: `celery -A core inspect stats`
- Consider batching adaptation for multiple users
- Cache performance signals in Redis
- Limit adjustment_history to last 100 entries

## References

- Bayesian Learning: https://en.wikipedia.org/wiki/Bayesian_inference
- Adaptive Learning: https://en.wikipedia.org/wiki/Adaptive_learning
- Difficulty Scaling: https://en.wikipedia.org/wiki/Dynamic_difficulty
- Celery Documentation: https://docs.celeryproject.io/
- Django Signals: https://docs.djangoproject.com/en/stable/topics/signals/
