/**
 * SkillTree AI - WebSocket Hook
 * Custom hook for WebSocket connections with controlled reconnect.
 *
 * FIX: Previous version had an infinite reconnect loop caused by:
 *   1. `connect` was a useCallback that depended on `onOpen/onMessage/…`
 *      callbacks.  If those were inline functions (new reference each render),
 *      `connect` changed every render → useEffect re-ran → new WebSocket
 *      opened before the old one closed → infinite loop.
 *   2. The storage key used to read the JWT token was wrong
 *      ('skilltree_access_token' vs the actual key 'auth_access').
 *
 * Fixes applied:
 *   - Callbacks are stored in refs so `connect` never changes identity.
 *   - Storage key is read from STORAGE_KEYS constant.
 *   - Reconnect is capped at `reconnectAttempts` with exponential back-off.
 *   - `disconnect()` sets a flag that prevents any further auto-reconnect.
 * @module hooks/useWebSocket
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { WS_URL, STORAGE_KEYS } from '../constants';

/** @readonly @enum {string} */
const WS_STATE = {
  CONNECTING: 'connecting',
  OPEN: 'open',
  CLOSING: 'closing',
  CLOSED: 'closed',
};

/**
 * @param {string} path - WebSocket path, e.g. '/ws/match/123/'
 * @param {Object} [options]
 * @param {function} [options.onOpen]
 * @param {function} [options.onMessage]
 * @param {function} [options.onError]
 * @param {function} [options.onClose]
 * @param {boolean}  [options.autoConnect=true]
 * @param {number}   [options.reconnectAttempts=5]   Max reconnect attempts
 * @param {number}   [options.reconnectInterval=3000] Base interval ms (doubles each attempt)
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
  // Intentional-close flag — prevents auto-reconnect after disconnect()
  const intentionalCloseRef = useRef(false);

  // Store callbacks in refs so `connect` never needs to change identity
  const onOpenRef = useRef(onOpen);
  const onMessageRef = useRef(onMessage);
  const onErrorRef = useRef(onError);
  const onCloseRef = useRef(onClose);
  useEffect(() => { onOpenRef.current = onOpen; }, [onOpen]);
  useEffect(() => { onMessageRef.current = onMessage; }, [onMessage]);
  useEffect(() => { onErrorRef.current = onError; }, [onError]);
  useEffect(() => { onCloseRef.current = onClose; }, [onClose]);

  // `path` is the only real dependency of `connect`
  const pathRef = useRef(path);
  useEffect(() => { pathRef.current = path; }, [path]);

  const buildUrl = useCallback(() => {
    // Use the correct storage key that authStore writes to
    const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN) || '';
    const base = WS_URL || `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`;
    const url = new URL(`${base}${pathRef.current}`);
    if (token) url.searchParams.set('token', token);
    return url.toString();
  }, []); // stable — reads from refs/localStorage at call time

  const connect = useCallback(() => {
    // Don't open a second socket if one is already open/connecting
    if (
      wsRef.current &&
      (wsRef.current.readyState === WebSocket.OPEN ||
        wsRef.current.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    intentionalCloseRef.current = false;
    setConnectionState(WS_STATE.CONNECTING);

    try {
      const ws = new WebSocket(buildUrl());
      wsRef.current = ws;

      ws.onopen = (event) => {
        setIsConnected(true);
        setConnectionState(WS_STATE.OPEN);
        reconnectCountRef.current = 0;
        onOpenRef.current?.(event);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
          onMessageRef.current?.(data);
        } catch (e) {
          console.error('[useWebSocket] Failed to parse message:', e);
        }
      };

      ws.onerror = (event) => {
        onErrorRef.current?.(event);
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        setConnectionState(WS_STATE.CLOSED);
        onCloseRef.current?.(event);

        // Do NOT reconnect if:
        //   - disconnect() was called explicitly
        //   - close was clean (code 1000/1001)
        //   - auth error codes (4001-4004)
        //   - max attempts reached
        const authError = event.code >= 4001 && event.code <= 4004;
        const cleanClose = event.code === 1000 || event.code === 1001;

        if (
          !intentionalCloseRef.current &&
          !cleanClose &&
          !authError &&
          reconnectCountRef.current < reconnectAttempts
        ) {
          reconnectCountRef.current += 1;
          // Exponential back-off: 3s, 6s, 12s, 24s, 48s
          const delay = reconnectInterval * Math.pow(2, reconnectCountRef.current - 1);
          reconnectTimeoutRef.current = setTimeout(connect, delay);
        }
      };
    } catch (error) {
      console.error('[useWebSocket] Connection error:', error);
      setConnectionState(WS_STATE.CLOSED);
    }
  }, [buildUrl, reconnectAttempts, reconnectInterval]); // stable deps only

  const disconnect = useCallback(() => {
    intentionalCloseRef.current = true;

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000);
      wsRef.current = null;
    }

    setIsConnected(false);
    setConnectionState(WS_STATE.CLOSED);
  }, []);

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
      return true;
    }
    return false;
  }, []);

  // Auto-connect once on mount; disconnect on unmount
  useEffect(() => {
    if (autoConnect) connect();
    return () => disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // intentionally empty — connect/disconnect are stable

  return {
    isConnected,
    connectionState,
    lastMessage,
    connect,
    disconnect,
    send,
  };
}

export default useWebSocket;
