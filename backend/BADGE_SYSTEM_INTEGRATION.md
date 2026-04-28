# Badge System - Integration Guide

## Overview

The achievement badge system provides event-driven badge unlocking with 20 seeded badges, a BadgeChecker service, WebSocket broadcasting, and dramatic unlock animations.

## Architecture

### Backend Components

1. **Badge Models** (users/models.py)
   - Badge: Badge definition with rarity and unlock conditions
   - UserBadge: User's earned badge with seen flag

2. **BadgeChecker Service** (users/badge_checker.py)
   - Event-driven badge evaluation
   - 20 badge checkers for different unlock conditions
   - WebSocket broadcasting
   - Redis caching for performance

3. **Management Command** (users/management/commands/add_badges.py)
   - Seeds 20 badges into database
   - Idempotent (safe to run multiple times)

4. **Admin Interface** (users/badge_admin.py)
   - Badge management
   - UserBadge tracking
   - Bulk actions (mark as seen/unseen)

### Frontend Components

1. **BadgeUnlockOverlay.jsx**
   - Full-screen dramatic overlay
   - Animated badge icon (scales 10% to 100%)
   - Particle burst effect
   - Rarity-specific styling

2. **BadgeGrid.jsx**
   - Profile page badge display
   - Earned badges in color, locked in greyscale
   - Hover tooltips with descriptions
   - Responsive grid layout

## 20 Seeded Badges

### Common (4)
- **First Blood** 🩸 - Pass your first quest
- **Night Owl** 🦉 - Solve 5 quests between midnight-5am
- **Mentor's Pet** 🤖 - Have 10 AI mentor conversations
- **Comeback Kid** 💪 - Pass after 5+ consecutive failures
- **Study Group Founder** 👥 - Create a study group

### Rare (8)
- **Speed Demon** ⚡ - Solve in top 5% fastest time
- **Perfectionist** ✨ - 10 consecutive first-attempt passes
- **Tree Builder** 🌳 - Generate a custom skill tree
- **Code Archaeologist** 🏺 - Complete skill 100% on first attempts
- **Skill Master** 🎯 - Master 5 different skills
- **AI Whisperer** 🧠 - Get 10 AI evaluations with score > 0.8
- **Bug Hunter** 🐛 - Successfully debug 20 quests
- **Consistent Learner** 📚 - Login 30 days in a row

### Epic (4)
- **Streak Lord** 🔥 - Maintain 30-day login streak
- **Polyglot** 🌐 - Pass quests in all 5 languages
- **Marathon Runner** 🏃 - Complete 100 quests
- **Leaderboard Climber** 📈 - Reach top 10 on leaderboard
- **Problem Solver** 🧩 - Solve 50 different quests

### Legendary (2)
- **Arena Legend** ⚔️ - Win 50 multiplayer races
- **Legendary Grind** 👑 - Reach level 50

## Setup Instructions

### 1. Run Migrations
```bash
python manage.py migrate users
```

### 2. Seed Badges
```bash
python manage.py add_badges
```

### 3. Update Django Admin
Badges are automatically registered in Django admin.

### 4. Frontend Setup
```bash
npm install framer-motion
```

## API Integration

### Check Badges After Event
```python
from users.badge_checker import badge_checker

# After quest submission
new_badges = badge_checker.check_badges(
    user=user,
    event_type='quest_passed',
    event_data={
        'event_type': 'quest_passed',
        'solve_time_ms': 5000,
        'quest_id': quest.id
    }
)

# After login
new_badges = badge_checker.check_badges(
    user=user,
    event_type='login',
    event_data={'event_type': 'login'}
)

# After race win
new_badges = badge_checker.check_badges(
    user=user,
    event_type='race_won',
    event_data={'event_type': 'race_won'}
)
```

### WebSocket Integration
BadgeChecker broadcasts via WebSocket:
```javascript
// Frontend WebSocket handler
socket.on('badge_earned', (data) => {
  // data: {
  //   type: 'badge_earned',
  //   badge_slug: 'first_blood',
  //   badge_name: 'First Blood',
  //   badge_icon: '🩸',
  //   rarity: 'common',
  //   description: 'Pass your first quest'
  // }
  
  showBadgeUnlock(data);
});
```

## Frontend Integration

### Display Badge Unlock
```jsx
import BadgeUnlockOverlay from './components/BadgeUnlockOverlay';

function QuestPage() {
  const [unlockedBadge, setUnlockedBadge] = useState(null);

  useEffect(() => {
    // Listen for badge earned events
    socket.on('badge_earned', (badge) => {
      setUnlockedBadge(badge);
    });
  }, []);

  return (
    <>
      <BadgeUnlockOverlay
        isOpen={!!unlockedBadge}
        badge={unlockedBadge}
        onClose={() => setUnlockedBadge(null)}
      />
    </>
  );
}
```

### Display Badge Grid on Profile
```jsx
import BadgeGrid from './components/BadgeGrid';

function ProfilePage({ user }) {
  const [badges, setBadges] = useState([]);
  const [earnedBadgeIds, setEarnedBadgeIds] = useState([]);

  useEffect(() => {
    // Fetch all badges
    fetch('/api/badges/')
      .then(r => r.json())
      .then(data => setBadges(data));

    // Fetch user's earned badges
    fetch(`/api/users/${user.id}/badges/`)
      .then(r => r.json())
      .then(data => setEarnedBadgeIds(data.map(b => b.badge_id)));
  }, [user.id]);

  return (
    <BadgeGrid badges={badges} earnedBadgeIds={earnedBadgeIds} />
  );
}
```

## Event Types

### Quest Events
- `quest_passed`: User passed a quest
  - Data: `{solve_time_ms, quest_id, attempt_number}`
- `quest_failed`: User failed a quest
  - Data: `{quest_id, attempt_number}`

### User Events
- `login`: User logged in
  - Data: `{}`
- `level_up`: User leveled up
  - Data: `{new_level}`

### Multiplayer Events
- `race_won`: User won a multiplayer race
  - Data: `{race_id, opponent_count}`
- `race_lost`: User lost a multiplayer race
  - Data: `{race_id}`

### Skill Events
- `skill_completed`: User completed a skill
  - Data: `{skill_id}`
- `tree_generated`: User generated a skill tree
  - Data: `{tree_id}`

### Mentor Events
- `mentor_interaction`: User had AI mentor conversation
  - Data: `{interaction_id}`

### Study Group Events
- `study_group_created`: User created a study group
  - Data: `{group_id}`

### Leaderboard Events
- `leaderboard_update`: Leaderboard updated
  - Data: `{rank}`

## Badge Unlock Conditions

Each badge has an `unlock_condition` JSON field:

```python
{
    'event_type': 'quest_passed',  # Event that triggers check
    'criteria': {                   # Optional criteria
        'min_count': 10,
        'min_score': 0.8,
        'time_window': 'day'
    }
}
```

## Performance Considerations

### Caching
- Solve time percentiles cached for 1 hour
- Badge checks are O(n) where n = unearned badges
- Typical check time: <100ms

### Database
- Indexes on user, badge, rarity
- Unique constraint on (user, badge)
- Efficient queries with select_related

### WebSocket
- Broadcasts only to user's channel
- Non-blocking async execution
- Error handling with logging

## Testing

### Run Tests
```bash
python manage.py test users.test_badges -v 2 --settings=core.test_settings
```

### Test Coverage
- Badge model tests
- UserBadge model tests
- BadgeChecker service tests
- Integration tests
- Error handling tests

## Monitoring

### Django Admin
- View all badges: `/admin/users/badge/`
- View user badges: `/admin/users/userbadge/`
- Filter by rarity, earned date
- Bulk mark as seen/unseen

### Logs
```bash
tail -f logs/django.log | grep badge
```

## Troubleshooting

### Badge Not Appearing
1. Check badge is seeded: `python manage.py add_badges`
2. Check event is triggered: Add logging to badge_checker
3. Check WebSocket connection: Verify channel layer
4. Check frontend is listening: Verify socket.on('badge_earned')

### Overlay Not Showing
1. Check BadgeUnlockOverlay is imported
2. Check isOpen prop is true
3. Check badge prop has data
4. Check z-index (10000) is highest

### Performance Issues
1. Check database indexes: `python manage.py sqlsequencereset users`
2. Profile badge_checker: Add timing logs
3. Check Redis connection: `redis-cli ping`
4. Monitor WebSocket broadcasts: Check channel layer

## Future Enhancements

1. **Badge Tiers**: Multiple levels of same badge
2. **Badge Chains**: Unlock badge B after earning badge A
3. **Seasonal Badges**: Limited-time badges
4. **Badge Trading**: Users can trade badges
5. **Badge Leaderboard**: Rank users by badge count
6. **Badge Notifications**: Email/push notifications
7. **Badge Achievements**: Meta-achievements for collecting badges
8. **Badge Customization**: Users can customize badge display

## References

- Django Models: https://docs.djangoproject.com/en/stable/topics/db/models/
- Django Admin: https://docs.djangoproject.com/en/stable/ref/contrib/admin/
- Django Signals: https://docs.djangoproject.com/en/stable/topics/signals/
- Channels: https://channels.readthedocs.io/
- Framer Motion: https://www.framer.com/motion/
