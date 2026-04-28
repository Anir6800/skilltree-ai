/**
 * SkillTree AI - Hint Panel
 * Tiered hint system with progressive unlock and XP penalties
 * Appears in EditorPage after 5 minutes or 2 failed submissions
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Lightbulb, Map, Wrench, Loader } from 'lucide-react';
import './HintPanel.css';

const HintPanel = ({
  questId,
  currentCode,
  onHintReceived,
  isVisible,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [hints, setHints] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [unlockStatus, setUnlockStatus] = useState({
    level_1: true,
    level_2: false,
    level_3: false,
  });
  const [hintsUsedToday, setHintsUsedToday] = useState(0);

  // Fetch unlock status on mount
  useEffect(() => {
    if (!isVisible || !questId) return;

    const fetchUnlockStatus = async () => {
      try {
        const response = await fetch(
          `/api/mentor/hint/unlock-status/${questId}/`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('auth_access')}`,
            },
          }
        );

        if (response.ok) {
          const data = await response.json();
          setUnlockStatus(data);
        }
      } catch (err) {
        console.error('Failed to fetch unlock status:', err);
      }
    };

    fetchUnlockStatus();
  }, [questId, isVisible]);

  const requestHint = async (hintLevel) => {
    if (loading) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/mentor/hint/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_access')}`,
        },
        body: JSON.stringify({
          quest_id: questId,
          hint_level: hintLevel,
          current_code: currentCode || '',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to get hint');
      }

      const data = await response.json();

      // Store hint
      setHints((prev) => ({
        ...prev,
        [hintLevel]: data.hint_text,
      }));

      setHintsUsedToday(data.hints_used_today);

      // Update unlock status
      if (hintLevel === 1) {
        setUnlockStatus((prev) => ({
          ...prev,
          level_2: true,
        }));
      } else if (hintLevel === 2) {
        setUnlockStatus((prev) => ({
          ...prev,
          level_3: true,
        }));
      }

      // Callback
      if (onHintReceived) {
        onHintReceived({
          level: hintLevel,
          text: data.hint_text,
          xpPenalty: data.xp_penalty,
        });
      }
    } catch (err) {
      setError(err.message);
      console.error('Error requesting hint:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!isVisible) {
    return null;
  }

  const hintButtons = [
    {
      level: 1,
      icon: Lightbulb,
      label: 'Nudge',
      description: 'Conceptual nudge',
      xpPenalty: 0,
      unlocked: unlockStatus.level_1,
    },
    {
      level: 2,
      icon: Map,
      label: 'Approach',
      description: 'Algorithm explanation',
      xpPenalty: 10,
      unlocked: unlockStatus.level_2,
    },
    {
      level: 3,
      icon: Wrench,
      label: 'Skeleton',
      description: 'Code skeleton',
      xpPenalty: 25,
      unlocked: unlockStatus.level_3,
    },
  ];

  return (
    <motion.div
      className="hint-panel-container"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      transition={{ duration: 0.3 }}
    >
      {/* Header */}
      <motion.button
        className="hint-panel-header"
        onClick={() => setIsExpanded(!isExpanded)}
        whileHover={{ backgroundColor: 'rgba(99, 102, 241, 0.1)' }}
      >
        <div className="hint-panel-title">
          <Lightbulb size={18} className="hint-icon" />
          <span>Need Help?</span>
        </div>
        <motion.div
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronDown size={18} />
        </motion.div>
      </motion.button>

      {/* Expanded Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            className="hint-panel-content"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
          >
            {/* Rate Limit Info */}
            <div className="hint-rate-limit">
              <span className="hint-count">{hintsUsedToday}/5 hints used today</span>
              {hintsUsedToday >= 5 && (
                <span className="hint-limit-reached">Rate limit reached</span>
              )}
            </div>

            {/* Hint Buttons */}
            <div className="hint-buttons-grid">
              {hintButtons.map((btn) => {
                const Icon = btn.icon;
                const hasHint = hints[btn.level];
                const isDisabled = !btn.unlocked || loading || hintsUsedToday >= 5;

                return (
                  <motion.button
                    key={btn.level}
                    className={`hint-button ${hasHint ? 'has-hint' : ''} ${
                      isDisabled ? 'disabled' : ''
                    }`}
                    onClick={() => requestHint(btn.level)}
                    disabled={isDisabled}
                    whileHover={!isDisabled ? { scale: 1.05 } : {}}
                    whileTap={!isDisabled ? { scale: 0.95 } : {}}
                    title={
                      !btn.unlocked
                        ? `Unlock by using Level ${btn.level - 1} hint`
                        : hasHint
                        ? 'Hint already received'
                        : `${btn.label} - ${btn.xpPenalty > 0 ? `-${btn.xpPenalty} XP` : 'No penalty'}`
                    }
                  >
                    <div className="hint-button-content">
                      <Icon size={20} />
                      <div className="hint-button-text">
                        <div className="hint-button-label">{btn.label}</div>
                        <div className="hint-button-desc">{btn.description}</div>
                      </div>
                    </div>

                    {/* XP Penalty Badge */}
                    {btn.xpPenalty > 0 && !hasHint && (
                      <div className="hint-xp-penalty">-{btn.xpPenalty} XP</div>
                    )}

                    {/* Loading Indicator */}
                    {loading && (
                      <motion.div
                        className="hint-loading"
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity }}
                      >
                        <Loader size={16} />
                      </motion.div>
                    )}

                    {/* Received Indicator */}
                    {hasHint && (
                      <div className="hint-received">✓</div>
                    )}

                    {/* Locked Indicator */}
                    {!btn.unlocked && (
                      <div className="hint-locked">🔒</div>
                    )}
                  </motion.button>
                );
              })}
            </div>

            {/* Error Message */}
            {error && (
              <motion.div
                className="hint-error"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                {error}
              </motion.div>
            )}

            {/* Hint Display */}
            {Object.keys(hints).length > 0 && (
              <div className="hint-display-section">
                <div className="hint-display-title">Your Hints</div>
                {[1, 2, 3].map((level) => {
                  if (!hints[level]) return null;

                  const levelNames = {
                    1: 'Nudge',
                    2: 'Approach',
                    3: 'Skeleton',
                  };

                  return (
                    <motion.div
                      key={level}
                      className="hint-display-item"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: level * 0.1 }}
                    >
                      <div className="hint-display-header">
                        <span className="hint-display-level">Level {level}: {levelNames[level]}</span>
                      </div>
                      <div className="hint-display-text">
                        {hints[level]}
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            )}

            {/* Info Text */}
            <div className="hint-info">
              <p>
                💡 <strong>Level 1 (Nudge)</strong>: Conceptual direction, no code
              </p>
              <p>
                🗺 <strong>Level 2 (Approach)</strong>: Algorithm explanation, pseudocode
              </p>
              <p>
                🔧 <strong>Level 3 (Skeleton)</strong>: Code skeleton with TODOs
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default HintPanel;
