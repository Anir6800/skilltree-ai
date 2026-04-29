/**
 * SkillTree AI - Badge Notification Queue
 * Plays back queued badge notifications one by one with 800ms delay
 * Integrates with BadgeUnlockOverlay for dramatic display
 */

import React, { useState, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import useUIStore from '../store/uiStore';
import BadgeUnlockOverlay from './BadgeUnlockOverlay';

const BadgeNotificationQueue = () => {
  const { badgeQueue, dequeueBadgeNotification, focusMode } = useUIStore();
  const [currentBadge, setCurrentBadge] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    const handleImmediateBadge = (event) => {
      if (!focusMode) {
        setCurrentBadge(event.detail);
        setIsPlaying(true);
      }
    };
    window.addEventListener('badgeEarned', handleImmediateBadge);
    return () => window.removeEventListener('badgeEarned', handleImmediateBadge);
  }, [focusMode]);

  // Process badge queue
  useEffect(() => {
    if (isPlaying || !focusMode) {
      return;
    }

    if (badgeQueue.length === 0) {
      setCurrentBadge(null);
      return;
    }

    // Start playback
    setIsPlaying(true);
    const badge = dequeueBadgeNotification();

    if (badge) {
      setCurrentBadge(badge);

      // Schedule next badge after 800ms delay
      const timer = setTimeout(() => {
        setCurrentBadge(null);
        setIsPlaying(false);
      }, 800 + 2000); // 800ms delay + 2s display time

      return () => clearTimeout(timer);
    }
  }, [badgeQueue, isPlaying, focusMode, dequeueBadgeNotification]);

  const handleClose = () => {
    setCurrentBadge(null);
    setIsPlaying(false);
  };

  return (
    <AnimatePresence>
      {currentBadge && (
        <BadgeUnlockOverlay
          isOpen={!!currentBadge}
          badge={currentBadge}
          onClose={handleClose}
        />
      )}
    </AnimatePresence>
  );
};

export default BadgeNotificationQueue;
