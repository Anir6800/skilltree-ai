/**
 * SkillTree AI - Badge Unlock Overlay
 * Dramatic full-screen overlay for legendary/epic badge unlocks.
 * Features animated badge icon, particle burst, and rarity-specific styling.
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './BadgeUnlockOverlay.css';

const RARITY_COLORS = {
  common: '#94a3b8',
  rare: '#3b82f6',
  epic: '#a855f7',
  legendary: '#f59e0b',
};

const RARITY_GLOW = {
  common: 'rgba(148, 163, 184, 0.3)',
  rare: 'rgba(59, 130, 246, 0.3)',
  epic: 'rgba(168, 85, 247, 0.3)',
  legendary: 'rgba(245, 158, 11, 0.3)',
};

const BadgeUnlockOverlay = ({
  isOpen,
  badge,
  onClose,
}) => {
  const [particles, setParticles] = useState([]);
  const [showContent, setShowContent] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      setShowContent(false);
      return;
    }

    // Generate particles for burst effect
    const newParticles = Array.from({ length: 30 }, (_, i) => ({
      id: i,
      angle: (i / 30) * Math.PI * 2,
      distance: 200 + Math.random() * 100,
      duration: 1 + Math.random() * 0.5,
    }));

    setParticles(newParticles);

    // Show content after slight delay
    const timer = setTimeout(() => setShowContent(true), 300);

    return () => clearTimeout(timer);
  }, [isOpen]);

  const rarityColor = RARITY_COLORS[badge?.rarity] || RARITY_COLORS.common;
  const rarityGlow = RARITY_GLOW[badge?.rarity] || RARITY_GLOW.common;

  return (
    <AnimatePresence>
      {isOpen && badge && (
        <motion.div
          className="badge-unlock-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          onClick={onClose}
        >
          {/* Particle burst effect */}
          <div className="particle-container">
            {particles.map((particle) => (
              <motion.div
                key={particle.id}
                className="particle"
                style={{
                  left: '50%',
                  top: '50%',
                  backgroundColor: rarityColor,
                }}
                initial={{
                  x: 0,
                  y: 0,
                  opacity: 1,
                  scale: 1,
                }}
                animate={{
                  x: Math.cos(particle.angle) * particle.distance,
                  y: Math.sin(particle.angle) * particle.distance,
                  opacity: 0,
                  scale: 0,
                }}
                transition={{
                  duration: particle.duration,
                  ease: 'easeOut',
                }}
              />
            ))}
          </div>

          {/* Main badge card */}
          <motion.div
            className={`badge-unlock-card badge-${badge.rarity}`}
            initial={{ scale: 0.1, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.1, opacity: 0 }}
            transition={{
              type: 'spring',
              stiffness: 100,
              damping: 15,
              duration: 0.6,
            }}
            onClick={(e) => e.stopPropagation()}
            style={{
              '--rarity-color': rarityColor,
              '--rarity-glow': rarityGlow,
            }}
          >
            {/* Animated badge icon */}
            <motion.div
              className="badge-icon-container"
              initial={{ scale: 0.1 }}
              animate={{ scale: 1 }}
              transition={{
                type: 'spring',
                stiffness: 200,
                damping: 10,
                delay: 0.2,
              }}
            >
              <motion.div
                className="badge-icon"
                animate={{
                  y: [0, -10, 0],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
              >
                {badge.icon_emoji}
              </motion.div>

              {/* Glow effect */}
              <motion.div
                className="badge-glow"
                animate={{
                  scale: [1, 1.2, 1],
                  opacity: [0.5, 0.8, 0.5],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
              />
            </motion.div>

            {/* Content */}
            <AnimatePresence>
              {showContent && (
                <motion.div
                  className="badge-content"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 20 }}
                  transition={{ duration: 0.4 }}
                >
                  <h1 className="badge-title">New Badge Unlocked!</h1>

                  <h2 className="badge-name">{badge.name}</h2>

                  <p className="badge-description">{badge.description}</p>

                  <div className="badge-rarity">
                    <span className={`rarity-badge rarity-${badge.rarity}`}>
                      {badge.rarity.toUpperCase()}
                    </span>
                  </div>

                  <motion.button
                    className="badge-close-btn"
                    onClick={onClose}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    Awesome! ✨
                  </motion.button>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default BadgeUnlockOverlay;
