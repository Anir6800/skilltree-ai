# Multiplayer Integration Guide

## Quick Start

### 1. Create a Match (HTTP)

```python
import requests

# User 1 creates a match
response = requests.post(
    'http://localhost:8000/api/matches/',
    headers={'Authorization': f'Bearer {user1_token}'},
    json={
        'quest_id': 1,
        'max_participants': 2
    }
)

match_data = response.json()
invite_code = match_data['invite_code']
match_id = match_data['id']
```

### 2. Join Match (HTTP)

```python
# User 2 joins the match
response = requests.post(
    'http://localhost:8000/api/matches/join/',
    headers={'Authorization': f'Bearer {user2_token}'},
    json={'invite_code': invite_code}
)
```

### 3. Connect via WebSocket

```python
import asyncio
import websockets
import json

async def connect_to_match(match_id, token):
    uri = f"ws://localhost:8000/ws/match/{match_id}/?token={token}"
    
    async with websockets.connect(uri) as websocket:
        # Receive connection confirmation
        message = await websocket.recv()
        data = json.loads(message)
        print(f"Connected: {data}")
        
        # Send ready signal
        await websocket.send(json.dumps({'type': 'ready'}))
        
        # Listen for events
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")
            
            if data['type'] == 'match_started':
                print("Match started! Begin coding...")
            elif data['type'] == 'submission_result':
                print(f"Player {data['username']}: {data['tests_passed']}/{data['tests_total']}")

# Run for both users
asyncio.run(connect_to_match(match_id, user1_token))
```

### 4. Submit Code and Broadcast Results

```python
# In your executor service, after running tests:
from multiplayer.tasks import broadcast_submission_result

# Check if user is in an active match for this quest
match = Match.objects.filter(
    quest=submission.quest,
    status='active',
    participants=submission.user
).first()

if match:
    # Calculate results
    tests_passed = sum(1 for test in results if test['passed'])
    tests_total = len(results)
    is_winner = tests_passed == tests_total
    
    # Broadcast to all participants
    broadcast_submission_result.delay(
        match_id=match.id,
        user_id=submission.user.id,
        username=submission.user.username,
        tests_passed=tests_passed,
        tests_total=tests_total,
        is_winner=is_winner
    )
    
    # If winner, update match
    if is_winner:
        match.winner = submission.user
        match.status = 'finished'
        match.ended_at = timezone.now()
        match.save()
```

## Frontend React Integration

### Match Lobby Component

```jsx
import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';

function MatchLobby({ questId }) {
  const { token } = useAuth();
  const [match, setMatch] = useState(null);
  const [inviteCode, setInviteCode] = useState('');

  const createMatch = async () => {
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
    
    const data = await response.json();
    setMatch(data);
    setInviteCode(data.invite_code);
  };

  const joinMatch = async (code) => {
    const response = await fetch('/api/matches/join/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ invite_code: code })
    });
    
    const data = await response.json();
    setMatch(data);
  };

  return (
    <div className="match-lobby">
      {!match ? (
        <>
          <button onClick={createMatch}>Create Match</button>
          <input
            placeholder="Enter invite code"
            value={inviteCode}
            onChange={(e) => setInviteCode(e.target.value)}
          />
          <button onClick={() => joinMatch(inviteCode)}>Join Match</button>
        </>
      ) : (
        <div>
          <h3>Match #{match.id}</h3>
          <p>Invite Code: {match.invite_code || `MATCH-${match.id}`}</p>
          <p>Status: {match.status}</p>
          <div>
            <h4>Participants:</h4>
            {match.participants.map(p => (
              <div key={p.user.id}>{p.user.username} (Lvl {p.user.level})</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

### WebSocket Hook

```jsx
import { useEffect, useRef, useState } from 'react';

function useMatchWebSocket(matchId, token) {
  const ws = useRef(null);
  const [matchState, setMatchState] = useState(null);
  const [events, setEvents] = useState([]);

  useEffect(() => {
    if (!matchId || !token) return;

    const wsUrl = `ws://localhost:8000/ws/match/${matchId}/?token=${token}`;
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'connected') {
        setMatchState(data.match_state);
      } else {
        setEvents(prev => [...prev, data]);
      }
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.current.onclose = () => {
      console.log('WebSocket disconnected');
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [matchId, token]);

  const sendReady = () => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'ready' }));
    }
  };

  const sendCodeUpdate = () => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'code_update' }));
    }
  };

  const sendSubmissionResult = (testsPassed, testsTotal, isWinner) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: 'submission_result',
        tests_passed: testsPassed,
        tests_total: testsTotal,
        is_winner: isWinner
      }));
    }
  };

  const surrender = () => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'surrender' }));
    }
  };

  return {
    matchState,
    events,
    sendReady,
    sendCodeUpdate,
    sendSubmissionResult,
    surrender
  };
}

export default useMatchWebSocket;
```

### Match Arena Component

```jsx
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import useMatchWebSocket from '../hooks/useMatchWebSocket';
import CodeEditor from '../components/CodeEditor';

function MatchArena() {
  const { matchId } = useParams();
  const { token, user } = useAuth();
  const [code, setCode] = useState('');
  const [isReady, setIsReady] = useState(false);
  
  const {
    matchState,
    events,
    sendReady,
    sendCodeUpdate,
    sendSubmissionResult,
    surrender
  } = useMatchWebSocket(matchId, token);

  useEffect(() => {
    if (matchState?.quest?.starter_code) {
      setCode(matchState.quest.starter_code);
    }
  }, [matchState]);

  const handleReady = () => {
    sendReady();
    setIsReady(true);
  };

  const handleCodeChange = (newCode) => {
    setCode(newCode);
    sendCodeUpdate(); // Throttled in production
  };

  const handleSubmit = async () => {
    // Submit to executor API
    const response = await fetch('/api/execute/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        quest_id: matchState.quest.id,
        code: code,
        language: 'python'
      })
    });
    
    const result = await response.json();
    
    // Broadcast result via WebSocket
    sendSubmissionResult(
      result.tests_passed,
      result.tests_total,
      result.tests_passed === result.tests_total
    );
  };

  return (
    <div className="match-arena">
      <div className="match-header">
        <h2>{matchState?.quest?.title}</h2>
        <div className="participants">
          {matchState?.participants.map(p => (
            <div key={p.id} className={p.id === user.id ? 'you' : 'opponent'}>
              {p.username}
            </div>
          ))}
        </div>
      </div>

      {matchState?.status === 'waiting' && !isReady && (
        <button onClick={handleReady}>Ready</button>
      )}

      {matchState?.status === 'active' && (
        <>
          <CodeEditor
            value={code}
            onChange={handleCodeChange}
            language="python"
          />
          <button onClick={handleSubmit}>Submit</button>
          <button onClick={surrender}>Surrender</button>
        </>
      )}

      <div className="events-feed">
        {events.map((event, idx) => (
          <div key={idx} className={`event event-${event.type}`}>
            {event.type === 'opponent_typing' && (
              <span>{event.username} is typing...</span>
            )}
            {event.type === 'submission_result' && (
              <span>
                {event.username}: {event.tests_passed}/{event.tests_total}
                {event.is_winner && ' 🏆'}
              </span>
            )}
            {event.type === 'match_started' && (
              <span>Match started! Good luck!</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default MatchArena;
```

## Testing the Integration

### 1. Start Services

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Django with Daphne
cd backend
python manage.py migrate
daphne -b 0.0.0.0 -p 8000 core.asgi:application

# Terminal 3: Celery
celery -A core worker -l info

# Terminal 4: Frontend
cd frontend
npm run dev
```

### 2. Test Flow

1. User 1 creates a match
2. User 2 joins using invite code
3. Both users click "Ready"
4. Match starts automatically
5. Users write code and submit
6. Results broadcast in real-time
7. First to pass all tests wins

### 3. Monitor WebSocket Traffic

Use browser DevTools → Network → WS to see WebSocket messages in real-time.

## Error Handling

### Connection Errors

```javascript
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
  // Show reconnection UI
};

ws.onclose = (event) => {
  if (event.code === 4001) {
    alert('Authentication failed. Please log in again.');
  } else if (event.code === 4004) {
    alert('You are not a participant in this match.');
  } else {
    // Attempt reconnection
    setTimeout(() => reconnect(), 3000);
  }
};
```

### API Errors

```javascript
const joinMatch = async (code) => {
  try {
    const response = await fetch('/api/matches/join/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ invite_code: code })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to join match');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Join match error:', error);
    alert(error.message);
  }
};
```

## Performance Tips

1. **Throttle typing indicators**: Use lodash throttle or debounce
2. **Batch events**: Collect multiple events and render once
3. **Optimize re-renders**: Use React.memo for participant lists
4. **Connection pooling**: Reuse WebSocket connections
5. **Lazy load**: Only connect to WebSocket when match is active

## Security Checklist

- ✅ JWT authentication on WebSocket connection
- ✅ Participant verification before allowing connection
- ✅ Code content not broadcast (only indicators)
- ✅ Test case answers hidden from clients
- ✅ Rate limiting on API endpoints (add in production)
- ✅ Input validation on all endpoints
- ✅ CORS configuration for allowed origins
- ✅ Secure WebSocket (wss://) in production
