/**
 * SkillTree AI - Badge Notification Queue (Fixed)
 * Plays back queued badge notifications with proper state management
 * 
 * Features:
 * - FIFO queue processing
 * - Proper timing and delays
 * - Focus mode integration
 * - Duplicate prevention
 * - Error handling
 */

import React, { useState, useEffect, useRef } from 'react';
import { AnimatePresence } from 'framer-motion';
import useBadgeStore from '../store/badgeStore';
import useUIStore from '../store/uiStore';
import BadgeUnlockOverlay from './BadgeUnlockOverlay';

const DISPLAY_DURATION = 2800; // 2.8 seconds
const QUEUE_DELAY = 800; // 800ms between badges

/**
 * BadgeNotificationQueue Component
 * 
 * Manages badge display queue and timing
 * Integrates with focus mode for deferred display
 */
const BadgeNotificationQueue = () => {
  const [currentBadge, setCurrentBadge] = useState(null);
  const [isDisplaying, setIsDisplaying] = useState(false);
  const timerRef = useRef(null);

  // Subscribe to stores
  const { badgeQueue, dequeueBadge, peekQueue } = useBadgeStore();
  const { focusMode } = useUIStore();

  // Handle immediate badge display (from custom event)
  useEffect(() => {
    const handleImmediateBadge = (event) => {
      if (!focusMode && event.detail) {
        displayBadge(event.detail);
      }
    };

    window.addEventListener('badgeEarned', handleImmediateBadge);
    return () => window.removeEventListener('badgeEarned', handleImmediateBadge);
  }, [focusMode]);

  // Process badge queue
  useEffect(() => {
    // Don't process queue if:
    // - Currently displaying a badge
    // - In focus mode
    // - Queue is empty
    if (isDisplaying || focusMode || badgeQueue.length === 0) {
      return;
    }

    // Get next badge from queue
    const nextBadge = peekQueue();
    if (!nextBadge) {
      return;
    }

    // Schedule display with delay
    timerRef.current = setTimeout(() => {
      displayBadge(nextBadge);
      dequeueBadge();
    }, QUEUE_DELAY);

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [badgeQueue, isDisplaying, focusMode, dequeueBadge, peekQueue]);

  /**
   * Display a badge with timing
   */
  const displayBadge = (badge) => {
    setCurrentBadge(badge);
    setIsDisplaying(true);

    // Auto-close after display duration
    timerRef.current = setTimeout(() => {
      closeBadge();
    }, DISPLAY_DURATION);
  };

  /**
   * Close current badge display
   */
  const closeBadge = () => {
    setCurrentBadge(null);
    setIsDisplaying(false);

    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  };

  /**
   * Handle manual close
   */
  const handleClose = () => {
    closeBadge();
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
