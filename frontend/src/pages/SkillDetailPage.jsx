/**
 * SkillTree AI - Skill Detail Page
 * Detailed view of a single skill with learning content
 * @module pages/SkillDetailPage
 */

import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import useSkillStore from '../store/skillStore';
import useExecution from '../hooks/useExecution';
import { SKILL_STATUS, SKILL_NODE_TYPES } from '../constants';
import { formatXP } from '../utils/constants';

/**
 * Skill detail page component
 * @returns {JSX.Element} Skill detail page
 */
function SkillDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { selectedSkill, fetchSkill, isLoading, error, unlockSkill, startLearning, completeSkill, clearSelectedSkill } = useSkillStore();
  const { execute, status: execStatus, output, error: execError, isRunning } = useExecution();

  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (id) {
      fetchSkill(id);
    }
    return () => clearSelectedSkill();
  }, [id, fetchSkill, clearSelectedSkill]);

  /**
   * Handle skill unlock
   */
  const handleUnlock = async () => {
    try {
      await unlockSkill(id);
    } catch (e) {
      // Error handled by store
    }
  };

  /**
   * Handle start learning
   */
  const handleStartLearning = async () => {
    try {
      await startLearning(id);
    } catch (e) {
      // Error handled by store
    }
  };

  /**
   * Handle code execution
   */
  const handleRunCode = async () => {
    try {
      await execute({ code, language, skillId: id });
    } catch (e) {
      // Error handled by execution hook
    }
  };

  /**
   * Handle skill completion
   */
  const handleComplete = async () => {
    try {
      await completeSkill(id, { code, output });
      navigate('/skills');
    } catch (e) {
      // Error handled by store
    }
  };

  if (isLoading || !selectedSkill) {
    return <div className="skill-detail-page loading">Loading skill...</div>;
  }

  const getTypeClass = (type) => {
    const classes = {
      [SKILL_NODE_TYPES.CORE]: 'node-core',
      [SKILL_NODE_TYPES.ADVANCED]: 'node-advanced',
      [SKILL_NODE_TYPES.ELITE]: 'node-elite',
      [SKILL_NODE_TYPES.LEGENDARY]: 'node-legendary',
    };
    return classes[type] || '';
  };

  return (
    <div className="skill-detail-page">
      <div className="skill-detail-header">
        <Link to="/skills" className="back-link">← Back to Skill Tree</Link>
        
        <div className="skill-header-content">
          <div className="skill-icon-large">{selectedSkill.icon || '📚'}</div>
          <div className="skill-header-info">
            <h1>{selectedSkill.name}</h1>
            <div className="skill-meta">
              <span className={`type-badge ${getTypeClass(selectedSkill.type)}`}>
                {selectedSkill.type}
              </span>
              <span className={`status-badge status-${selectedSkill.status}`}>
                {selectedSkill.status}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="skill-tabs">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`tab ${activeTab === 'content' ? 'active' : ''}`}
          onClick={() => setActiveTab('content')}
        >
          Content
        </button>
        <button
          className={`tab ${activeTab === 'practice' ? 'active' : ''}`}
          onClick={() => setActiveTab('practice')}
        >
          Practice
        </button>
      </div>

      {/* Tab Content */}
      <div className="skill-content">
        {activeTab === 'overview' && (
          <div className="overview-tab glass-panel">
            <div className="section">
              <h3>Description</h3>
              <p>{selectedSkill.description}</p>
            </div>
            
            <div className="section">
              <h3>Details</h3>
              <div className="detail-grid">
                <div className="detail-item">
                  <span className="label">XP Cost</span>
                  <span className="value">{formatXP(selectedSkill.xpCost || 0)}</span>
                </div>
                <div className="detail-item">
                  <span className="label">XP Reward</span>
                  <span className="value">+{formatXP(selectedSkill.xpReward || 0)}</span>
                </div>
                <div className="detail-item">
                  <span className="label">Category</span>
                  <span className="value">{selectedSkill.category || 'General'}</span>
                </div>
                <div className="detail-item">
                  <span className="label">Type</span>
                  <span className="value">{selectedSkill.type}</span>
                </div>
              </div>
            </div>

            {selectedSkill.prerequisites?.length > 0 && (
              <div className="section">
                <h3>Prerequisites</h3>
                <ul className="prerequisites-list">
                  {selectedSkill.prerequisites.map((prereq) => (
                    <li key={prereq}>
                      <Link to={`/skills/${prereq}`}>{prereq}</Link>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="action-buttons">
              {selectedSkill.status === SKILL_STATUS.LOCKED && (
                <button onClick={handleUnlock} className="primary-cta">
                  Unlock ({formatXP(selectedSkill.xpCost || 0)} XP)
                </button>
              )}
              {selectedSkill.status === SKILL_STATUS.AVAILABLE && (
                <button onClick={handleStartLearning} className="primary-cta">
                  Start Learning
                </button>
              )}
              {selectedSkill.status === SKILL_STATUS.IN_PROGRESS && (
                <button onClick={() => setActiveTab('practice')} className="primary-cta">
                  Continue Learning
                </button>
              )}
              {selectedSkill.status === SKILL_STATUS.COMPLETED && (
                <div className="completed-badge">✓ Completed</div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'content' && (
          <div className="content-tab glass-panel">
            <div className="lesson-content">
              {selectedSkill.content || selectedSkill.lessons?.map((lesson) => (
                <div key={lesson.id} className="lesson-item">
                  <h4>{lesson.title}</h4>
                  <p>{lesson.content}</p>
                </div>
              )) || <p>No content available yet.</p>}
            </div>
          </div>
        )}

        {activeTab === 'practice' && (
          <div className="practice-tab">
            <div className="code-editor glass-panel">
              <div className="editor-header">
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
                <div className="editor-actions">
                  <button
                    onClick={handleRunCode}
                    disabled={isRunning}
                    className="run-button"
                  >
                    {isRunning ? 'Running...' : 'Run Code'}
                  </button>
                </div>
              </div>
              <textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="code-textarea"
                placeholder="Write your code here..."
                spellCheck={false}
              />
            </div>

            <div className="output-panel glass-panel">
              <h4>Output</h4>
              {execError && <div className="output-error">{execError}</div>}
              {output && <pre className="output-content">{output}</pre>}
              {!output && !execError && <div className="output-empty">Run your code to see output</div>}
            </div>

            {selectedSkill.status === SKILL_STATUS.IN_PROGRESS && (
              <button onClick={handleComplete} className="primary-cta complete-button">
                Mark as Complete
              </button>
            )}
          </div>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}
    </div>
  );
}

export default SkillDetailPage;