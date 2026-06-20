import React from 'react';
import useAuthStore from '../store/authStore';
import { useWebSocket } from '../hooks/useWebSocket';
import { useBadgeSync, useBadgeQueuePlayback } from '../hooks/useBadgeSync';

/**
 * GlobalNotificationProvider
 * Establishes a background WebSocket connection for the authenticated user
 * to receive global real-time notifications (such as badge unlocks).
 */
const GlobalNotificationProvider = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  
  // Only connect to global notifications if the user is authenticated
  const wsUrl = isAuthenticated ? `/ws/user/` : null;
  const { lastMessage } = useWebSocket(wsUrl, {
    reconnectInterval: 5000,
    reconnectAttempts: 10,
  });

  // Sync badge events from the WebSocket's latest message
  useBadgeSync(lastMessage);

  // Replay badges that were queued while in focus mode, once it's exited.
  useBadgeQueuePlayback();

  return <>{children}</>;
};

export default GlobalNotificationProvider;
