# SkillTree AI - Multiplayer System

Real-time multiplayer competitive coding matches using Django Channels and WebSockets.

## Architecture

### Components

1. **WebSocket Consumer** (`consumers.py`)
   - Handles real-time bidirectional communication
   - JWT authentication via query string
   - Room-based channel groups for match isolation
   - Event-driven message routing

2. **HTTP API** (`views.py`)
   - RESTful endpoints for match management
   - Create, join, leave, and query matches
   - Invite code system for easy match joining

3. **Celery Tasks** (`tasks.py`)
   - Async broadcasting of submission results
   - Match timeout monitoring
   - Background processing for heavy operations

4. **Models** (`models.py`)
   - `Match`: Core match entity with quest, status, and winner
   - `MatchParticipant`: Through model for match participants with scores

## API Endpoints

### Create Match
```http
POST /api/matches/
Authorization: Bearer <token>
Content-Type: application/json

{
  "quest_id": 1,
  "max_participants": 2
}
```

**Response:**
```json
{
  "id": 1,
  "quest": {...},
  "status": "waiting",
  "participants": [...],
  "invite_code": "MATCH-1",
  "started_at": null,
  "ended_at": null
}
```

### Join Match
```http
POST /api/matches/join/
Authorization: Bearer <token>
Content-Type: application/json

{
  "invite_code": "MATCH-1"
}
```

### List Matches
```http
GET /api/matches/?status=waiting
Authorization: Bearer <token>
```

Query parameters:
- `status`: Filter by match status (waiting, active, finished)
- `quest_id`: Filter by quest ID

### Get Match Details
```http
GET /api/matches/{id}/
Authorization: Bearer <token>
```

### Leave Match
```http
POST /api/matches/{id}/leave/
Authorization: Bearer <token>
```

### Get Match Status
```http
GET /api/matches/{id}/status/
Authorization: Bearer <token>
```

## WebSocket Protocol

### Connection
```
ws://localhost:8000/ws/match/{match_id}/?token={jwt_token}
```

### Connection Response
```json
{
  "type": "connected",
  "match_state": {
    "id": 1,
    "status": "waiting",
    "participants": [...],
    "quest": {...},
    "started_at": null
  }
}
```

### Client → Server Events

#### Ready Signal
```json
{
  "type": "ready"
}
```

#### Code Update (Typing Indicator)
```json
{
  "type": "code_update"
}
```

#### Submission Result
```json
{
  "type": "submission_result",
  "tests_passed": 5,
  "tests_total": 5,
  "is_winner": true
}
```

#### Surrender
```json
{
  "type": "surrender"
}
```

### Server → Client Events

#### Player Ready
```json
{
  "type": "player_ready",
  "user_id": 1,
  "username": "player1",
  "ready_count": 1,
  "total_participants": 2
}
```

#### Match Started
```json
{
  "type": "match_started",
  "started_at": "2026-04-26T10:00:00Z"
}
```

#### Opponent Typing
```json
{
  "type": "opponent_typing",
  "user_id": 2,
  "username": "player2"
}
```

#### Submission Result
```json
{
  "type": "submission_result",
  "user_id": 1,
  "username": "player1",
  "tests_passed": 5,
  "tests_total": 5,
  "is_winner": true
}
```

#### Player Disconnected
```json
{
  "type": "player_disconnected",
  "user_id": 2,
  "username": "player2"
}
```

#### Player Surrendered
```json
{
  "type": "player_surrendered",
  "user_id": 2,
  "username": "player2"
}
```

#### Match Timeout
```json
{
  "type": "match_timeout",
  "winner": {
    "id": 1,
    "username": "player1"
  }
}
```

## Security

### Authentication
- JWT token required in WebSocket query string: `?token=<access_token>`
- Token validated on connection
- User must be a match participant

### Authorization
- Users can only connect to matches they're participating in
- Connection rejected with specific error codes:
  - `4001`: No token provided
  - `4002`: Invalid user ID
  - `4003`: Invalid token
  - `4004`: Not a participant

### Data Protection
- Code content not broadcast (only typing indicators)
- Test case expected outputs hidden from clients
- Participant verification on all operations

## Integration with Executor

The multiplayer system integrates with the code executor service:

1. User submits code via executor API
2. Executor runs tests and evaluates code
3. Executor calls Celery task `broadcast_submission_result`
4. Task broadcasts results to all match participants via WebSocket

Example integration in executor:
```python
from multiplayer.tasks import broadcast_submission_result

# After code execution
if submission.quest.matches.filter(status='active').exists():
    match = submission.quest.matches.filter(
        status='active',
        participants=submission.user
    ).first()
    
    if match:
        broadcast_submission_result.delay(
            match_id=match.id,
            user_id=submission.user.id,
            username=submission.user.username,
            tests_passed=tests_passed,
            tests_total=tests_total,
            is_winner=(tests_passed == tests_total)
        )
```

## Frontend Integration

### WebSocket Connection
```javascript
const token = localStorage.getItem('access_token');
const matchId = 123;
const ws = new WebSocket(`ws://localhost:8000/ws/match/${matchId}/?token=${token}`);

ws.onopen = () => {
  console.log('Connected to match');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
  
  switch(data.type) {
    case 'connected':
      // Initialize match UI with match_state
      break;
    case 'match_started':
      // Start timer, enable code editor
      break;
    case 'opponent_typing':
      // Show typing indicator
      break;
    case 'submission_result':
      // Update scoreboard
      if (data.is_winner) {
        // Show victory screen
      }
      break;
  }
};

// Send ready signal
ws.send(JSON.stringify({ type: 'ready' }));

// Send typing indicator (throttled)
editor.on('change', throttle(() => {
  ws.send(JSON.stringify({ type: 'code_update' }));
}, 1000));
```

### HTTP API Usage
```javascript
// Create match
const createMatch = async (questId) => {
  const response = await fetch('/api/matches/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      quest_id: questId,
      max_participants: 2
    })
  });
  return response.json();
};

// Join match
const joinMatch = async (inviteCode) => {
  const response = await fetch('/api/matches/join/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ invite_code: inviteCode })
  });
  return response.json();
};
```

## Testing

Run tests:
```bash
python manage.py test multiplayer
```

Test WebSocket connection:
```bash
# Install wscat
npm install -g wscat

# Connect to match
wscat -c "ws://localhost:8000/ws/match/1/?token=YOUR_JWT_TOKEN"

# Send ready signal
> {"type": "ready"}
```

## Configuration

### Redis (Required for Production)
```env
REDIS_URL=redis://localhost:6379/0
USE_REDIS_CHANNELS=True
```

### Development (In-Memory)
```env
USE_REDIS_CHANNELS=False
```

## Deployment

### Requirements
- Redis server for channel layer
- Daphne ASGI server for WebSocket support
- Celery worker for background tasks

### Start Services
```bash
# Start Redis
redis-server

# Start Django with Daphne
daphne -b 0.0.0.0 -p 8000 core.asgi:application

# Start Celery worker
celery -A core worker -l info
```

## Performance Considerations

1. **Channel Layer**: Use Redis in production for horizontal scaling
2. **Connection Pooling**: Configure Redis connection pool size
3. **Message Size**: Keep WebSocket messages small (<1KB)
4. **Broadcast Optimization**: Use `exclude_sender` to reduce traffic
5. **Database Queries**: Use `select_related` and `prefetch_related`

## Future Enhancements

- [ ] Spectator mode for watching matches
- [ ] Match replay system
- [ ] Tournament brackets
- [ ] Team-based matches
- [ ] Voice chat integration
- [ ] Match analytics and statistics
- [ ] ELO rating system
- [ ] Match history and achievements
