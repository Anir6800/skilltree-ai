/**
 * SkillTree AI - Pomodoro Timer
 * 25-minute countdown timer with pause/reset buttons
 * Appears bottom-right when focus mode is active
 * Plays gentle chime on completion
 */

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Pause, RotateCcw } from 'lucide-react';
import useUIStore from '../store/uiStore';
import './PomodoroTimer.css';

const PomodoroTimer = () => {
  const {
    focusMode,
    pomodoroActive,
    pomodoroTimeRemaining,
    setPomodoroActive,
    setPomodoroTimeRemaining,
    resetPomodoro,
  } = useUIStore();

  const [showBreakNotification, setShowBreakNotification] = useState(false);
  const audioContextRef = useRef(null);

  // Timer interval
  useEffect(() => {
    if (!focusMode || !pomodoroActive || pomodoroTimeRemaining <= 0) {
      return;
    }

    const interval = setInterval(() => {
      setPomodoroTimeRemaining(pomodoroTimeRemaining - 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [focusMode, pomodoroActive, pomodoroTimeRemaining, setPomodoroTimeRemaining]);

  // Handle timer completion
  useEffect(() => {
    if (pomodoroTimeRemaining === 0 && pomodoroActive) {
      setPomodoroActive(false);
      playChime();
      setShowBreakNotification(true);
      setTimeout(() => setShowBreakNotification(false), 4000);
    }
  }, [pomodoroTimeRemaining, pomodoroActive, setPomodoroActive]);

  // Play gentle chime using Web Audio API
  const playChime = () => {
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      audioContextRef.current = audioContext;

      const now = audioContext.currentTime;
      const notes = [523.25, 659.25, 783.99]; // C5, E5, G5

      notes.forEach((freq, index) => {
        const osc = audioContext.createOscillator();
        const gain = audioContext.createGain();

        osc.connect(gain);
        gain.connect(audioContext.destination);

        osc.frequency.value = freq;
        osc.type = 'sine';

        gain.gain.setValueAtTime(0.3, now + index * 0.1);
        gain.gain.exponentialRampToValueAtTime(0.01, now + index * 0.1 + 0.3);

        osc.start(now + index * 0.1);
        osc.stop(now + index * 0.1 + 0.3);
      });
    } catch (error) {
      console.error('Failed to play chime:', error);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handlePlayPause = () => {
    setPomodoroActive(!pomodoroActive);
  };

  const handleReset = () => {
    resetPomodoro();
  };

  if (!focusMode) {
    return null;
  }

  return (
    <>
      {/* Pomodoro Timer */}
      <motion.div
        className="pomodoro-timer-container"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 20 }}
        transition={{ duration: 0.3 }}
      >
        <div className="pomodoro-timer-card">
          <div className="pomodoro-display">
            <div className="pomodoro-time">{formatTime(pomodoroTimeRemaining)}</div>
            <div className="pomodoro-label">Focus Time</div>
          </div>

          <div className="pomodoro-controls">
            <motion.button
              className="pomodoro-btn play-pause"
              onClick={handlePlayPause}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              aria-label={pomodoroActive ? 'Pause' : 'Play'}
            >
              {pomodoroActive ? (
                <Pause size={16} />
              ) : (
                <Play size={16} />
              )}
            </motion.button>

            <motion.button
              className="pomodoro-btn reset"
              onClick={handleReset}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              aria-label="Reset"
            >
              <RotateCcw size={16} />
            </motion.button>
          </div>

          {/* Progress ring */}
          <svg className="pomodoro-progress-ring" viewBox="0 0 100 100">
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke="rgba(255, 255, 255, 0.1)"
              strokeWidth="2"
            />
            <motion.circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke="url(#progressGradient)"
              strokeWidth="2"
              strokeDasharray={`${2 * Math.PI * 45}`}
              strokeDashoffset={`${2 * Math.PI * 45 * (1 - pomodoroTimeRemaining / (25 * 60))}`}
              strokeLinecap="round"
              style={{ transform: 'rotate(-90deg)', transformOrigin: '50% 50%' }}
            />
            <defs>
              <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#6366f1" />
                <stop offset="100%" stopColor="#a855f7" />
              </linearGradient>
            </defs>
          </svg>
        </div>
      </motion.div>

      {/* Break Notification */}
      <AnimatePresence>
        {showBreakNotification && (
          <motion.div
            className="break-notification"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            transition={{ duration: 0.3 }}
          >
            <div className="break-notification-content">
              <span className="break-emoji">☕</span>
              <div>
                <div className="break-title">Break Time!</div>
                <div className="break-subtitle">You've completed a focus session</div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default PomodoroTimer;
