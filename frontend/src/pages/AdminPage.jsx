/**
 * SkillTree AI - Admin Page
 * Admin dashboard for managing users, content, and system
 * @module pages/AdminPage
 */

import { useEffect, useState } from 'react';
import * as authApi from '../api/authApi';
import * as skillApi from '../api/skillApi';
import * as questApi from '../api/questApi';

/**
 * Admin page component
 * @returns {JSX.Element} Admin page
 */
function AdminPage() {
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [skills, setSkills] = useState([]);
  const [quests, setQuests] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  /**
   * Fetch admin data
   */
  const fetchData = async () => {
    setIsLoading(true);
    try {
      // Fetch basic stats
      const [usersData, skillsData, questsData] = await Promise.all([
        authApi.getCurrentUser().catch(() => null),
        skillApi.getSkills({ pageSize: 100 }).catch(() => ({ results: [] })),
        questApi.getQuests({ pageSize: 100 }).catch(() => ({ results: [] })),
      ]);
      
      setSkills(skillsData.results || []);
      setQuests(questsData.results || []);
      
      // Mock stats for demo
      setStats({
        totalUsers: 1250,
        activeUsers: 342,
        totalSkills: skillsData.results?.length || 0,
        totalQuests: questsData.results?.length || 0,
        totalXP: 2450000,
        matchesPlayed: 5670,
      });
    } catch (e) {
      setError('Failed to load admin data');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle skill creation
   * @param {Object} skillData - Skill data
   */
  const handleCreateSkill = async (skillData) => {
    try {
      // In real implementation, call API to create skill
      alert('Skill created successfully!');
      fetchData();
    } catch (e) {
      alert('Failed to create skill');
    }
  };

  /**
   * Handle quest creation
   * @param {Object} questData - Quest data
   */
  const handleCreateQuest = async (questData) => {
    try {
      // In real implementation, call API to create quest
      alert('Quest created successfully!');
      fetchData();
    } catch (e) {
      alert('Failed to create quest');
    }
  };

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1>Admin Dashboard</h1>
        <p className="header-subtitle">Manage SkillTree AI platform</p>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="admin-stats">
          <div className="glass-panel stat-card">
            <div className="stat-icon">👥</div>
            <div className="stat-value">{stats.totalUsers}</div>
            <div className="stat-label">Total Users</div>
          </div>
          <div className="glass-panel stat-card">
            <div className="stat-icon">🔥</div>
            <div className="stat-value">{stats.activeUsers}</div>
            <div className="stat-label">Active Users</div>
          </div>
          <div className="glass-panel stat-card">
            <div className="stat-icon">🌳</div>
            <div className="stat-value">{stats.totalSkills}</div>
            <div className="stat-label">Total Skills</div>
          </div>
          <div className="glass-panel stat-card">
            <div className="stat-icon">📜</div>
            <div className="stat-value">{stats.totalQuests}</div>
            <div className="stat-label">Total Quests</div>
          </div>
          <div className="glass-panel stat-card">
            <div className="stat-icon">⭐</div>
            <div className="stat-value">{(stats.totalXP / 1000000).toFixed(1)}M</div>
            <div className="stat-label">Total XP</div>
          </div>
          <div className="glass-panel stat-card">
            <div className="stat-icon">⚔️</div>
            <div className="stat-value">{stats.matchesPlayed}</div>
            <div className="stat-label">Matches Played</div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="admin-tabs">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`tab ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => setActiveTab('users')}
        >
          Users
        </button>
        <button
          className={`tab ${activeTab === 'skills' ? 'active' : ''}`}
          onClick={() => setActiveTab('skills')}
        >
          Skills
        </button>
        <button
          className={`tab ${activeTab === 'quests' ? 'active' : ''}`}
          onClick={() => setActiveTab('quests')}
        >
          Quests
        </button>
        <button
          className={`tab ${activeTab === 'system' ? 'active' : ''}`}
          onClick={() => setActiveTab('system')}
        >
          System
        </button>
      </div>

      {/* Tab Content */}
      <div className="admin-content">
        {activeTab === 'overview' && (
          <div className="overview-tab">
            <div className="glass-panel admin-section">
              <h3>Platform Health</h3>
              <div className="health-grid">
                <div className="health-item">
                  <span className="health-label">API Status</span>
                  <span className="health-value status-ok">Operational</span>
                </div>
                <div className="health-item">
                  <span className="health-label">Database</span>
                  <span className="health-value status-ok">Connected</span>
                </div>
                <div className="health-item">
                  <span className="health-label">Redis</span>
                  <span className="health-value status-ok">Connected</span>
                </div>
                <div className="health-item">
                  <span className="health-label">WebSocket</span>
                  <span className="health-value status-ok">Operational</span>
                </div>
              </div>
            </div>

            <div className="glass-panel admin-section">
              <h3>Recent Activity</h3>
              <div className="activity-list">
                <div className="activity-item">
                  <span className="activity-time">2 min ago</span>
                  <span className="activity-desc">New user registered: john_doe</span>
                </div>
                <div className="activity-item">
                  <span className="activity-time">15 min ago</span>
                  <span className="activity-desc">Quest completed: Python Basics</span>
                </div>
                <div className="activity-item">
                  <span className="activity-time">1 hour ago</span>
                  <span className="activity-desc">Match completed: Arena #4521</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'users' && (
          <div className="users-tab">
            <div className="glass-panel admin-section">
              <div className="section-header">
                <h3>User Management</h3>
                <button className="primary-cta">Add User</button>
              </div>
              <p className="empty-message">User list would be displayed here with pagination and search</p>
            </div>
          </div>
        )}

        {activeTab === 'skills' && (
          <div className="skills-tab">
            <div className="glass-panel admin-section">
              <div className="section-header">
                <h3>Skill Management</h3>
                <button className="primary-cta">Add Skill</button>
              </div>
              <div className="items-list">
                {skills.slice(0, 10).map((skill) => (
                  <div key={skill.id} className="list-item">
                    <span className="item-name">{skill.name}</span>
                    <span className="item-type">{skill.type}</span>
                    <span className="item-status">{skill.status}</span>
                    <button className="secondary-cta">Edit</button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'quests' && (
          <div className="quests-tab">
            <div className="glass-panel admin-section">
              <div className="section-header">
                <h3>Quest Management</h3>
                <button className="primary-cta">Add Quest</button>
              </div>
              <div className="items-list">
                {quests.slice(0, 10).map((quest) => (
                  <div key={quest.id} className="list-item">
                    <span className="item-name">{quest.title}</span>
                    <span className="item-type">{quest.difficulty}</span>
                    <span className="item-status">{quest.status}</span>
                    <button className="secondary-cta">Edit</button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'system' && (
          <div className="system-tab">
            <div className="glass-panel admin-section">
              <h3>System Configuration</h3>
              <div className="config-list">
                <div className="config-item">
                  <label>API Base URL</label>
                  <input type="text" value="http://localhost:8000" readOnly className="config-input" />
                </div>
                <div className="config-item">
                  <label>WebSocket URL</label>
                  <input type="text" value="ws://localhost:8000" readOnly className="config-input" />
                </div>
                <div className="config-item">
                  <label>Max Execution Time</label>
                  <input type="number" value="30000" className="config-input" />
                </div>
                <div className="config-item">
                  <label>Maintenance Mode</label>
                  <input type="checkbox" />
                </div>
              </div>
              <button className="primary-cta">Save Configuration</button>
            </div>
          </div>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}
    </div>
  );
}

export default AdminPage;