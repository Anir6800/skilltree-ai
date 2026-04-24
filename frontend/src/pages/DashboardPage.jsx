/**
 * SkillTree AI - Dashboard Page
 * Main dashboard showing user progress and quick actions
 * @module pages/DashboardPage
 */

import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import useSkillStore from '../store/skillStore';
import useQuestStore from '../store/questStore';
import { formatXP, formatPercentage, getLevelFromXP, getRankFromLevel } from '../utils/constants';

/**
 * Dashboard page component
 * @returns {JSX.Element} Dashboard page
 */
function DashboardPage() {
  const { user, isAuthenticated, fetchUser } = useAuthStore();
  const { skills, fetchSkills, progressStats } = useSkillStore();
  const { activeQuests, fetchActiveQuests } = useQuestStore();

  useEffect(() => {
    if (isAuthenticated) {
      fetchUser();
      fetchSkills();
      fetchActiveQuests();
    }
  }, [isAuthenticated, fetchUser, fetchSkills, fetchActiveQuests]);

  const level = user?.level || getLevelFromXP(user?.xp || 0);
  const rank = user?.rank || getRankFromLevel(level);
  const xpProgress = user?.xp ? formatPercentage(user.xp, 100) : '0%';

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1>Welcome back, {user?.username || 'Adventurer'}!</h1>
        <p className="dashboard-subtitle">Continue your learning journey</p>
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="glass-panel stat-card">
          <div className="stat-icon">⚡</div>
          <div className="stat-value">{level}</div>
          <div className="stat-label">Level</div>
        </div>
        
        <div className="glass-panel stat-card">
          <div className="stat-icon">⭐</div>
          <div className="stat-value">{formatXP(user?.xp || 0)}</div>
          <div className="stat-label">Total XP</div>
        </div>
        
        <div className="glass-panel stat-card">
          <div className="stat-icon">🏆</div>
          <div className="stat-value">{rank}</div>
          <div className="stat-label">Rank</div>
        </div>
        
        <div className="glass-panel stat-card">
          <div className="stat-icon">🎯</div>
          <div className="stat-value">{progressStats?.completed || 0}</div>
          <div className="stat-label">Skills Completed</div>
        </div>
      </div>

      {/* XP Progress Bar */}
      <div className="glass-panel progress-panel">
        <div className="progress-header">
          <span>Level {level} Progress</span>
          <span>{xpProgress} to Level {level + 1}</span>
        </div>
        <div className="progress-bar">
          <div 
            className="progress-fill premium-gradient" 
            style={{ width: xpProgress }}
          />
        </div>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <h2>Quick Actions</h2>
        <div className="actions-grid">
          <Link to="/skills" className="glass-panel action-card">
            <div className="action-icon">🌳</div>
            <div className="action-content">
              <h3>Skill Tree</h3>
              <p>Explore and unlock new skills</p>
            </div>
          </Link>
          
          <Link to="/quests" className="glass-panel action-card">
            <div className="action-icon">📜</div>
            <div className="action-content">
              <h3>Quests</h3>
              <p>{activeQuests?.length || 0} active quests</p>
            </div>
          </Link>
          
          <Link to="/arena" className="glass-panel action-card">
            <div className="action-icon">⚔️</div>
            <div className="action-content">
              <h3>Arena</h3>
              <p>Challenge other players</p>
            </div>
          </Link>
          
          <Link to="/leaderboard" className="glass-panel action-card">
            <div className="action-icon">📊</div>
            <div className="action-content">
              <h3>Leaderboard</h3>
              <p>See top players</p>
            </div>
          </Link>
        </div>
      </div>

      {/* Active Quests Preview */}
      {activeQuests?.length > 0 && (
        <div className="active-quests-preview">
          <div className="section-header">
            <h2>Active Quests</h2>
            <Link to="/quests" className="view-all-link">View All</Link>
          </div>
          <div className="quests-list">
            {activeQuests.slice(0, 3).map((quest) => (
              <Link 
                key={quest.id} 
                to={`/quests/${quest.id}`}
                className="glass-panel quest-preview-card"
              >
                <div className="quest-info">
                  <h4>{quest.title}</h4>
                  <span className={`difficulty-badge ${quest.difficulty}`}>
                    {quest.difficulty}
                  </span>
                </div>
                <div className="quest-xp">+{quest.xpReward} XP</div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default DashboardPage;