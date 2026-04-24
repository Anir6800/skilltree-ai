/**
 * SkillTree AI - WebSocket Hook
 * Custom hook for WebSocket connections with auto-reconnect
 * @module hooks/useWebSocket
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { WS_URL } from '../constants';

/**
 * WebSocket connection states
 * @readonly
 * @enum {string}
 */
const WS_STATE = {
  CONNECTING: 'connecting',
  OPEN: 'open',
  CLOSING: 'closing',
  CLOSED: 'closed',
};

/**
 * Custom hook for WebSocket connections
 * @param {string} path - WebSocket path (e.g., '/ws/multiplayer/')
 * @param {Object} options - WebSocket options
 * @param {function} options.onOpen - Callback when connection opens
 * @param {function} options.onMessage - Callback when message received
 * @param {function} options.onError - Callback on error
 * @param {function} options.onClose - Callback when connection closes
 * @param {boolean} options.autoConnect - Auto-connect on mount (default: true)
 * @param {number} options.reconnectAttempts - Max reconnect attempts (default: 5)
 * @param {number} options.reconnectInterval - Reconnect interval in ms (default: 3000)
 * @returns {Object} WebSocket methods and state
 */
export function useWebSocket(path, options = {}) {
  const {
    onOpen,
    onMessage,
    onError,
    onClose,
    autoConnect = true,
    reconnectAttempts = 5,
    reconnectInterval = 3000,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [connectionState, setConnectionState] = useState(WS_STATE.CLOSED);
  
  const wsRef = useRef(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef(null);

  /**
   * Build WebSocket URL with auth token
   * @returns {string} Full WebSocket URL
   */
  const buildUrl = useCallback(() => {
    const token = localStorage.getItem('skilltree_access_token');
    const url = new URL(`${WS_URL}${path}`);
    
    if (token) {
      url.searchParams.set('token', token);
    }
    
    return url.toString();
  }, [path]);

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionState(WS_STATE.CONNECTING);
    
    try {
      const ws = new WebSocket(buildUrl());
      wsRef.current = ws;

      ws.onopen = (event) => {
        setIsConnected(true);
        setConnectionState(WS_STATE.OPEN);
        reconnectCountRef.current = 0;
        
        if (onOpen) {
          onOpen(event);
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
          
          if (onMessage) {
            onMessage(data);
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onerror = (event) => {
        if (onError) {
          onError(event);
        }
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        setConnectionState(WS_STATE.CLOSED);
        
        if (onClose) {
          onClose(event);
        }

        // Auto-reconnect if not a clean close
        if (!event.wasClean && reconnectCountRef.current < reconnectAttempts) {
          reconnectCountRef.current += 1;
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };
    } catch (error) {
      console.error('WebSocket connection error:', error);
      setConnectionState(WS_STATE.CLOSED);
    }
  }, [buildUrl, onOpen, onMessage, onError, onClose, reconnectAttempts, reconnectInterval]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    reconnectCountRef.current = reconnectAttempts; // Prevent auto-reconnect

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setConnectionState(WS_STATE.CLOSED);
  }, [reconnectAttempts]);

  /**
   * Send message through WebSocket
   * @param {Object} data - Data to send
   * @returns {boolean} Whether send was successful
   */
  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
      return true;
    }
    return false;
  }, []);

  /**
   * Send message and wait for response
   * @param {Object} data - Data to send
   * @param {string} responseType - Expected response type
   * @param {number} timeout - Timeout in ms
   * @returns {Promise<Object>} Response data
   */
  const sendAndWait = useCallback((data, responseType, timeout = 30000) => {
    return new Promise((resolve, reject) => {
      const messageId = Date.now().toString();
      const timeoutId = setTimeout(() => {
        reject(new Error('WebSocket message timeout'));
      }, timeout);

      const handleMessage = (message) => {
        if (message.id === messageId || message.type === responseType) {
          clearTimeout(timeoutId);
          setLastMessage((prev) => {
            if (prev?.id === messageId || prev?.type === responseType) {
              return null;
            }
            return prev;
          });
          resolve(message);
        }
      };

      // Temporarily add message handler
      const originalOnMessage = wsRef.current?.onmessage;
      
      send({ ...data, id: messageId });
    });
  }, [send]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    isConnected,
    connectionState,
    lastMessage,
    connect,
    disconnect,
    send,
    sendAndWait,
  };
}

export default useWebSocket;