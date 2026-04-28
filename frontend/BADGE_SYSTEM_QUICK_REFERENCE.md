# Badge System - Quick Reference

## Components

### BadgeUnlockOverlay
```jsx
<BadgeUnlockOverlay
  isOpen={boolean}
  badge={{
    id: number,
    slug: string,
    name: string,
    description: string,
    icon_emoji: string,
    rarity: 'common' | 'rare' | 'epic' | 'legendary'
  }}
  onClose={function}
/>
```

### BadgeGrid
```jsx
<BadgeGrid
  badges={Badge[]}
  earnedBadgeIds={number[]}
/>
```

## Usage Example

```jsx
import { useState, useEffect } from 'react';
import BadgeUnlockOverlay from './components/BadgeUnlockOverlay';
import BadgeGrid from './components/BadgeGrid';

function App() {
  const [unlockedBadge, setUnlockedBadge] = useState(null);
  const [badges, setBadges] = useState([]);
  const [earnedIds, setEarnedIds] = useState([]);

  useEffect(() => {
    // Listen for badge earned events
    socket.on('badge_earned', (badge) => {
      setUnlockedBadge(badge);
    });

    // Fetch badges
    fetch('/api/badges/')
      .then(r => r.json())
      .then(setBadges);

    // Fetch earned badges
    fetch('/api/user/badges/')
      .then(r => r.json())
      .then(data => setEarnedIds(data.map(b => b.badge_id)));
  }, []);

  return (
    <>
      <BadgeUnlockOverlay
        isOpen={!!unlockedBadge}
        badge={unlockedBadge}
        onClose={() => setUnlockedBadge(null)}
      />
      <BadgeGrid badges={badges} earnedBadgeIds={earnedIds} />
    </>
  );
}
```

## Rarity Colors

```javascript
const RARITY_COLORS = {
  common: '#94a3b8',      // Grey
  rare: '#3b82f6',        // Blue
  epic: '#a855f7',        // Purple
  legendary: '#f59e0b',   // Orange
};
```

## 20 Badges

### Common (5)
- 🩸 First Blood - Pass first quest
- 🦉 Night Owl - Solve 5 quests midnight-5am
- 🤖 Mentor's Pet - 10 AI mentor conversations
- 💪 Comeback Kid - Pass after 5+ fails
- 👥 Study Group Founder - Create study group

### Rare (8)
- ⚡ Speed Demon - Top 5% solve time
- ✨ Perfectionist - 10 consecutive first-attempts
- 🌳 Tree Builder - Generate skill tree
- 🏺 Code Archaeologist - Skill 100% first-attempts
- 🎯 Skill Master - Master 5 skills
- 🧠 AI Whisperer - 10 evals score > 0.8
- 🐛 Bug Hunter - Debug 20 quests
- 📚 Consistent Learner - Login 30 days

### Epic (5)
- 🔥 Streak Lord - 30-day streak
- 🌐 Polyglot - All 5 languages
- 🏃 Marathon Runner - 100 quests
- 📈 Leaderboard Climber - Top 10
- 🧩 Problem Solver - 50 quests

### Legendary (2)
- ⚔️ Arena Legend - Win 50 races
- 👑 Legendary Grind - Level 50

## WebSocket Events

```javascript
socket.on('badge_earned', (data) => {
  // {
  //   type: 'badge_earned',
  //   badge_slug: 'first_blood',
  //   badge_name: 'First Blood',
  //   badge_icon: '🩸',
  //   rarity: 'common',
  //   description: 'Pass your first quest'
  // }
});
```

## CSS Classes

### BadgeUnlockOverlay
- `.badge-unlock-backdrop` - Full-screen overlay
- `.badge-unlock-card` - Main card
- `.badge-${rarity}` - Rarity-specific styling
- `.badge-icon` - Badge emoji
- `.particle` - Particle effect

### BadgeGrid
- `.badge-grid-container` - Container
- `.badge-grid` - Grid layout
- `.badge-item` - Individual badge
- `.badge-${rarity}` - Rarity styling
- `.earned` / `.locked` - State styling
- `.badge-tooltip` - Hover tooltip

## Customization

### Change Colors
```css
.badge-unlock-card.badge-legendary {
  --rarity-color: #f59e0b;
  --rarity-glow: rgba(245, 158, 11, 0.5);
}
```

### Change Animation Speed
```jsx
// In BadgeUnlockOverlay.jsx
animate={{ scale: 1 }}
transition={{
  type: 'spring',
  stiffness: 100,  // Increase for faster
  damping: 15,
  duration: 0.6,
}}
```

### Change Particle Count
```jsx
// In BadgeUnlockOverlay.jsx
const newParticles = Array.from({ length: 50 }, ...)  // Change 30 to 50
```

## Dependencies

```json
{
  "framer-motion": "^10.0.0",
  "react": "^18.0.0"
}
```

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
- Mobile browsers (iOS Safari 14+, Chrome Android)

## Performance Tips

1. **Memoize Components**:
   ```jsx
   export default React.memo(BadgeUnlockOverlay);
   ```

2. **Lazy Load**:
   ```jsx
   const BadgeUnlockOverlay = lazy(() => import('./BadgeUnlockOverlay'));
   ```

3. **Optimize Animations**:
   - Use `will-change` CSS
   - Reduce particles on mobile
   - Use `transform` instead of `left/top`

## Accessibility

### Keyboard Navigation
- Tab through buttons
- Enter to activate
- Escape to close

### Screen Readers
- Semantic HTML
- ARIA labels
- Alt text for icons

### Motion Preferences
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation: none !important;
    transition: none !important;
  }
}
```

## Troubleshooting

### Overlay Not Showing
1. Check `isOpen` prop is true
2. Check `badge` prop has data
3. Check z-index (10000) is highest
4. Check CSS is loaded

### Animations Not Working
1. Check Framer Motion is installed
2. Check CSS is loaded
3. Check browser supports animations
4. Check `prefers-reduced-motion` setting

### Grid Not Displaying
1. Check `badges` array has data
2. Check `earnedBadgeIds` array is correct
3. Check CSS is loaded
4. Check responsive breakpoints

### WebSocket Not Working
1. Check socket connection
2. Check event name matches
3. Check backend is broadcasting
4. Check channel layer is configured

## References

- [Framer Motion Docs](https://www.framer.com/motion/)
- [React Hooks](https://react.dev/reference/react/hooks)
- [CSS Grid](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Grid_Layout)
- [Glassmorphism](https://glassmorphism.com/)

---

**Version**: 1.0.0
**Last Updated**: 2026-04-28
