/**
 * SkillTree AI - Quest Page
 * Quest browsing and management
 * @module pages/QuestPage
 */

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import useQuestStore from '../store/questStore';
import { QUEST_STATUS, QUEST_DIFFICULTY } from '../constants';
import { formatXP, formatRelativeTime } from '../utils/constants';

/**
 * Quest page component
 * @returns {JSX.Element} Quest page
 */
function QuestPage() {
  const {
    quests,
    activeQuests,
    isLoading,
    error,
    fetchQuests,
    fetchActiveQuests,
    setFilters,
    filters,
  } = useQuestStore();

  const [activeTab, setActiveTab] = useState('available');

  useEffect(() => {
    fetchQuests();
    fetchActiveQuests();
  }, [fetchQuests, fetchActiveQuests]);

  /**
   * Get difficulty color class
   * @param {string} difficulty - Quest difficulty
   * @returns {string} CSS class
   */
  const getDifficultyClass = (difficulty) => {
    const classes = {
      [QUEST_DIFFICULTY.EASY]: 'difficulty-easy',
      [QUEST_DIFFICULTY.MEDIUM]: 'difficulty-medium',
      [QUEST_DIFFICULTY.HARD]: 'difficulty-hard',
      [QUEST_DIFFICULTY.EXPERT]: 'difficulty-expert',
    };
    return classes[difficulty] || '';
  };

  /**
   * Get status color class
   * @param {string} status - Quest status
   * @returns {string} CSS class
   */
  const getStatusClass = (status) => {
    const classes = {
      [QUEST_STATUS.AVAILABLE]: 'status-available',
      [QUEST_STATUS.IN_PROGRESS]: 'status-in-progress',
      [QUEST_STATUS.COMPLETED]: 'status-completed',
      [QUEST_STATUS.FAILED]: 'status-failed',
    };
    return classes[status] || '';
  };

  return (
    <div className="quest-page">
      <div className="quest-header">
        <h1>Quests</h1>
        <p className="header-subtitle">Complete quests to earn XP and level up</p>
      </div>

      {/* Tabs */}
      <div className="quest-tabs">
        <button
          className={`tab ${activeTab === 'available' ? 'active' : ''}`}
          onClick={() => setActiveTab('available')}
        >
          Available ({quests.filter(q => q.status === QUEST_STATUS.AVAILABLE).length})
        </button>
        <button
          className={`tab ${activeTab === 'active' ? 'active' : ''}`}
          onClick={() => setActiveTab('active')}
        >
          Active ({activeQuests.length})
        </button>
        <button
          className={`tab ${activeTab === 'completed' ? 'active' : ''}`}
          onClick={() => setActiveTab('completed')}
        >
          Completed
        </button>
      </div>

      {/* Filters */}
      <div className="quest-filters">
        <select
          value={filters.difficulty || ''}
          onChange={(e) => setFilters({ difficulty: e.target.value || null })}
          className="filter-select"
        >
          <option value="">All Difficulties</option>
          <option value={QUEST_DIFFICULTY.EASY}>Easy</option>
          <option value={QUEST_DIFFICULTY.MEDIUM}>Medium</option>
          <option value={QUEST_DIFFICULTY.HARD}>Hard</option>
          <option value={QUEST_DIFFICULTY.EXPERT}>Expert</option>
        </select>
      </div>

      {/* Quest List */}
      <div className="quest-list">
        {isLoading ? (
          <div className="loading-message">Loading quests...</div>
        ) : activeTab === 'available' && quests.filter(q => q.status === QUEST_STATUS.AVAILABLE).length === 0 ? (
          <div className="empty-message">No available quests</div>
        ) : (
          (activeTab === 'available' ? quests.filter(q => q.status === QUEST_STATUS.AVAILABLE) : 
           activeTab === 'active' ? activeQuests : 
           quests.filter(q => q.status === QUEST_STATUS.COMPLETED)).map((quest) => (
            <Link
              key={quest.id}
              to={`/quests/${quest.id}`}
              className="glass-panel quest-card"
            >
              <div className="quest-card-header">
                <h3>{quest.title}</h3>
                <span className={`difficulty-badge ${getDifficultyClass(quest.difficulty)}`}>
                  {quest.difficulty}
                </span>
              </div>
              <p className="quest-description">{quest.description}</p>
              <div className="quest-card-footer">
                <div className="quest-meta">
                  <span className="quest-xp">+{formatXP(quest.xpReward)} XP</span>
                  {quest.category && <span className="quest-category">{quest.category}</span>}
                </div>
                <span className={`status-badge ${getStatusClass(quest.status)}`}>
                  {quest.status}
                </span>
              </div>
            </Link>
          ))
        )}
      </div>

      {error && <div className="error-message">{error}</div>}
    </div>
  );
}

export default QuestPage;