/**
 * SkillTree AI - Badge Notifications Hook
 * Integrates WebSocket badge events with focus mode queue
 */

import { useEffect } from 'react';
import useUIStore from '../store/uiStore';

/**
 * Hook to handle badge notifications
 * When focus mode is active, queues badges for playback on exit
 * When focus mode is inactive, shows badges immediately
 */
export const useBadgeNotifications = (socket) => {
  const { focusMode, queueBadgeNotification } = useUIStore();

  useEffect(() => {
    if (!socket) return;

    const handleBadgeEarned = (data) => {
      const badge = {
        id: `${data.badge_slug}_${Date.now()}`,
        badge_slug: data.badge_slug,
        badge_name: data.badge_name,
        badge_icon: data.badge_icon,
        rarity: data.rarity,
        description: data.description,
        timestamp: Date.now(),
      };

      if (focusMode) {
        // Queue badge for playback on exit
        queueBadgeNotification(badge);
      } else {
        // Show badge immediately (handled by existing BadgeUnlockOverlay)
        // Dispatch custom event for immediate display
        window.dispatchEvent(
          new CustomEvent('badgeEarned', { detail: badge })
        );
      }
    };

    socket.on('badge_earned', handleBadgeEarned);

    return () => {
      socket.off('badge_earned', handleBadgeEarned);
    };
  }, [socket, focusMode, queueBadgeNotification]);
};

export default useBadgeNotifications;
