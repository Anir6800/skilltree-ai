/**
 * SkillTree AI - Skill Tree Page
 * Interactive skill tree visualization
 * @module pages/SkillTreePage
 */

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import useSkillTree from '../hooks/useSkillTree';
import { SKILL_STATUS, SKILL_NODE_TYPES } from '../constants';

/**
 * Skill tree page component
 * @returns {JSX.Element} Skill tree page
 */
function SkillTreePage() {
  const {
    skills,
    selectedSkill,
    isLoading,
    error,
    fetchSkillTree,
    selectSkill,
    clearSelectedSkill,
    treeVisualization,
    progressStats,
    setFilters,
    filters,
  } = useSkillTree({ autoFetch: true });

  const [viewMode, setViewMode] = useState('tree');

  useEffect(() => {
    fetchSkillTree();
  }, [fetchSkillTree]);

  /**
   * Get status color class
   * @param {string} status - Skill status
   * @returns {string} CSS class
   */
  const getStatusClass = (status) => {
    const classes = {
      [SKILL_STATUS.LOCKED]: 'skill-locked',
      [SKILL_STATUS.AVAILABLE]: 'skill-available',
      [SKILL_STATUS.IN_PROGRESS]: 'skill-in-progress',
      [SKILL_STATUS.COMPLETED]: 'skill-completed',
    };
    return classes[status] || '';
  };

  /**
   * Get node type class
   * @param {string} type - Node type
   * @returns {string} CSS class
   */
  const getTypeClass = (type) => {
    const classes = {
      [SKILL_NODE_TYPES.CORE]: 'node-core',
      [SKILL_NODE_TYPES.ADVANCED]: 'node-advanced',
      [SKILL_NODE_TYPES.ELITE]: 'node-elite',
      [SKILL_NODE_TYPES.LEGENDARY]: 'node-legendary',
    };
    return classes[type] || '';
  };

  if (isLoading && !skills.length) {
    return (
      <div className="skill-tree-page loading">
        <div className="loading-spinner">Loading skill tree...</div>
      </div>
    );
  }

  return (
    <div className="skill-tree-page">
      <div className="skill-tree-header">
        <div className="header-content">
          <h1>Skill Tree</h1>
          <p className="header-subtitle">
            {progressStats.completed} / {progressStats.total} skills completed
          </p>
        </div>
        
        <div className="view-controls">
          <button
            className={`view-btn ${viewMode === 'tree' ? 'active' : ''}`}
            onClick={() => setViewMode('tree')}
          >
            Tree View
          </button>
          <button
            className={`view-btn ${viewMode === 'list' ? 'active' : ''}`}
            onClick={() => setViewMode('list')}
          >
            List View
          </button>
        </div>
      </div>

      {/* Progress Overview */}
      <div className="skill-progress-overview glass-panel">
        <div className="progress-stat">
          <span className="stat-number">{progressStats.completed}</span>
          <span className="stat-text">Completed</span>
        </div>
        <div className="progress-stat">
          <span className="stat-number">{progressStats.inProgress}</span>
          <span className="stat-text">In Progress</span>
        </div>
        <div className="progress-stat">
          <span className="stat-number">{progressStats.available}</span>
          <span className="stat-text">Available</span>
        </div>
        <div className="progress-stat">
          <span className="stat-number">{progressStats.locked}</span>
          <span className="stat-text">Locked</span>
        </div>
      </div>

      {/* Filters */}
      <div className="skill-filters">
        <select
          value={filters.status || ''}
          onChange={(e) => setFilters({ status: e.target.value || null })}
          className="filter-select"
        >
          <option value="">All Status</option>
          <option value={SKILL_STATUS.AVAILABLE}>Available</option>
          <option value={SKILL_STATUS.IN_PROGRESS}>In Progress</option>
          <option value={SKILL_STATUS.COMPLETED}>Completed</option>
          <option value={SKILL_STATUS.LOCKED}>Locked</option>
        </select>

        <select
          value={filters.type || ''}
          onChange={(e) => setFilters({ type: e.target.value || null })}
          className="filter-select"
        >
          <option value="">All Types</option>
          <option value={SKILL_NODE_TYPES.CORE}>Core</option>
          <option value={SKILL_NODE_TYPES.ADVANCED}>Advanced</option>
          <option value={SKILL_NODE_TYPES.ELITE}>Elite</option>
          <option value={SKILL_NODE_TYPES.LEGENDARY}>Legendary</option>
        </select>
      </div>

      {/* Skill Tree Visualization */}
      {viewMode === 'tree' ? (
        <div className="skill-tree-visualization glass-panel">
          <div className="tree-container">
            {skills.map((skill) => (
              <div
                key={skill.id}
                className={`skill-node ${getStatusClass(skill.status)} ${getTypeClass(skill.type)}`}
                onClick={() => selectSkill(skill)}
                style={{
                  left: skill.x || 0,
                  top: skill.y || 0,
                }}
              >
                <div className="node-icon">{skill.icon || '📚'}</div>
                <div className="node-label">{skill.name}</div>
                {skill.status === SKILL_STATUS.COMPLETED && (
                  <div className="node-check">✓</div>
                )}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="skill-list">
          {skills.map((skill) => (
            <Link
              key={skill.id}
              to={`/skills/${skill.id}`}
              className={`glass-panel skill-list-item ${getStatusClass(skill.status)}`}
            >
              <div className="skill-icon">{skill.icon || '📚'}</div>
              <div className="skill-info">
                <h3>{skill.name}</h3>
                <p>{skill.description}</p>
                <div className="skill-meta">
                  <span className={`type-badge ${getTypeClass(skill.type)}`}>
                    {skill.type}
                  </span>
                  <span className={`status-badge ${getStatusClass(skill.status)}`}>
                    {skill.status}
                  </span>
                </div>
              </div>
              <div className="skill-xp">
                {skill.xpReward > 0 && <span>+{skill.xpReward} XP</span>}
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Selected Skill Modal */}
      {selectedSkill && (
        <div className="skill-modal-overlay" onClick={clearSelectedSkill}>
          <div className="skill-modal glass-panel" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={clearSelectedSkill}>×</button>
            <div className="modal-header">
              <div className="modal-icon">{selectedSkill.icon || '📚'}</div>
              <h2>{selectedSkill.name}</h2>
              <span className={`type-badge ${getTypeClass(selectedSkill.type)}`}>
                {selectedSkill.type}
              </span>
            </div>
            <p className="modal-description">{selectedSkill.description}</p>
            <div className="modal-stats">
              <div className="modal-stat">
                <span className="label">XP Cost</span>
                <span className="value">{selectedSkill.xpCost || 0}</span>
              </div>
              <div className="modal-stat">
                <span className="label">XP Reward</span>
                <span className="value">+{selectedSkill.xpReward || 0}</span>
              </div>
              <div className="modal-stat">
                <span className="label">Status</span>
                <span className={`value status-badge ${getStatusClass(selectedSkill.status)}`}>
                  {selectedSkill.status}
                </span>
              </div>
            </div>
            {selectedSkill.prerequisites?.length > 0 && (
              <div className="modal-prerequisites">
                <h4>Prerequisites</h4>
                <ul>
                  {selectedSkill.prerequisites.map((prereq) => (
                    <li key={prereq}>{prereq}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className="modal-actions">
              {selectedSkill.status === SKILL_STATUS.AVAILABLE && (
                <button className="primary-cta">Start Learning</button>
              )}
              {selectedSkill.status === SKILL_STATUS.IN_PROGRESS && (
                <button className="primary-cta">Continue</button>
              )}
              <Link to={`/skills/${selectedSkill.id}`} className="secondary-cta">
                View Details
              </Link>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
    </div>
  );
}

export default SkillTreePage;