import React from 'react';
import useAuthStore from '../store/authStore';
import { useWebSocket } from '../hooks/useWebSocket';
import { useBadgeSync } from '../hooks/useBadgeSync';

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

  return <>{children}</>;
};

export default GlobalNotificationProvider;
