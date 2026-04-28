/**
 * SkillTree AI - useGroupChat Hook
 * Manages WebSocket connection for real-time group chat.
 *
 * FIX: Previous version used process.env.REACT_APP_WS_URL (CRA convention)
 * which is undefined in Vite.  Also had no reconnect guard — if groupId
 * changed rapidly the old socket was never closed before a new one opened.
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { STORAGE_KEYS } from '../constants';

// Vite exposes env vars as import.meta.env.VITE_*
const WS_BASE_URL =
  import.meta.env.VITE_WS_URL ||
  `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`;

export function useGroupChat(groupId) {
  const wsRef = useRef(null);
  const [messages, setMessages] = useState([]);
  const [typingUsers, setTypingUsers] = useState(new Set());
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const typingTimeouts = useRef({});

  const handleMessage = useCallback((data) => {
    const { type } = data;

    if (type === 'message') {
      setMessages((prev) => [
        ...prev,
        {
          id: data.id,
          sender_id: data.sender_id,
          sender_username: data.sender_username,
          sender_avatar: data.sender_avatar,
          text: data.text,
          sent_at: data.sent_at,
          is_system: false,
        },
      ]);
    } else if (type === 'typing') {
      setTypingUsers((prev) => new Set([...prev, data.user_id]));

      if (typingTimeouts.current[data.user_id]) {
        clearTimeout(typingTimeouts.current[data.user_id]);
      }

      typingTimeouts.current[data.user_id] = setTimeout(() => {
        setTypingUsers((prev) => {
          const updated = new Set(prev);
          updated.delete(data.user_id);
          return updated;
        });
        delete typingTimeouts.current[data.user_id];
      }, 3000);
    } else if (type === 'system') {
      setMessages((prev) => [
        ...prev,
        {
          id: `system_${Date.now()}`,
          sender_id: data.user_id,
          sender_username: data.username,
          text: data.message,
          sent_at: new Date().toISOString(),
          is_system: true,
          event: data.event,
          skill_title: data.skill_title,
        },
      ]);
    } else if (type === 'error') {
      setError(data.message);
    }
  }, []); // no deps — only uses setters which are stable

  const sendMessage = useCallback((text) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setError('Not connected');
      return;
    }
    wsRef.current.send(JSON.stringify({ type: 'message', text }));
  }, []);

  const sendTyping = useCallback((username) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ type: 'typing', username }));
  }, []);

  useEffect(() => {
    if (!groupId) return;

    // Close any existing socket before opening a new one
    if (wsRef.current) {
      wsRef.current.close(1000);
      wsRef.current = null;
    }

    const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN) || '';
    const wsUrl = `${WS_BASE_URL}/ws/group/${groupId}/?token=${encodeURIComponent(token)}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleMessage(data);
      } catch (err) {
        console.error('[useGroupChat] Failed to parse message:', err);
      }
    };

    ws.onerror = () => {
      setError('Connection error');
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    return () => {
      ws.close(1000);
      Object.values(typingTimeouts.current).forEach(clearTimeout);
    };
  }, [groupId, handleMessage]);

  return {
    messages,
    typingUsers,
    isConnected,
    error,
    sendMessage,
    sendTyping,
    setMessages,
  };
}
