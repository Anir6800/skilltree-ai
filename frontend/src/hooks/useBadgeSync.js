/**
 * SkillTree AI - Badge Sync Hook
 * Integrates WebSocket badge events with centralized badge store
 * 
 * Features:
 * - Listens for badge_earned WebSocket events
 * - Syncs with badge store
 * - Handles focus mode queueing
 * - Prevents duplicate displays
 * - Broadcasts badge earned events to UI
 */

import { useEffect, useCallback } from 'react';
import useBadgeStore from '../store/badgeStore';
import useUIStore from '../store/uiStore';

/**
 * Hook to sync badge events from WebSocket with store.
 *
 * `useWebSocket` exposes the latest parsed message as `lastMessage` (it is NOT
 * a socket.io-style emitter with .on/.off), so this hook reacts to changes in
 * that message object.
 *
 * Usage:
 * const { lastMessage } = useWebSocket('/ws/user/');
 * useBadgeSync(lastMessage);
 */
export const useBadgeSync = (lastMessage) => {
  const {
    addEarnedBadge,
    queueBadge,
    markBadgeDisplayed,
  } = useBadgeStore();

  const { focusMode } = useUIStore();

  // Handle badge earned event from WebSocket
  const handleBadgeEarned = useCallback(
    (data) => {
      try {
        // Validate badge data
        if (!data || !data.badge_id) {
          console.warn('Invalid badge data received:', data);
          return;
        }

        // Create badge object
        const badge = {
          id: data.badge_id,
          slug: data.badge_slug,
          name: data.badge_name,
          icon: data.badge_icon,
          rarity: data.rarity,
          description: data.description,
          timestamp: data.timestamp || new Date().toISOString(),
        };

        // Add to earned badges
        addEarnedBadge(badge);

        // Queue or display based on focus mode
        if (focusMode) {
          // Queue for playback on focus mode exit
          queueBadge(badge);
        } else {
          // Show immediately
          markBadgeDisplayed(badge.id);
          window.dispatchEvent(
            new CustomEvent('badgeEarned', { detail: badge })
          );
        }

        console.log(`Badge earned: ${badge.name} (${badge.rarity})`);
      } catch (error) {
        console.error('Error handling badge earned event:', error);
      }
    },
    [addEarnedBadge, queueBadge, markBadgeDisplayed, focusMode]
  );

  // React to incoming WebSocket messages. The backend sends badge unlocks as
  // {type: 'badge_earned', badge_id, ...} to the user's personal group.
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'badge_earned') {
      handleBadgeEarned(lastMessage);
    }
  }, [lastMessage, handleBadgeEarned]);
};

/**
 * Hook to handle badge queue playback
 * Plays queued badges one by one with delay
 * 
 * Usage:
 * useBadgeQueuePlayback();
 */
export const useBadgeQueuePlayback = () => {
  const { badgeQueue, dequeueBadge, peekQueue } = useBadgeStore();
  const { focusMode } = useUIStore();

  useEffect(() => {
    // Only process queue when not in focus mode
    if (focusMode || badgeQueue.length === 0) {
      return;
    }

    const badge = peekQueue();
    if (!badge) {
      return;
    }

    // Display badge
    window.dispatchEvent(
      new CustomEvent('badgeEarned', { detail: badge })
    );

    // Schedule next badge after display time
    const timer = setTimeout(() => {
      dequeueBadge();
    }, 2800); // 2.8s display time

    return () => clearTimeout(timer);
  }, [badgeQueue, focusMode, dequeueBadge, peekQueue]);
};
