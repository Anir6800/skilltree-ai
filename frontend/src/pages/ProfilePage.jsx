/**
 * SkillTree AI - Profile Page
 * User profile with stats, achievements, and settings
 * @module pages/ProfilePage
 */

import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import useSkillStore from '../store/skillStore';
import useQuestStore from '../store/questStore';
import * as authApi from '../api/authApi';
import { formatXP, formatDate, getLevelFromXP, getRankFromLevel, calculateXPProgress } from '../utils/constants';

/**
 * Profile page component
 * @returns {JSX.Element} Profile page
 */
function ProfilePage() {
  const navigate = useNavigate();
  const { user, fetchUser, updateUser, logout } = useAuthStore();
  const { skills, fetchSkills, progressStats } = useSkillStore();
  const { completedQuests, fetchCompletedQuests } = useQuestStore();
  
  const [activeTab, setActiveTab] = useState('overview');
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({});
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchUser();
    fetchSkills();
    fetchCompletedQuests();
  }, [fetchUser, fetchSkills, fetchCompletedQuests]);

  useEffect(() => {
    if (user) {
      setEditForm({
        username: user.username || '',
        email: user.email || '',
        avatar: user.avatar || '',
      });
    }
  }, [user]);

  /**
   * Handle form change
   * @param {React.ChangeEvent<HTMLInputElement>} e - Change event
   */
  const handleChange = (e) => {
    const { name, value } = e.target;
    setEditForm((prev) => ({ ...prev, [name]: value }));
  };

  /**
   * Handle profile update
   */
  const handleUpdate = async () => {
    setIsLoading(true);
    try {
      const updated = await authApi.updateProfile(editForm);
      updateUser(updated);
      setIsEditing(false);
    } catch (e) {
      console.error('Failed to update profile:', e);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle logout
   */
  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const level = user?.level || getLevelFromXP(user?.xp || 0);
  const rank = user?.rank || getRankFromLevel(level);
  const xpProgress = calculateXPProgress(user?.xp || 0, level);

  return (
    <div className="profile-page">
      {/* Profile Header */}
      <div className="profile-header glass-panel">
        <div className="profile-avatar-section">
          <div className="profile-avatar">
            {user?.avatar ? (
              <img src={user.avatar} alt={user.username} />
            ) : (
              <span className="avatar-placeholder">👤</span>
            )}
          </div>
          {isEditing ? (
            <input
              type="text"
              name="avatar"
              value={editForm.avatar}
              onChange={handleChange}
              placeholder="Avatar URL"
              className="avatar-input"
            />
          ) : (
            <button onClick={() => setIsEditing(true)} className="edit-avatar-btn">
              Change Avatar
            </button>
          )}
        </div>

        <div className="profile-info">
          {isEditing ? (
            <div className="edit-form">
              <input
                type="text"
                name="username"
                value={editForm.username}
                onChange={handleChange}
                className="edit-input"
                placeholder="Username"
              />
              <input
                type="email"
                name="email"
                value={editForm.email}
                onChange={handleChange}
                className="edit-input"
                placeholder="Email"
              />
              <div className="edit-actions">
                <button onClick={handleUpdate} disabled={isLoading} className="primary-cta">
                  {isLoading ? 'Saving...' : 'Save'}
                </button>
                <button onClick={() => setIsEditing(false)} className="secondary-cta">
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <>
              <h1>{user?.username}</h1>
              <p className="profile-email">{user?.email}</p>
              <div className="profile-badges">
                <span className="level-badge">Level {level}</span>
                <span className="rank-badge">{rank}</span>
              </div>
              <button onClick={() => setIsEditing(true)} className="edit-profile-btn">
                Edit Profile
              </button>
            </>
          )}
        </div>

        <div className="profile-stats-summary">
          <div className="summary-stat">
            <span className="stat-value">{formatXP(user?.xp || 0)}</span>
            <span className="stat-label">Total XP</span>
          </div>
          <div className="summary-stat">
            <span className="stat-value">{progressStats?.completed || 0}</span>
            <span className="stat-label">Skills</span>
          </div>
          <div className="summary-stat">
            <span className="stat-value">{completedQuests?.length || 0}</span>
            <span className="stat-label">Quests</span>
          </div>
        </div>
      </div>

      {/* XP Progress */}
      <div className="profile-progress glass-panel">
        <div className="progress-info">
          <span>Level {level} → {level + 1}</span>
          <span>{xpProgress}% complete</span>
        </div>
        <div className="progress-bar">
          <div className="progress-fill premium-gradient" style={{ width: `${xpProgress}%` }} />
        </div>
        <div className="progress-details">
          <span>{user?.xp || 0} XP</span>
          <span>{formatXP(user?.xpToNextLevel || 100)} XP needed</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="profile-tabs">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`tab ${activeTab === 'skills' ? 'active' : ''}`}
          onClick={() => setActiveTab('skills')}
        >
          Skills
        </button>
        <button
          className={`tab ${activeTab === 'achievements' ? 'active' : ''}`}
          onClick={() => setActiveTab('achievements')}
        >
          Achievements
        </button>
        <button
          className={`tab ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          Settings
        </button>
      </div>

      {/* Tab Content */}
      <div className="profile-content">
        {activeTab === 'overview' && (
          <div className="overview-tab">
            <div className="stats-grid">
              <div className="glass-panel stat-card">
                <div className="stat-icon">🎯</div>
                <div className="stat-value">{progressStats?.completed || 0}</div>
                <div className="stat-label">Skills Completed</div>
              </div>
              <div className="glass-panel stat-card">
                <div className="stat-icon">📜</div>
                <div className="stat-value">{completedQuests?.length || 0}</div>
                <div className="stat-label">Quests Completed</div>
              </div>
              <div className="glass-panel stat-card">
                <div className="stat-icon">🔥</div>
                <div className="stat-value">{user?.streak || 0}</div>
                <div className="stat-label">Day Streak</div>
              </div>
              <div className="glass-panel stat-card">
                <div className="stat-icon">⏱️</div>
                <div className="stat-value">{user?.totalTime || 0}h</div>
                <div className="stat-label">Total Time</div>
              </div>
            </div>

            <div className="activity-section glass-panel">
              <h3>Recent Activity</h3>
              <div className="activity-list">
                {user?.recentActivity?.length > 0 ? (
                  user.recentActivity.map((activity, i) => (
                    <div key={i} className="activity-item">
                      <span className="activity-icon">{activity.icon}</span>
                      <div className="activity-info">
                        <span className="activity-title">{activity.title}</span>
                        <span className="activity-time">{formatDate(activity.timestamp)}</span>
                      </div>
                      <span className="activity-xp">+{activity.xp} XP</span>
                    </div>
                  ))
                ) : (
                  <p className="empty-message">No recent activity</p>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'skills' && (
          <div className="skills-tab">
            <div className="skills-progress">
              <h3>Skill Progress</h3>
              <div className="progress-stats">
                <span>{progressStats?.completed || 0} / {progressStats?.total || 0} completed</span>
              </div>
            </div>
            <div className="skills-list">
              {skills.slice(0, 10).map((skill) => (
                <Link
                  key={skill.id}
                  to={`/skills/${skill.id}`}
                  className="glass-panel skill-item"
                >
                  <span className="skill-icon">{skill.icon || '📚'}</span>
                  <span className="skill-name">{skill.name}</span>
                  <span className={`skill-status status-${skill.status}`}>{skill.status}</span>
                </Link>
              ))}
            </div>
            <Link to="/skills" className="view-all-link">View All Skills</Link>
          </div>
        )}

        {activeTab === 'achievements' && (
          <div className="achievements-tab">
            <div className="achievements-grid">
              {user?.achievements?.length > 0 ? (
                user.achievements.map((achievement) => (
                  <div key={achievement.id} className="glass-panel achievement-card">
                    <div className="achievement-icon">{achievement.icon || '🏆'}</div>
                    <h4>{achievement.name}</h4>
                    <p>{achievement.description}</p>
                    <span className="achievement-date">{formatDate(achievement.unlockedAt)}</span>
                  </div>
                ))
              ) : (
                <p className="empty-message">No achievements yet. Keep learning!</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="settings-tab glass-panel">
            <h3>Account Settings</h3>
            
            <div className="setting-group">
              <h4>Security</h4>
              <button className="setting-button">Change Password</button>
              <button className="setting-button">Enable 2FA</button>
            </div>

            <div className="setting-group">
              <h4>Notifications</h4>
              <label className="checkbox-label">
                <input type="checkbox" defaultChecked /> Email notifications
              </label>
              <label className="checkbox-label">
                <input type="checkbox" defaultChecked /> Push notifications
              </label>
            </div>

            <div className="setting-group">
              <h4>Account</h4>
              <button 
                onClick={handleLogout} 
                className="logout-button"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '12px 24px',
                  borderRadius: '12px',
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  color: '#ef4444',
                  fontWeight: 'bold',
                  fontSize: '14px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(239, 68, 68, 0.2)';
                  e.currentTarget.style.boxShadow = '0 0 16px rgba(239, 68, 68, 0.4)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                  <polyline points="16 17 21 12 16 7"></polyline>
                  <line x1="21" y1="12" x2="9" y2="12"></line>
                </svg>
                Log Out
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ProfilePage;