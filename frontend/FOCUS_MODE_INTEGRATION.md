# Focus Mode - Integration Guide

## Overview

Focus Mode is a global app toggle that hides gamification elements (XP, ranks, badges, leaderboards) to help users concentrate on learning. When activated, it displays a Pomodoro timer and queues badge notifications for playback on exit.

## Architecture

### Zustand Store (store/uiStore.ts)

**State:**
- `focusMode: boolean` - Whether focus mode is active
- `pomodoroActive: boolean` - Whether timer is running
- `pomodoroTimeRemaining: number` - Seconds remaining (default: 1500 = 25 min)
- `badgeQueue: QueuedBadgeNotification[]` - Queued badges

**Actions:**
- `toggleFocusMode()` - Toggle focus mode on/off
- `setPomodoroActive(active)` - Start/pause timer
- `setPomodoroTimeRemaining(time)` - Update timer
- `resetPomodoro()` - Reset to 25 minutes
- `queueBadgeNotification(badge)` - Add badge to queue
- `dequeueBadgeNotification()` - Remove and return first badge
- `clearBadgeQueue()` - Clear all queued badges

**Persistence:**
- Focus mode state persists to localStorage as `ui_focusMode`
- On app load, focus mode class is applied to body if enabled

### Components

#### FocusModeToggle.jsx
- Moon/Sun icon button (top-right)
- Tooltip: "Focus Mode — hide XP & ranks"
- Smooth icon rotation on toggle
- Applies/removes `focus-mode` class to body

#### PomodoroTimer.jsx
- 25-minute countdown timer (bottom-right)
- Play/Pause and Reset buttons
- Progress ring animation
- Plays gentle chime (Web Audio API) on completion
- Shows "Break time!" toast notification
- Only visible when focus mode is active

#### BadgeNotificationQueue.jsx
- Plays back queued badges one by one
- 800ms delay between badges
- Uses BadgeUnlockOverlay for display
- Only active when focus mode is enabled

#### useBadgeNotifications Hook
- Listens to WebSocket `badge_earned` events
- Queues badges when focus mode is active
- Shows badges immediately when focus mode is inactive

#### useFocusResultModal Hook
- Manages ResultModal behavior in focus mode
- Applies CSS classes to hide gamification

### CSS Classes

**Global Focus Mode Styles (styles/focusMode.css):**

```css
body.focus-mode .gamification { display: none !important; }
body.focus-mode .xp-bar { display: none !important; }
body.focus-mode .level-badge { display: none !important; }
body.focus-mode .streak-indicator { display: none !important; }
body.focus-mode .leaderboard-widget { display: none !important; }
body.focus-mode .xp-reward { display: none !important; }
body.focus-mode .rank-indicator { display: none !important; }
body.focus-mode .badge-notification { display: none !important; }
body.focus-mode .result-modal-confetti { display: none !important; }
body.focus-mode .xp-counter { display: none !important; }
```

**Elements to Hide:**
- Sidebar XP bar, level badge, streak indicator
- Leaderboard widget on Dashboard
- XP reward badge on quest cards
- Rank indicators on all pages
- Badge notifications and WebSocket events
- ResultModal confetti and XP counter
- Streak milestone badges

**Elements to Keep:**
- Pass/fail status in ResultModal
- Motivational quote in ResultModal
- Action buttons (Try Again, Next Quest, View Feedback)

## Integration Steps

### 1. Add CSS Classes to Elements

Add `gamification` class to elements that should be hidden:

```jsx
// Sidebar XP bar
<div className="xp-bar gamification">...</div>

// Level badge
<div className="level-badge gamification">...</div>

// Leaderboard widget
<div className="leaderboard-widget gamification">...</div>

// XP reward on quest card
<div className="xp-reward gamification">...</div>

// Rank indicator
<div className="rank-indicator gamification">...</div>

// ResultModal confetti
<div className="result-modal-confetti gamification">...</div>

// XP counter
<div className="xp-counter gamification">...</div>
```

### 2. Import Focus Mode Components in App.jsx

```jsx
import FocusModeToggle from './components/FocusModeToggle';
import PomodoroTimer from './components/PomodoroTimer';
import BadgeNotificationQueue from './components/BadgeNotificationQueue';
import './styles/focusMode.css';
```

### 3. Add Components to App Render

```jsx
<FocusModeToggle />
<PomodoroTimer />
<BadgeNotificationQueue />
```

### 4. Integrate Badge Notifications

In your WebSocket setup or main component:

```jsx
import { useBadgeNotifications } from './hooks/useBadgeNotifications';

function MyComponent() {
  const socket = useSocket(); // Your socket instance
  useBadgeNotifications(socket);
  
  return <div>...</div>;
}
```

### 5. Update ResultModal (Optional)

Add focus mode awareness to ResultModal:

```jsx
import { useFocusResultModal } from './hooks/useFocusResultModal';

function ResultModal({ isOpen, ...props }) {
  const { focusMode } = useFocusResultModal(isOpen);
  
  return (
    <div className={`result-modal ${focusMode ? 'focus-mode-active' : ''}`}>
      {/* Content */}
    </div>
  );
}
```

## Usage

### Toggle Focus Mode

```jsx
import useUIStore from './store/uiStore';

function MyComponent() {
  const { focusMode, toggleFocusMode } = useUIStore();
  
  return (
    <button onClick={toggleFocusMode}>
      {focusMode ? 'Exit Focus Mode' : 'Enter Focus Mode'}
    </button>
  );
}
```

### Access Pomodoro Timer

```jsx
import useUIStore from './store/uiStore';

function MyComponent() {
  const {
    pomodoroActive,
    pomodoroTimeRemaining,
    setPomodoroActive,
    resetPomodoro,
  } = useUIStore();
  
  return (
    <div>
      <p>Time: {pomodoroTimeRemaining}s</p>
      <button onClick={() => setPomodoroActive(!pomodoroActive)}>
        {pomodoroActive ? 'Pause' : 'Play'}
      </button>
      <button onClick={resetPomodoro}>Reset</button>
    </div>
  );
}
```

### Queue Badge Notifications

```jsx
import useUIStore from './store/uiStore';

function MyComponent() {
  const { queueBadgeNotification } = useUIStore();
  
  const handleBadgeEarned = (badge) => {
    queueBadgeNotification({
      id: `badge_${Date.now()}`,
      badge_slug: badge.slug,
      badge_name: badge.name,
      badge_icon: badge.icon,
      rarity: badge.rarity,
      description: badge.description,
      timestamp: Date.now(),
    });
  };
  
  return <div>...</div>;
}
```

## Features

### Focus Mode Toggle
- Moon icon button (top-right)
- Tooltip on hover
- Smooth icon rotation
- Persists to localStorage
- Applies `focus-mode` class to body

### Pomodoro Timer
- 25-minute countdown
- Play/Pause button
- Reset button
- Progress ring animation
- Gentle chime on completion (Web Audio API)
- "Break time!" toast notification
- Only visible in focus mode

### Badge Notification Queue
- Queues badges when focus mode is active
- Plays back one by one on exit
- 800ms delay between badges
- Uses dramatic BadgeUnlockOverlay
- Automatic playback

### Gamification Hiding
- Sidebar XP bar, level badge, streak
- Leaderboard widget
- XP rewards on quest cards
- Rank indicators
- Badge notifications
- ResultModal confetti and XP counter
- Streak milestones

### Fade Transition
- 300ms fade when toggling focus mode
- Signals mode change to user
- Respects prefers-reduced-motion

## CSS Classes Reference

### Elements to Add Gamification Class

```jsx
// Sidebar
<div className="xp-bar gamification" />
<div className="level-badge gamification" />
<div className="streak-indicator gamification" />

// Dashboard
<div className="leaderboard-widget gamification" />

// Quest Cards
<div className="xp-reward gamification" />

// All Pages
<div className="rank-indicator gamification" />

// Notifications
<div className="badge-notification gamification" />

// ResultModal
<div className="result-modal-confetti gamification" />
<div className="xp-counter gamification" />
<div className="streak-milestone gamification" />
```

## Accessibility

- Respects `prefers-reduced-motion` media query
- Semantic HTML with ARIA labels
- Keyboard navigation support
- High contrast colors
- Clear visual feedback

## Performance

- Zustand store for efficient state management
- CSS class-based hiding (no re-renders)
- Lazy component loading
- Web Audio API for chime (no external files)
- Efficient badge queue processing

## Browser Support

- Modern browsers with Web Audio API support
- Fallback for older browsers (chime won't play)
- localStorage for persistence
- CSS backdrop-filter support

## Troubleshooting

### Focus Mode Not Persisting
- Check localStorage is enabled
- Verify `ui_focusMode` key in localStorage
- Check browser console for errors

### Pomodoro Timer Not Showing
- Verify focus mode is active
- Check z-index conflicts (should be 999)
- Verify PomodoroTimer component is imported

### Badges Not Queuing
- Check WebSocket connection
- Verify `useBadgeNotifications` hook is called
- Check browser console for errors
- Verify badge data structure matches interface

### Gamification Elements Still Visible
- Verify `gamification` class is added to elements
- Check CSS file is imported
- Verify `focus-mode` class is on body
- Check CSS specificity (use `!important` if needed)

### Chime Not Playing
- Check browser audio permissions
- Verify Web Audio API is supported
- Check browser console for errors
- Try different browser

## Future Enhancements

1. **Custom Timer Duration** - Allow users to set custom focus session length
2. **Break Timer** - Add 5-minute break timer after focus session
3. **Statistics** - Track focus sessions and productivity
4. **Notifications** - Desktop notifications for timer completion
5. **Themes** - Different color themes for focus mode
6. **Keyboard Shortcuts** - Quick toggle with keyboard shortcut
7. **Focus Goals** - Set daily focus time goals
8. **Analytics** - Track focus mode usage and effectiveness

## References

- Zustand: https://github.com/pmndrs/zustand
- Web Audio API: https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API
- Framer Motion: https://www.framer.com/motion/
- localStorage: https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage

---

**Version**: 1.0.0
**Status**: Production Ready
**Last Updated**: 2026-04-28

