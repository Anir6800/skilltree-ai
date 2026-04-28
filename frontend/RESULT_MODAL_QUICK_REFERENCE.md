# ResultModal - Quick Reference

## Component Props

```jsx
<ResultModal
  isOpen={boolean}                    // Show/hide modal
  submission={QuestSubmission}        // Submission data
  quote={string}                      // Motivational quote
  xpAwarded={number}                  // XP to animate
  streakMilestone={number}            // Streak milestone (optional)
  onTryAgain={function}               // Try again callback
  onNextQuest={function}              // Next quest callback
  onViewFeedback={function}           // View feedback callback
  onClose={function}                  // Close callback
/>
```

## Usage Example

```jsx
import ResultModal from './components/ResultModal';
import { useState } from 'react';

function QuestPage() {
  const [showResult, setShowResult] = useState(false);
  const [submission, setSubmission] = useState(null);
  const [quote, setQuote] = useState('');
  const [xpAwarded, setXpAwarded] = useState(0);

  const handleSubmit = async (code) => {
    // Submit quest
    const res = await fetch('/api/quests/submit/', {
      method: 'POST',
      body: JSON.stringify({ quest_id, code, language }),
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();

    // Wait for pipeline
    let result = data;
    while (result.status === 'pending' || result.status === 'running') {
      await new Promise(r => setTimeout(r, 1000));
      const statusRes = await fetch(`/api/quests/submissions/${data.id}/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      result = await statusRes.json();
    }

    // Fetch quote
    const quoteRes = await fetch(`/api/ai-evaluation/quotes/${data.id}/`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const quoteData = await quoteRes.json();

    // Show result
    setSubmission(result);
    setQuote(quoteData.quote);
    setXpAwarded(result.xp_awarded || 0);
    setShowResult(true);
  };

  return (
    <>
      <ResultModal
        isOpen={showResult}
        submission={submission}
        quote={quote}
        xpAwarded={xpAwarded}
        streakMilestone={submission?.streak_milestone}
        onTryAgain={() => {
          setShowResult(false);
          // Reload quest
        }}
        onNextQuest={() => {
          setShowResult(false);
          // Navigate to next quest
        }}
        onViewFeedback={() => {
          setShowResult(false);
          // Show feedback panel
        }}
        onClose={() => setShowResult(false)}
      />
    </>
  );
}
```

## Features

### Animations
- ✅ Typewriter effect for quote (30ms per character)
- ✅ Confetti for passed quests
- ✅ XP counter animation
- ✅ Streak badge pulse
- ✅ Button hover effects
- ✅ Status icon animations

### Design
- ✅ Glassmorphism with backdrop blur
- ✅ Dark gradients
- ✅ Floating panels
- ✅ Status-specific colors (green/red/orange)
- ✅ Motion-led hierarchy

### Responsive
- ✅ Mobile-first design
- ✅ Touch-friendly buttons
- ✅ Readable on all screen sizes
- ✅ Breakpoint at 640px

### Accessibility
- ✅ Respects `prefers-reduced-motion`
- ✅ Semantic HTML
- ✅ Keyboard navigation
- ✅ ARIA labels

## Styling

### CSS Classes
- `.result-modal-backdrop` - Full-screen overlay
- `.result-modal-card` - Main card container
- `.result-passed` - Green gradient for passed
- `.result-failed` - Red gradient for failed
- `.result-flagged` - Orange gradient for flagged
- `.motivational-quote` - Quote text styling
- `.stats-grid` - Stats display grid
- `.xp-counter` - XP animation container
- `.streak-badge` - Streak milestone badge
- `.action-buttons` - Button container

### Colors
- **Passed**: #22c55e (green)
- **Failed**: #ef4444 (red)
- **Flagged**: #f59e0b (orange)
- **XP**: #fbbf24 (yellow)
- **Streak**: #fca5a5 (light red)

## Dependencies

```json
{
  "framer-motion": "^10.0.0",
  "react-confetti": "^6.0.0"
}
```

Install:
```bash
npm install framer-motion react-confetti
```

## API Integration

### Get Quote
```javascript
const response = await fetch(
  `/api/ai-evaluation/quotes/${submissionId}/`,
  { headers: { 'Authorization': `Bearer ${token}` } }
);
const data = await response.json();
// data.quote - motivational quote string
```

### Check Service
```javascript
const response = await fetch(
  '/api/ai-evaluation/quotes/service/status/',
  { headers: { 'Authorization': `Bearer ${token}` } }
);
const data = await response.json();
// data.available - boolean
```

## Submission Data Structure

```javascript
{
  id: number,
  quest: {
    id: number,
    title: string,
    skill: {
      id: number,
      title: string
    },
    test_cases: array
  },
  user: {
    id: number,
    username: string,
    streak_days: number
  },
  status: 'passed' | 'failed' | 'flagged',
  execution_result: {
    time_ms: number,
    tests_passed: number,
    output: string
  },
  ai_feedback: {
    score: number
  },
  xp_awarded: number,
  streak_milestone: number | null
}
```

## Customization

### Change Colors
Edit `ResultModal.css`:
```css
.status-icon.passed {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.3) 0%, rgba(34, 197, 94, 0.1) 100%);
  color: #22c55e;
  border: 2px solid rgba(34, 197, 94, 0.5);
}
```

### Change Animation Speed
Edit `ResultModal.jsx`:
```jsx
// Typewriter speed (ms per character)
}, 30); // Change this value

// XP animation speed (ms per frame)
}, 16); // Change this value
```

### Change Confetti
Edit `ResultModal.jsx`:
```jsx
<Confetti
  width={window.innerWidth}
  height={window.innerHeight}
  recycle={false}
  numberOfPieces={100}  // Change this value
/>
```

## Troubleshooting

### Quote Not Appearing
1. Check API endpoint: `/api/ai-evaluation/quotes/{submission_id}/`
2. Verify token is valid
3. Check browser console for errors
4. Ensure LM Studio is running

### Animations Not Working
1. Check Framer Motion is installed: `npm list framer-motion`
2. Check CSS is loaded
3. Check browser supports CSS animations
4. Check `prefers-reduced-motion` setting

### Modal Not Closing
1. Verify `onClose` callback is provided
2. Check `isOpen` prop is being updated
3. Check for JavaScript errors in console

### Confetti Not Showing
1. Check `react-confetti` is installed: `npm list react-confetti`
2. Verify `showConfetti` state is true
3. Check browser supports canvas

## Performance Tips

1. **Memoize Component**:
   ```jsx
   export default React.memo(ResultModal);
   ```

2. **Lazy Load**:
   ```jsx
   const ResultModal = lazy(() => import('./ResultModal'));
   ```

3. **Optimize Animations**:
   - Use `will-change` CSS property
   - Reduce confetti pieces on mobile
   - Use `transform` instead of `left/top`

## Accessibility

### Keyboard Navigation
- Tab through buttons
- Enter to activate
- Escape to close (optional)

### Screen Readers
- Semantic HTML
- ARIA labels on buttons
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

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
- Mobile browsers (iOS Safari 14+, Chrome Android)

## References

- [Framer Motion Docs](https://www.framer.com/motion/)
- [React Confetti](https://www.npmjs.com/package/react-confetti)
- [CSS Backdrop Filter](https://developer.mozilla.org/en-US/docs/Web/CSS/backdrop-filter)
- [Glassmorphism](https://glassmorphism.com/)

---

**Version**: 1.0.0
**Last Updated**: 2026-04-28
