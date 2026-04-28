# Quote Generator - Integration Guide

## Overview

The Quote Generator creates context-aware motivational quotes for quest submissions using LM Studio. Quotes are cached in Redis and displayed in an animated ResultModal component with glassmorphism design.

## Architecture

### Backend Components

1. **quote_generator.py** (QuoteGenerator class)
   - Generates motivational quotes based on submission context
   - Implements tone rules (celebratory, persistent, speed, encouraging, committed, diplomatic, streak)
   - Caches quotes in Redis (1 hour TTL)
   - Provides fallback quotes when LM Studio is unavailable

2. **quote_views.py** (REST API endpoints)
   - GET `/api/ai-evaluation/quotes/{submission_id}/` - Get quote for submission
   - GET `/api/ai-evaluation/quotes/service/status/` - Check service availability

3. **quote_signals.py** (Signal handlers)
   - Pre-generates quotes on submission completion
   - Non-blocking async execution
   - Ensures quote is cached before frontend requests it

4. **test_quote_generator.py** (Comprehensive tests)
   - 30+ test cases covering all functionality
   - Context building, tone determination, caching, fallbacks

### Frontend Components

1. **ResultModal.jsx** (React component)
   - Full-screen overlay with glassmorphism design
   - Animated quote with typewriter effect (30ms per character)
   - Confetti animation for passed quests
   - XP counter animation
   - Streak milestone badge
   - Action buttons (Try Again, Next Quest, View Feedback)

2. **ResultModal.css** (Styling)
   - Dark gradients and floating panels
   - Motion-led hierarchy with Framer Motion
   - Responsive design for mobile
   - Accessibility support (prefers-reduced-motion)

## Context Data

The QuoteGenerator builds context from submission data:

```python
{
    'quest_title': str,           # e.g., "Find Target in Sorted Array"
    'skill_title': str,           # e.g., "Binary Search"
    'result': str,                # 'passed', 'failed', or 'flagged'
    'tests_passed': int,          # Number of tests passed
    'tests_total': int,           # Total number of tests
    'attempt_number': int,        # Attempt count for this quest
    'solve_time_seconds': float,  # Time to solve in seconds
    'ai_score': float,            # AI evaluation score (0.0-1.0)
    'user_streak': int,           # User's current streak days
    'ability_score': float,       # User's adaptive ability score
    'time_of_day': str,           # 'morning', 'afternoon', 'evening', 'night'
}
```

## Tone Rules

### Passed Submissions
- **Celebratory** (first attempt): "Two Pointers mastered first try — your pattern recognition is sharp."
- **Speed** (fast solve, <5s): "Solved Sliding Window in 4 minutes — that's interview speed."
- **Persistent** (3+ attempts): "Four attempts. One breakthrough. That's how Dynamic Programming gets learned."

### Failed Submissions
- **Encouraging** (1-2 attempts): "The logic is close — your Binary Search boundary condition needs one more look."
- **Committed** (4+ attempts): "5 attempts shows real commitment. Try the hint system — sometimes a nudge unlocks everything."

### Special Cases
- **Diplomatic** (AI flagged): "Strong solution — but the AI flagged it. Walk us through your approach to confirm it's yours."
- **Streak** (milestone, divisible by 7): "7-day streak on Binary Search — consistency is the real skill."

## LM Studio Prompt

The system prompt instructs LM Studio to:
- Generate ONE short motivational quote (max 2 sentences, max 30 words)
- Match emotional tone to outcome
- Reference actual quest/skill names
- Never be generic
- Provide specific, constructive feedback

Example system prompt:
```
You are an inspiring coding mentor. Generate ONE short motivational quote 
(max 2 sentences, max 30 words) based on the exact result provided. 
Match the emotional tone to the outcome. Never be generic. 
Reference the actual quest or skill by name when possible.

Tone: Celebrate the win enthusiastically. Praise their achievement and pattern recognition.
Example: 'Two Pointers mastered first try — your pattern recognition is sharp.'
```

## Caching Strategy

- **Cache Key**: `quote:{submission_id}`
- **TTL**: 1 hour (3600 seconds)
- **Backend**: Redis
- **Behavior**: Never regenerate quote for same submission

Benefits:
- Instant quote retrieval on frontend
- Reduced LM Studio load
- Consistent quotes across page reloads

## API Endpoints

### Get Quote for Submission
```bash
GET /api/ai-evaluation/quotes/{submission_id}/
Authorization: Bearer {token}
```

Response:
```json
{
  "quote": "Two Pointers mastered first try — your pattern recognition is sharp.",
  "submission_id": 123,
  "status": "passed"
}
```

### Check Service Status
```bash
GET /api/ai-evaluation/quotes/service/status/
Authorization: Bearer {token}
```

Response:
```json
{
  "available": true,
  "service": "lm_studio"
}
```

## Frontend Integration

### Basic Usage

```jsx
import ResultModal from './components/ResultModal';

function QuestPage() {
  const [showResult, setShowResult] = useState(false);
  const [submission, setSubmission] = useState(null);
  const [quote, setQuote] = useState('');
  const [xpAwarded, setXpAwarded] = useState(0);

  const handleSubmissionComplete = async (submissionData) => {
    setSubmission(submissionData);
    setXpAwarded(submissionData.xp_awarded || 0);

    // Fetch quote
    const response = await fetch(
      `/api/ai-evaluation/quotes/${submissionData.id}/`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    const data = await response.json();
    setQuote(data.quote);

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

### With Submission Pipeline

```jsx
async function submitQuest(code) {
  // 1. Submit code
  const submitResponse = await fetch('/api/quests/submit/', {
    method: 'POST',
    body: JSON.stringify({ quest_id, code, language }),
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const submission = await submitResponse.json();

  // 2. Wait for pipeline (execution, evaluation, detection)
  let result = submission;
  while (result.status === 'pending' || result.status === 'running') {
    await new Promise(r => setTimeout(r, 1000));
    const statusResponse = await fetch(`/api/quests/submissions/${submission.id}/`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    result = await statusResponse.json();
  }

  // 3. Fetch quote (already cached by signal handler)
  const quoteResponse = await fetch(
    `/api/ai-evaluation/quotes/${submission.id}/`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  );
  const quoteData = await quoteResponse.json();

  // 4. Show result modal with quote
  showResultModal(result, quoteData.quote);
}
```

## Fallback Quotes

When LM Studio is unavailable, fallback quotes are used:

```python
{
    'passed_first': "✓ {quest_title} mastered on first try. Sharp work.",
    'passed_multiple': "✓ {quest_title} conquered. Persistence pays off.",
    'failed_early': "Close on {quest_title}. You've got this — try again.",
    'failed_late': "Strong effort on {quest_title}. Consider the hint system.",
    'flagged': "Strong solution on {quest_title}. Let's verify your approach.",
}
```

## Performance Considerations

### Optimization Strategies

1. **Pre-generation on Signal**
   - Quote generated immediately on submission completion
   - Cached before frontend requests it
   - Eliminates latency on result display

2. **Redis Caching**
   - 1-hour TTL prevents stale quotes
   - Instant retrieval for repeated views
   - Reduces LM Studio load

3. **Fallback Quotes**
   - Instant response if LM Studio unavailable
   - No user-facing errors
   - Graceful degradation

4. **Async Execution**
   - Quote generation doesn't block submission processing
   - Non-blocking signal handler
   - Errors logged but not raised

### Monitoring

```bash
# Check Redis cache
redis-cli KEYS "quote:*"
redis-cli TTL "quote:123"

# Check LM Studio availability
curl http://localhost:1234/v1/models

# Monitor logs
tail -f logs/django.log | grep quote_generator
```

## Configuration

### Environment Variables

```bash
# LM Studio
LM_STUDIO_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=openai/gpt-oss-20b

# Redis
REDIS_URL=redis://localhost:6379/0

# Cache TTL (seconds)
QUOTE_CACHE_TTL=3600
```

### Django Settings

Already configured in `core/settings.py`:
- Redis channel layer
- Celery broker/result backend
- Cache framework

## Testing

### Run Tests

```bash
python manage.py test ai_evaluation.test_quote_generator -v 2
```

### Test Coverage

- Context building (passed, failed, flagged)
- Tone determination (all 7 tones)
- Attempt number calculation
- Time of day categorization
- Cache key generation
- Fallback quotes
- LM Studio integration
- Error handling
- Singleton instance

### Example Test

```python
def test_determine_tone_celebratory(self):
    """Test tone determination for first-attempt pass."""
    submission = QuestSubmission.objects.create(
        user=self.user,
        quest=self.quest,
        code='correct',
        language='python',
        status='passed',
        execution_result={'time_ms': 2000}
    )

    context = self.generator._build_context(submission)
    tone = self.generator._determine_tone(submission, context)

    self.assertEqual(tone, 'celebratory')
```

## Troubleshooting

### Quote Not Appearing

1. Check LM Studio is running: `curl http://localhost:1234/v1/models`
2. Check Redis is running: `redis-cli ping`
3. Check logs: `tail -f logs/django.log | grep quote`
4. Verify signal handler registered: Check `ai_evaluation/apps.py` has `ready()` method

### Slow Quote Generation

1. Check LM Studio response time: `time curl http://localhost:1234/v1/chat/completions`
2. Check Redis latency: `redis-cli --latency`
3. Consider increasing LM Studio timeout in `quote_generator.py`

### Fallback Quotes Always Used

1. Check LM Studio logs for errors
2. Verify LM Studio model is loaded: `curl http://localhost:1234/v1/models`
3. Check network connectivity: `ping localhost:1234`

## Future Enhancements

1. **Personalization**: Adjust tone based on user learning style
2. **Streak Tracking**: More granular streak milestones (3, 5, 10, 21 days)
3. **Difficulty Scaling**: Adjust quote complexity based on skill difficulty
4. **Language Support**: Generate quotes in user's preferred language
5. **A/B Testing**: Test different quote styles and measure engagement
6. **Analytics**: Track which quotes are most motivating
7. **Caching Strategy**: Use Redis Streams for quote history
8. **Batch Generation**: Pre-generate quotes for common scenarios

## References

- LM Studio: https://lmstudio.ai/
- Redis: https://redis.io/
- Framer Motion: https://www.framer.com/motion/
- Django Signals: https://docs.djangoproject.com/en/stable/topics/signals/
- React Hooks: https://react.dev/reference/react/hooks
