import { create } from 'zustand';

/**
 * Badge notification queued for playback
 */
export interface QueuedBadgeNotification {
  id: string;
  badge_slug: string;
  badge_name: string;
  badge_icon: string;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  description: string;
  timestamp: number;
}

/**
 * UI Store State and Actions
 * Manages global UI state including focus mode and badge notifications
 */
interface UIState {
  // Focus Mode State
  focusMode: boolean;
  toggleFocusMode: () => void;

  // Pomodoro Timer State
  pomodoroActive: boolean;
  pomodoroTimeRemaining: number;
  setPomodoroActive: (active: boolean) => void;
  setPomodoroTimeRemaining: (time: number) => void;
  resetPomodoro: () => void;

  // Badge Notification Queue
  badgeQueue: QueuedBadgeNotification[];
  queueBadgeNotification: (badge: QueuedBadgeNotification) => void;
  dequeueBadgeNotification: () => QueuedBadgeNotification | undefined;
  clearBadgeQueue: () => void;
  getBadgeQueueLength: () => number;
}

/**
 * Zustand UI Store
 * Handles focus mode, pomodoro timer, and badge notification queue
 * Persists focus mode to localStorage
 */
const useUIStore = create<UIState>((set, get) => ({
  // Focus Mode
  focusMode: (() => {
    try {
      const stored = localStorage.getItem('ui_focusMode');
      return stored ? JSON.parse(stored) : false;
    } catch {
      return false;
    }
  })(),

  toggleFocusMode: () => {
    set((state) => {
      const newFocusMode = !state.focusMode;
      localStorage.setItem('ui_focusMode', JSON.stringify(newFocusMode));

      // Apply focus mode class to body
      if (newFocusMode) {
        document.body.classList.add('focus-mode');
      } else {
        document.body.classList.remove('focus-mode');
      }

      return { focusMode: newFocusMode };
    });
  },

  // Pomodoro Timer
  pomodoroActive: false,
  pomodoroTimeRemaining: 25 * 60, // 25 minutes in seconds

  setPomodoroActive: (active) => {
    set({ pomodoroActive: active });
  },

  setPomodoroTimeRemaining: (time) => {
    set({ pomodoroTimeRemaining: time });
  },

  resetPomodoro: () => {
    set({
      pomodoroActive: false,
      pomodoroTimeRemaining: 25 * 60,
    });
  },

  // Badge Notification Queue
  badgeQueue: [],

  queueBadgeNotification: (badge) => {
    set((state) => ({
      badgeQueue: [...state.badgeQueue, badge],
    }));
  },

  dequeueBadgeNotification: () => {
    let dequeued: QueuedBadgeNotification | undefined;
    set((state) => {
      if (state.badgeQueue.length === 0) return state;
      [dequeued, ...state.badgeQueue] = state.badgeQueue;
      return { badgeQueue: state.badgeQueue };
    });
    return dequeued;
  },

  clearBadgeQueue: () => {
    set({ badgeQueue: [] });
  },

  getBadgeQueueLength: () => {
    return get().badgeQueue.length;
  },
}));

// Initialize focus mode on app load
if (typeof window !== 'undefined') {
  try {
    const stored = localStorage.getItem('ui_focusMode');
    if (stored && JSON.parse(stored)) {
      document.body.classList.add('focus-mode');
    }
  } catch {
    // Silently fail
  }
}

export default useUIStore;
