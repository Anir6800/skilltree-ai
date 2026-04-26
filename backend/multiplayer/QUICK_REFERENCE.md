# Multiplayer System - Quick Reference

## 🚀 One-Command Setup

```bash
# Create test environment
python manage.py test_match --users 2

# Start all services (separate terminals)
redis-server
daphne -b 0.0.0.0 -p 8000 core.asgi:application
celery -A core worker -l info
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/matches/` | Create match |
| POST | `/api/matches/join/` | Join by invite code |
| GET | `/api/matches/` | List matches |
| GET | `/api/matches/{id}/` | Match details |
| POST | `/api/matches/{id}/leave/` | Leave match |
| GET | `/api/matches/{id}/status/` | Match status |

## 🔌 WebSocket Events

### Client → Server

```json
{"type": "ready"}
{"type": "code_update"}
{"type": "submission_result", "tests_passed": 5, "tests_total": 5, "is_winner": true}
{"type": "surrender"}
```

### Server → Client

```json
{"type": "connected", "match_state": {...}}
{"type": "player_ready", "user_id": 1, "username": "player1"}
{"type": "match_started", "started_at": "2026-04-26T10:00:00Z"}
{"type": "opponent_typing", "user_id": 2}
{"type": "submission_result", "user_id": 1, "tests_passed": 5, "is_winner": true}
{"type": "player_disconnected", "user_id": 2}
{"type": "player_surrendered", "user_id": 2}
```

## 🔐 Authentication

WebSocket: `ws://localhost:8000/ws/match/{id}/?token={jwt}`
HTTP: `Authorization: Bearer {jwt}`

## 🧪 Testing

```bash
# Run tests
python manage.py test multiplayer

# Create test data
python manage.py test_match

# Get JWT token
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testplayer1", "password": "test123"}'
```

## 📦 Celery Integration

```python
from multiplayer.tasks import broadcast_submission_result

broadcast_submission_result.delay(
    match_id=1,
    user_id=user.id,
    username=user.username,
    tests_passed=5,
    tests_total=5,
    is_winner=True
)
```

## 🎨 Frontend Hook

```javascript
import useMatchWebSocket from '../hooks/useMatchWebSocket';

const { matchState, events, sendReady, sendSubmissionResult } = 
  useMatchWebSocket(matchId, token);

// Send ready
sendReady();

// Submit result
sendSubmissionResult(5, 5, true);
```

## 🐛 Debug Commands

```bash
# Check Redis
redis-cli ping

# Test WebSocket
wscat -c "ws://localhost:8000/ws/match/1/?token=TOKEN"

# Monitor Celery
celery -A core inspect active

# Check logs
tail -f logs/daphne.log
tail -f logs/celery.log
```

## ⚡ Performance Tips

- Use Redis in production
- Enable connection pooling
- Throttle typing indicators (1s)
- Use `select_related` in queries
- Monitor channel layer health

## 🔒 Security

- ✅ JWT required
- ✅ Participant verification
- ✅ No code broadcast
- ✅ Hidden test answers
- ⚠️ Add rate limiting
- ⚠️ Use WSS in production

## 📚 Documentation

- `README.md` - Full API docs
- `INTEGRATION.md` - Frontend guide
- `DEPLOYMENT.md` - Production setup
- `tests.py` - Usage examples
