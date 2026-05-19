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
 * Hook to sync badge events from WebSocket with store
 * 
 * Usage:
 * const socket = useSocket();
 * useBadgeSync(socket);
 */
export const useBadgeSync = (socket) => {
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

  // Set up WebSocket listener
  useEffect(() => {
    if (!socket) {
      console.warn('Socket not available for badge sync');
      return;
    }

    // Listen for badge_earned events
    socket.on('badge_earned', handleBadgeEarned);

    // Cleanup
    return () => {
      socket.off('badge_earned', handleBadgeEarned);
    };
  }, [socket, handleBadgeEarned]);
};

/**
 * Hook to fetch and sync earned badges from API
 * 
 * Usage:
 * useBadgeFetch();
 */
export const useBadgeFetch = () => {
  const { setBadges, setLoading, setError } = useBadgeStore();

  useEffect(() => {
    const fetchBadges = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/badges/', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch badges: ${response.status}`);
        }

        const data = await response.json();
        const earnedBadges = data.results.filter((b) => b.unlocked);
        setBadges(earnedBadges);
        setError(null);
      } catch (error) {
        console.error('Error fetching badges:', error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchBadges();
  }, [setBadges, setLoading, setError]);
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
