/**
 * SkillTree AI - Match Page
 * Active multiplayer match view with real-time updates
 * @module pages/MatchPage
 */

import { useEffect, useState, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import useMatchStore from '../store/matchStore';
import useWebSocket from '../hooks/useWebSocket';
import { MATCH_STATUS } from '../constants';
import { formatMatchDuration } from '../utils/constants';

/**
 * Match page component
 * @returns {JSX.Element} Match page
 */
function MatchPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { currentMatch, fetchMatch, submitSolution, leaveMatch, isLoading, error } = useMatchStore();
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [timeLeft, setTimeLeft] = useState(0);
  const [matchState, setMatchState] = useState(null);

  // WebSocket for real-time updates
  const { isConnected, lastMessage, send } = useWebSocket(`/ws/matches/${id}/`, {
    autoConnect: true,
    onMessage: (data) => {
      if (data.type === 'match_update') {
        setMatchState(data.payload);
      } else if (data.type === 'match_ended') {
        handleMatchEnd(data.payload);
      }
    },
  });

  // Fetch match on mount
  useEffect(() => {
    if (id) {
      fetchMatch(id);
    }
    return () => {
      // Cleanup
    };
  }, [id, fetchMatch]);

  // Timer countdown
  useEffect(() => {
    if (currentMatch?.status === MATCH_STATUS.IN_PROGRESS && currentMatch?.timeLimit) {
      const interval = setInterval(() => {
        setTimeLeft((prev) => {
          if (prev <= 1) {
            clearInterval(interval);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [currentMatch?.status, currentMatch?.timeLimit]);

  /**
   * Handle match end
   * @param {Object} result - Match result
   */
  const handleMatchEnd = useCallback((result) => {
    setMatchState((prev) => ({ ...prev, status: MATCH_STATUS.COMPLETED, result }));
  }, []);

  /**
   * Handle solution submission
   */
  const handleSubmit = async () => {
    try {
      await submitSolution(id, { code, language });
    } catch (e) {
      // Error handled by store
    }
  };

  /**
   * Handle leave match
   */
  const handleLeave = async () => {
    try {
      await leaveMatch();
      navigate('/arena');
    } catch (e) {
      // Error handled by store
    }
  };

  /**
   * Send ready status
   */
  const handleReady = () => {
    send({ type: 'ready' });
  };

  if (!currentMatch) {
    return <div className="match-page loading">Loading match...</div>;
  }

  const isWaiting = currentMatch.status === MATCH_STATUS.WAITING;
  const isActive = currentMatch.status === MATCH_STATUS.IN_PROGRESS;
  const isCompleted = currentMatch.status === MATCH_STATUS.COMPLETED;

  return (
    <div className="match-page">
      {/* Match Header */}
      <div className="match-header glass-panel">
        <div className="match-info">
          <h1>Match #{id?.slice(0, 8)}</h1>
          <span className="match-mode">{currentMatch.mode}</span>
        </div>
        
        <div className="match-timer">
          {isActive && (
            <>
              <span className="timer-label">Time Left</span>
              <span className={`timer-value ${timeLeft < 60 ? 'urgent' : ''}`}>
                {formatMatchDuration(timeLeft)}
              </span>
            </>
          )}
          {isWaiting && <span className="waiting-text">Waiting for players...</span>}
          {isCompleted && <span className="completed-text">Match Ended</span>}
        </div>

        <div className="match-connection">
          <span className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '🟢 Live' : '🔴 Reconnecting...'}
          </span>
        </div>
      </div>

      {/* Waiting Room */}
      {isWaiting && (
        <div className="waiting-room glass-panel">
          <h2>Waiting for players</h2>
          <div className="players-list">
            {currentMatch.players?.map((player) => (
              <div key={player.id} className="player-item">
                <span className="player-avatar">{player.avatar || '👤'}</span>
                <span className="player-name">{player.username}</span>
                <span className={`player-status ${player.ready ? 'ready' : 'not-ready'}`}>
                  {player.ready ? '✓ Ready' : '...'}
                </span>
              </div>
            ))}
          </div>
          <button onClick={handleReady} className="primary-cta">
            I'm Ready!
          </button>
          <button onClick={handleLeave} className="secondary-cta">
            Leave Match
          </button>
        </div>
      )}

      {/* Active Match */}
      {isActive && (
        <div className="match-arena">
          {/* Problem Panel */}
          <div className="problem-panel glass-panel">
            <h3>Challenge</h3>
            <div className="problem-content">
              <h4>{currentMatch.currentProblem?.title || 'Coding Challenge'}</h4>
              <p>{currentMatch.currentProblem?.description || 'Complete the challenge to score points.'}</p>
              {currentMatch.currentProblem?.examples && (
                <div className="problem-examples">
                  <h5>Examples:</h5>
                  {currentMatch.currentProblem.examples.map((ex, i) => (
                    <pre key={i} className="example-block">
                      <strong>Input:</strong> {ex.input}
                      <strong>Output:</strong> {ex.output}
                    </pre>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Leaderboard Panel */}
          <div className="leaderboard-panel glass-panel">
            <h3>Live Rankings</h3>
            <div className="live-rankings">
              {(matchState?.players || currentMatch.players || []).map((player, index) => (
                <div key={player.id} className={`ranking-item ${player.isCurrentUser ? 'current' : ''}`}>
                  <span className="rank-position">#{index + 1}</span>
                  <span className="rank-name">{player.username}</span>
                  <span className="rank-score">{player.score || 0} pts</span>
                </div>
              ))}
            </div>
          </div>

          {/* Code Editor */}
          <div className="code-editor-panel glass-panel">
            <div className="editor-toolbar">
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="language-select"
              >
                <option value="python">Python</option>
                <option value="javascript">JavaScript</option>
                <option value="java">Java</option>
                <option value="cpp">C++</option>
              </select>
              <button
                onClick={handleSubmit}
                disabled={isLoading || !code.trim()}
                className="submit-button primary-cta"
              >
                {isLoading ? 'Submitting...' : 'Submit Solution'}
              </button>
            </div>
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="code-textarea"
              placeholder="Write your solution here..."
              spellCheck={false}
            />
          </div>
        </div>
      )}

      {/* Match Results */}
      {isCompleted && (
        <div className="match-results glass-panel">
          <div className="results-header">
            <h2>Match Results</h2>
            <span className={`result-badge ${matchState?.result || currentMatch.result}`}>
              {matchState?.result === 'win' || currentMatch.result === 'win' ? '🎉 Victory!' : '💪 Good Try!'}
            </span>
          </div>
          
          <div className="results-stats">
            <div className="result-stat">
              <span className="stat-label">Final Score</span>
              <span className="stat-value">{matchState?.score || currentMatch.score || 0}</span>
            </div>
            <div className="result-stat">
              <span className="stat-label">XP Earned</span>
              <span className="stat-value">+{matchState?.xpEarned || currentMatch.xpEarned || 0}</span>
            </div>
            <div className="result-stat">
              <span className="stat-label">Rank Change</span>
              <span className="stat-value">{matchState?.rankChange || currentMatch.rankChange || 0}</span>
            </div>
          </div>

          <div className="results-actions">
            <Link to="/arena" className="primary-cta">Play Again</Link>
            <Link to="/leaderboard" className="secondary-cta">View Leaderboard</Link>
          </div>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}
    </div>
  );
}

export default MatchPage;