/**
 * SkillTree AI - Arena Page
 * Multiplayer match creation and joining
 * @module pages/ArenaPage
 */

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import useMatchStore from '../store/matchStore';
import { MATCH_MODES, MATCH_STATUS } from '../constants';

/**
 * Arena page component
 * @returns {JSX.Element} Arena page
 */
function ArenaPage() {
  const {
    availableMatches,
    matchHistory,
    matchStats,
    currentMatch,
    isLoading,
    error,
    fetchAvailableMatches,
    fetchMatchHistory,
    fetchMatchStats,
    createMatch,
    joinMatch,
    fetchActiveMatch,
  } = useMatchStore();

  const [selectedMode, setSelectedMode] = useState(MATCH_MODES.CASUAL);
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    fetchAvailableMatches();
    fetchMatchHistory();
    fetchMatchStats();
    fetchActiveMatch();
  }, [fetchAvailableMatches, fetchMatchHistory, fetchMatchStats, fetchActiveMatch]);

  /**
   * Handle create match
   */
  const handleCreateMatch = async () => {
    try {
      const match = await createMatch({ mode: selectedMode });
      if (match?.id) {
        // Navigate to match page
        window.location.href = `/match/${match.id}`;
      }
    } catch (e) {
      // Error handled by store
    }
  };

  /**
   * Handle join match
   * @param {string} matchId - Match ID
   */
  const handleJoinMatch = async (matchId) => {
    try {
      await joinMatch(matchId);
      window.location.href = `/match/${matchId}`;
    } catch (e) {
      // Error handled by store
    }
  };

  /**
   * Get mode icon
   * @param {string} mode - Match mode
   * @returns {string} Emoji icon
   */
  const getModeIcon = (mode) => {
    const icons = {
      [MATCH_MODES.RANKED]: '🏆',
      [MATCH_MODES.CASUAL]: '🎮',
      [MATCH_MODES.TOURNAMENT]: '⚔️',
      [MATCH_MODES.PRACTICE]: '📝',
    };
    return icons[mode] || '🎮';
  };

  /**
   * Get status class
   * @param {string} status - Match status
   * @returns {string} CSS class
   */
  const getStatusClass = (status) => {
    const classes = {
      [MATCH_STATUS.WAITING]: 'status-waiting',
      [MATCH_STATUS.IN_PROGRESS]: 'status-active',
      [MATCH_STATUS.COMPLETED]: 'status-completed',
    };
    return classes[status] || '';
  };

  return (
    <div className="arena-page">
      <div className="arena-header">
        <h1>Arena</h1>
        <p className="header-subtitle">Challenge other players in real-time coding battles</p>
      </div>

      {/* Active Match Alert */}
      {currentMatch && (
        <div className="active-match-alert glass-panel">
          <div className="alert-content">
            <span className="alert-icon">⚔️</span>
            <div className="alert-text">
              <h3>You have an active match!</h3>
              <p>Mode: {currentMatch.mode} | Status: {currentMatch.status}</p>
            </div>
          </div>
          <Link to={`/match/${currentMatch.id}`} className="primary-cta">
            Continue Match
          </Link>
        </div>
      )}

      {/* Stats Overview */}
      {matchStats && (
        <div className="arena-stats glass-panel">
          <div className="stat-item">
            <span className="stat-value">{matchStats.totalMatches || 0}</span>
            <span className="stat-label">Total Matches</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{matchStats.wins || 0}</span>
            <span className="stat-label">Wins</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{matchStats.losses || 0}</span>
            <span className="stat-label">Losses</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{matchStats.winRate || 0}%</span>
            <span className="stat-label">Win Rate</span>
          </div>
        </div>
      )}

      {/* Game Modes */}
      <div className="game-modes">
        <h2>Game Modes</h2>
        <div className="modes-grid">
          {Object.values(MATCH_MODES).map((mode) => (
            <button
              key={mode}
              className={`glass-panel mode-card ${selectedMode === mode ? 'selected' : ''}`}
              onClick={() => setSelectedMode(mode)}
            >
              <div className="mode-icon">{getModeIcon(mode)}</div>
              <h3>{mode.charAt(0).toUpperCase() + mode.slice(1)}</h3>
              <p>
                {mode === MATCH_MODES.RANKED && 'Compete for points and climb the leaderboard'}
                {mode === MATCH_MODES.CASUAL && 'Practice without affecting your rank'}
                {mode === MATCH_MODES.TOURNAMENT && 'Join tournaments for big rewards'}
                {mode === MATCH_MODES.PRACTICE && 'Learn at your own pace'}
              </p>
            </button>
          ))}
        </div>
        
        <button
          onClick={handleCreateMatch}
          disabled={isLoading}
          className="create-match-button primary-cta"
        >
          {isLoading ? 'Creating...' : 'Create Match'}
        </button>
      </div>

      {/* Available Matches */}
      <div className="available-matches">
        <h2>Available Matches</h2>
        {availableMatches.length === 0 ? (
          <div className="empty-message glass-panel">No matches available. Create one!</div>
        ) : (
          <div className="matches-list">
            {availableMatches.map((match) => (
              <div key={match.id} className="glass-panel match-card">
                <div className="match-info">
                  <span className="match-mode">{getModeIcon(match.mode)} {match.mode}</span>
                  <span className={`match-status ${getStatusClass(match.status)}`}>
                    {match.status}
                  </span>
                </div>
                <div className="match-players">
                  <span>{match.currentPlayers || 1}/{match.maxPlayers || 2} players</span>
                </div>
                <button
                  onClick={() => handleJoinMatch(match.id)}
                  className="join-button secondary-cta"
                  disabled={match.currentPlayers >= match.maxPlayers}
                >
                  {match.currentPlayers >= match.maxPlayers ? 'Full' : 'Join'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Match History */}
      {matchHistory.length > 0 && (
        <div className="match-history">
          <h2>Recent Matches</h2>
          <div className="history-list">
            {matchHistory.slice(0, 5).map((match) => (
              <Link
                key={match.id}
                to={`/match/${match.id}`}
                className="glass-panel history-item"
              >
                <div className="history-match-info">
                  <span className="history-mode">{getModeIcon(match.mode)} {match.mode}</span>
                  <span className={`history-result ${match.result}`}>
                    {match.result === 'win' ? '✓ Won' : '✗ Lost'}
                  </span>
                </div>
                <div className="history-meta">
                  <span>{match.xpEarned > 0 ? `+${match.xpEarned}` : match.xpEarned} XP</span>
                  <span>{new Date(match.completedAt).toLocaleDateString()}</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}
    </div>
  );
}

export default ArenaPage;