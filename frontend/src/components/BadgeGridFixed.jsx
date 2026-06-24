/**
 * SkillTree AI - Badge Grid (Fixed)
 * Displays all badges with real-time sync from store
 * 
 * Features:
 * - Real-time badge state sync
 * - Earned/locked state management
 * - Rarity-based styling
 * - Hover tooltips
 * - Smooth animations
 */

import  { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import useBadgeStore from '../store/badgeStore';
import './BadgeGrid.css';

const RARITY_COLORS = {
  common: '#94a3b8',
  rare: '#3b82f6',
  epic: '#a855f7',
  legendary: '#f59e0b',
};

const RARITY_ORDER = {
  common: 0,
  rare: 1,
  epic: 2,
  legendary: 3,
};

/**
 * BadgeGrid Component
 * 
 * Props:
 * - badges: Array of all badge definitions
 * - onBadgeClick: Optional callback when badge is clicked
 */
const BadgeGrid = ({ badges = [], onBadgeClick }) => {
  const [hoveredBadge, setHoveredBadge] = useState(null);
  const [sortedBadges, setSortedBadges] = useState([]);
  
  // Subscribe to badge store
  const earnedBadges = useBadgeStore((state) => state.earnedBadges);
  const isLoading = useBadgeStore((state) => state.isLoading);
  const error = useBadgeStore((state) => state.error);

  // Sort badges by rarity
  useEffect(() => {
    const sorted = [...badges].sort((a, b) => {
      const rarityDiff = (RARITY_ORDER[a.rarity] || 0) - (RARITY_ORDER[b.rarity] || 0);
      if (rarityDiff !== 0) return rarityDiff;
      return a.name.localeCompare(b.name);
    });
    setSortedBadges(sorted);
  }, [badges]);

  // Check if badge is earned
  const isEarned = (badgeId) => earnedBadges.has(badgeId);

  // Handle badge click
  const handleBadgeClick = (badge) => {
    if (onBadgeClick) {
      onBadgeClick(badge);
    }
  };

  if (isLoading) {
    return (
      <div className="badge-grid-container">
        <h2 className="badge-grid-title">Achievements</h2>
        <div className="badge-grid-loading">Loading badges...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="badge-grid-container">
        <h2 className="badge-grid-title">Achievements</h2>
        <div className="badge-grid-error">Error loading badges: {error}</div>
      </div>
    );
  }

  if (!sortedBadges || sortedBadges.length === 0) {
    return (
      <div className="badge-grid-container">
        <h2 className="badge-grid-title">Achievements</h2>
        <div className="badge-grid-empty">No badges available</div>
      </div>
    );
  }

  // Calculate earned count
  const earnedCount = Array.from(earnedBadges).length;
  const totalCount = sortedBadges.length;
  const progressPercent = Math.round((earnedCount / totalCount) * 100);

  return (
    <div className="badge-grid-container">
      <div className="badge-grid-header">
        <h2 className="badge-grid-title">Achievements</h2>
        <div className="badge-grid-stats">
          <span className="badge-count">
            {earnedCount} / {totalCount}
          </span>
          <div className="badge-progress-bar">
            <motion.div
              className="badge-progress-fill"
              initial={{ width: 0 }}
              animate={{ width: `${progressPercent}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
          <span className="badge-percent">{progressPercent}%</span>
        </div>
      </div>

      <div className="badge-grid">
        {sortedBadges.map((badge, index) => {
          const earned = isEarned(badge.id);
          const color = RARITY_COLORS[badge.rarity] || RARITY_COLORS.common;

          return (
            <motion.div
              key={badge.id}
              className={`badge-item badge-${badge.rarity} ${earned ? 'earned' : 'locked'}`}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.02, duration: 0.3 }}
              onMouseEnter={() => setHoveredBadge(badge.id)}
              onMouseLeave={() => setHoveredBadge(null)}
              onClick={() => handleBadgeClick(badge)}
              style={{
                '--rarity-color': color,
                cursor: 'pointer',
              }}
              role="button"
              tabIndex={0}
              aria-label={`${badge.name} badge - ${earned ? 'earned' : 'locked'}`}
            >
              {/* Badge icon */}
              <div className="badge-icon-wrapper">
                <motion.div
                  className="badge-icon"
                  animate={
                    hoveredBadge === badge.id && earned
                      ? { scale: 1.15, rotate: 5 }
                      : { scale: 1, rotate: 0 }
                  }
                  transition={{ duration: 0.2 }}
                >
                  {badge.icon_emoji}
                </motion.div>

                {/* Earned indicator */}
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

                {/* Locked indicator */}
                {!earned && (
                  <motion.div
                    className="locked-indicator"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', stiffness: 200 }}
                  >
                    🔒
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
                  <p className="tooltip-locked">🔒 Locked - Keep playing to unlock!</p>
                )}
                {earned && badge.earned_at && (
                  <p className="tooltip-earned">
                    ✓ Earned on {new Date(badge.earned_at).toLocaleDateString()}
                  </p>
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
