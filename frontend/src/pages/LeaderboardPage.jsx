/**
 * SkillTree AI - Leaderboard Page
 * Global and skill-specific leaderboards
 * @module pages/LeaderboardPage
 */

import { useEffect, useState } from 'react';
import * as leaderboardApi from '../api/leaderboardApi';
import useAuthStore from '../store/authStore';
import { LEADERBOARD_PERIODS } from '../constants';
import { formatXP, formatPosition } from '../utils/constants';

/**
 * Leaderboard page component
 * @returns {JSX.Element} Leaderboard page
 */
function LeaderboardPage() {
  const { user } = useAuthStore();
  const [leaderboard, setLeaderboard] = useState([]);
  const [userRank, setUserRank] = useState(null);
  const [topPlayers, setTopPlayers] = useState([]);
  const [globalStats, setGlobalStats] = useState(null);
  const [period, setPeriod] = useState(LEADERBOARD_PERIODS.WEEKLY);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchLeaderboard();
  }, [period]);

  /**
   * Fetch leaderboard data
   */
  const fetchLeaderboard = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const [leaderboardData, userRankData, topData, statsData] = await Promise.all([
        leaderboardApi.getLeaderboard({ period }),
        leaderboardApi.getUserRank({ period }).catch(() => null),
        leaderboardApi.getTopPlayers(period, 3),
        leaderboardApi.getGlobalStats().catch(() => null),
      ]);
      
      setLeaderboard(leaderboardData.results || leaderboardData);
      setUserRank(userRankData);
      setTopPlayers(topData);
      setGlobalStats(statsData);
    } catch (e) {
      setError('Failed to load leaderboard');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Get rank badge class
   * @param {number} position - Position number
   * @returns {string} CSS class
   */
  const getRankBadgeClass = (position) => {
    if (position === 1) return 'rank-gold';
    if (position === 2) return 'rank-silver';
    if (position === 3) return 'rank-bronze';
    return '';
  };

  /**
   * Get period label
   * @param {string} p - Period key
   * @returns {string} Display label
   */
  const getPeriodLabel = (p) => {
    const labels = {
      [LEADERBOARD_PERIODS.DAILY]: 'Today',
      [LEADERBOARD_PERIODS.WEEKLY]: 'This Week',
      [LEADERBOARD_PERIODS.MONTHLY]: 'This Month',
      [LEADERBOARD_PERIODS.ALL_TIME]: 'All Time',
    };
    return labels[p] || p;
  };

  return (
    <div className="leaderboard-page">
      <div className="leaderboard-header">
        <h1>Leaderboard</h1>
        <p className="header-subtitle">See how you rank against other adventurers</p>
      </div>

      {/* User Rank Card */}
      {userRank && (
        <div className="user-rank-card glass-panel">
          <div className="user-rank-info">
            <span className="user-rank-label">Your Rank</span>
            <span className="user-rank-position">{formatPosition(userRank.rank)}</span>
          </div>
          <div className="user-rank-stats">
            <div className="stat">
              <span className="stat-value">{formatXP(userRank.xp)}</span>
              <span className="stat-label">Total XP</span>
            </div>
            <div className="stat">
              <span className="stat-value">{userRank.level}</span>
              <span className="stat-label">Level</span>
            </div>
            <div className="stat">
              <span className="stat-value">{userRank.change > 0 ? `+${userRank.change}` : userRank.change}</span>
              <span className="stat-label">Change</span>
            </div>
          </div>
        </div>
      )}

      {/* Top 3 Players */}
      {topPlayers.length > 0 && (
        <div className="top-players">
          <div className="podium">
            {/* Second Place */}
            {topPlayers[1] && (
              <div className="podium-item silver">
                <div className="player-avatar">{topPlayers[1].avatar || '🥈'}</div>
                <div className="player-name">{topPlayers[1].username}</div>
                <div className="player-xp">{formatXP(topPlayers[1].xp)} XP</div>
                <div className="podium-position">2</div>
              </div>
            )}
            
            {/* First Place */}
            {topPlayers[0] && (
              <div className="podium-item gold">
                <div className="player-avatar">{topPlayers[0].avatar || '🥇'}</div>
                <div className="player-name">{topPlayers[0].username}</div>
                <div className="player-xp">{formatXP(topPlayers[0].xp)} XP</div>
                <div className="podium-position">1</div>
              </div>
            )}
            
            {/* Third Place */}
            {topPlayers[2] && (
              <div className="podium-item bronze">
                <div className="player-avatar">{topPlayers[2].avatar || '🥉'}</div>
                <div className="player-name">{topPlayers[2].username}</div>
                <div className="player-xp">{formatXP(topPlayers[2].xp)} XP</div>
                <div className="podium-position">3</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Period Filter */}
      <div className="period-filter">
        {Object.values(LEADERBOARD_PERIODS).map((p) => (
          <button
            key={p}
            className={`period-button ${period === p ? 'active' : ''}`}
            onClick={() => setPeriod(p)}
          >
            {getPeriodLabel(p)}
          </button>
        ))}
      </div>

      {/* Global Stats */}
      {globalStats && (
        <div className="global-stats glass-panel">
          <div className="global-stat">
            <span className="stat-value">{globalStats.totalPlayers || 0}</span>
            <span className="stat-label">Total Players</span>
          </div>
          <div className="global-stat">
            <span className="stat-value">{formatXP(globalStats.totalXP || 0)}</span>
            <span className="stat-label">Total XP Earned</span>
          </div>
          <div className="global-stat">
            <span className="stat-value">{globalStats.activePlayers || 0}</span>
            <span className="stat-label">Active This Week</span>
          </div>
        </div>
      )}

      {/* Leaderboard Table */}
      <div className="leaderboard-table glass-panel">
        <div className="table-header">
          <span className="col-rank">Rank</span>
          <span className="col-player">Player</span>
          <span className="col-level">Level</span>
          <span className="col-xp">XP</span>
          <span className="col-streak">Streak</span>
        </div>
        
        {isLoading ? (
          <div className="loading-message">Loading leaderboard...</div>
        ) : error ? (
          <div className="error-message">{error}</div>
        ) : leaderboard.length === 0 ? (
          <div className="empty-message">No players yet</div>
        ) : (
          <div className="table-body">
            {leaderboard.map((entry, index) => (
              <div
                key={entry.id || entry.userId}
                className={`table-row ${entry.id === user?.id || entry.userId === user?.id ? 'current-user' : ''} ${getRankBadgeClass(index + 1)}`}
              >
                <span className="col-rank">
                  <span className={`rank-badge ${getRankBadgeClass(index + 1)}`}>
                    {formatPosition(index + 1)}
                  </span>
                </span>
                <span className="col-player">
                  <span className="player-avatar">{entry.avatar || '👤'}</span>
                  <span className="player-name">{entry.username}</span>
                  {entry.badges?.length > 0 && (
                    <span className="player-badges">
                      {entry.badges.map((badge) => (
                        <span key={badge} className="badge">{badge}</span>
                      ))}
                    </span>
                  )}
                </span>
                <span className="col-level">{entry.level}</span>
                <span className="col-xp">{formatXP(entry.xp)}</span>
                <span className="col-streak">
                  {entry.streak > 0 ? `🔥 ${entry.streak}d` : '-'}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default LeaderboardPage;