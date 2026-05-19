/**
 * SkillTree AI - Badge Store
 * Centralized badge state management with WebSocket sync
 * 
 * Features:
 * - Tracks earned badges with deduplication
 * - Manages badge queue for notifications
 * - Syncs with backend via WebSocket
 * - Prevents duplicate badge displays
 * - Handles focus mode badge queueing
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

/**
 * Badge Store
 * 
 * State:
 * - earnedBadges: Set of earned badge IDs (for O(1) lookup)
 * - badgeQueue: Array of badges to display (FIFO)
 * - recentlyDisplayed: Set of recently shown badge IDs (prevents duplicates)
 * - isLoading: Whether badges are being fetched
 * - error: Error message if fetch failed
 * 
 * Actions:
 * - setBadges: Set earned badges from API
 * - addEarnedBadge: Add single earned badge
 * - queueBadge: Add badge to display queue
 * - dequeueBadge: Remove badge from queue
 * - clearQueue: Clear all queued badges
 * - markBadgeDisplayed: Mark badge as recently displayed
 * - setLoading: Set loading state
 * - setError: Set error state
 */
const useBadgeStore = create(
  devtools(
    (set, get) => ({
      // State
      earnedBadges: new Set(),
      badgeQueue: [],
      recentlyDisplayed: new Set(),
      isLoading: false,
      error: null,

      // Actions

      /**
       * Set earned badges from API response
       * Replaces entire earned badges set
       */
      setBadges: (badges) => {
        set((state) => ({
          earnedBadges: new Set(badges.map((b) => b.id)),
          error: null,
        }));
      },

      /**
       * Add a single earned badge
       * Prevents duplicates via Set
       */
      addEarnedBadge: (badge) => {
        set((state) => {
          const newEarned = new Set(state.earnedBadges);
          newEarned.add(badge.id);
          return { earnedBadges: newEarned };
        });
      },

      /**
       * Queue a badge for display
       * Prevents duplicate queuing within 5 seconds
       */
      queueBadge: (badge) => {
        set((state) => {
          const { recentlyDisplayed, badgeQueue } = state;

          // Prevent duplicate queuing
          if (recentlyDisplayed.has(badge.id)) {
            console.warn(`Badge ${badge.id} already queued recently, skipping`);
            return state;
          }

          // Add to queue
          const newQueue = [...badgeQueue, badge];

          // Mark as recently displayed
          const newRecentlyDisplayed = new Set(recentlyDisplayed);
          newRecentlyDisplayed.add(badge.id);

          // Auto-remove from recently displayed after 5 seconds
          setTimeout(() => {
            set((s) => {
              const updated = new Set(s.recentlyDisplayed);
              updated.delete(badge.id);
              return { recentlyDisplayed: updated };
            });
          }, 5000);

          return {
            badgeQueue: newQueue,
            recentlyDisplayed: newRecentlyDisplayed,
          };
        });
      },

      /**
       * Remove first badge from queue (FIFO)
       */
      dequeueBadge: () => {
        set((state) => {
          const [, ...rest] = state.badgeQueue;
          return { badgeQueue: rest };
        });
      },

      /**
       * Clear all queued badges
       */
      clearQueue: () => {
        set({ badgeQueue: [] });
      },

      /**
       * Mark badge as recently displayed
       * Prevents duplicate displays within time window
       */
      markBadgeDisplayed: (badgeId) => {
        set((state) => {
          const newRecentlyDisplayed = new Set(state.recentlyDisplayed);
          newRecentlyDisplayed.add(badgeId);

          // Auto-remove after 5 seconds
          setTimeout(() => {
            set((s) => {
              const updated = new Set(s.recentlyDisplayed);
              updated.delete(badgeId);
              return { recentlyDisplayed: updated };
            });
          }, 5000);

          return { recentlyDisplayed: newRecentlyDisplayed };
        });
      },

      /**
       * Set loading state
       */
      setLoading: (isLoading) => {
        set({ isLoading });
      },

      /**
       * Set error state
       */
      setError: (error) => {
        set({ error });
      },

      /**
       * Check if badge is earned
       */
      isEarned: (badgeId) => {
        return get().earnedBadges.has(badgeId);
      },

      /**
       * Get current queue length
       */
      getQueueLength: () => {
        return get().badgeQueue.length;
      },

      /**
       * Get first queued badge without removing
       */
      peekQueue: () => {
        const queue = get().badgeQueue;
        return queue.length > 0 ? queue[0] : null;
      },
    }),
    { name: 'BadgeStore' }
  )
);

export default useBadgeStore;
