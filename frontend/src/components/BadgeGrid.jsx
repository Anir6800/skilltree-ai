/**
 * SkillTree AI - Badge Grid
 * Displays all badges on profile page with earned/locked states.
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import './BadgeGrid.css';

const RARITY_COLORS = {
  common: '#94a3b8',
  rare: '#3b82f6',
  epic: '#a855f7',
  legendary: '#f59e0b',
};

const BadgeGrid = ({ badges, earnedBadgeIds }) => {
  const [hoveredBadge, setHoveredBadge] = useState(null);

  const isEarned = (badgeId) => earnedBadgeIds.includes(badgeId);

  return (
    <div className="badge-grid-container">
      <h2 className="badge-grid-title">Achievements</h2>

      <div className="badge-grid">
        {badges.map((badge, index) => {
          const earned = isEarned(badge.id);
          const color = RARITY_COLORS[badge.rarity];

          return (
            <motion.div
              key={badge.id}
              className={`badge-item badge-${badge.rarity} ${earned ? 'earned' : 'locked'}`}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.05, duration: 0.3 }}
              onMouseEnter={() => setHoveredBadge(badge.id)}
              onMouseLeave={() => setHoveredBadge(null)}
              style={{
                '--rarity-color': color,
              }}
            >
              {/* Badge icon */}
              <div className="badge-icon-wrapper">
                <motion.div
                  className="badge-icon"
                  animate={hoveredBadge === badge.id && earned ? { scale: 1.1 } : { scale: 1 }}
                  transition={{ duration: 0.2 }}
                >
                  {badge.icon_emoji}
                </motion.div>

                {earned && (
                  <motion.div
                    className="earned-indicator"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', stiffness: 200 }}
                  >
                    ✓
                  </motion.div>
                )}
              </div>

              {/* Badge info */}
              <div className="badge-info">
                <h3 className="badge-name">{badge.name}</h3>
                <p className="badge-rarity">{badge.rarity}</p>
              </div>

              {/* Tooltip */}
              <motion.div
                className="badge-tooltip"
                initial={{ opacity: 0, y: 10 }}
                animate={
                  hoveredBadge === badge.id
                    ? { opacity: 1, y: 0 }
                    : { opacity: 0, y: 10 }
                }
                transition={{ duration: 0.2 }}
                pointerEvents={hoveredBadge === badge.id ? 'auto' : 'none'}
              >
                <p className="tooltip-description">{badge.description}</p>
                {!earned && (
                  <p className="tooltip-locked">🔒 Locked</p>
                )}
              </motion.div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

export default BadgeGrid;
