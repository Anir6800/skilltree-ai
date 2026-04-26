/**
 * SkillTree AI - Match Page
 * Real-time multiplayer race: waiting room, live editor, opponent tracking, winner modal.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import Editor from '@monaco-editor/react';
import {
  Swords, Play, Send, RotateCcw, CheckCircle2, XCircle, AlertCircle,
  Loader2, Clock, Zap, Trophy, Users, Wifi, WifiOff, ChevronLeft,
  Shield, Target, Code2,
} from 'lucide-react';
import api from '../api/api';
import useAuthStore from '../store/authStore';
import { STORAGE_KEYS } from '../constants';
import { cn } from '../utils/cn';

// ─── Constants ────────────────────────────────────────────────────────────────

const MATCH_DURATION_SECONDS = 15 * 60; // 15 minutes
const POLL_INTERVAL_MS = 2000;
const MAX_POLL_ATTEMPTS = 30;
const COUNTDOWN_SECONDS = 3;

const LANGUAGES = [
  { id: 'python',     label: 'Python',     monacoId: 'python'     },
  { id: 'javascript', label: 'JavaScript', monacoId: 'javascript' },
  { id: 'cpp',        label: 'C++',        monacoId: 'cpp'        },
  { id: 'java',       label: 'Java',       monacoId: 'java'       },
  { id: 'go',         label: 'Go',         monacoId: 'go'         },
];

const LANG_COLORS = {
  python:     { bg: 'bg-blue-500/20',   border: 'border-blue-500/40',   text: 'text-blue-400'   },
  javascript: { bg: 'bg-yellow-500/20', border: 'border-yellow-500/40', text: 'text-yellow-400' },
  cpp:        { bg: 'bg-cyan-500/20',   border: 'border-cyan-500/40',   text: 'text-cyan-400'   },
  java:       { bg: 'bg-orange-500/20', border: 'border-orange-500/40', text: 'text-orange-400' },
  go:         { bg: 'bg-teal-500/20',   border: 'border-teal-500/40',   text: 'text-teal-400'   },
};

// ─── Monaco Theme ─────────────────────────────────────────────────────────────

function defineMonacoTheme(monaco) {
  monaco.editor.defineTheme('skilltree-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'keyword',         foreground: '7c6af5', fontStyle: 'bold' },
      { token: 'keyword.control', foreground: 'a78bfa' },
      { token: 'string',          foreground: '3dd68c' },
      { token: 'comment',         foreground: '4b5563', fontStyle: 'italic' },
      { token: 'number',          foreground: 'f59e0b' },
      { token: 'type',            foreground: '38bdf8' },
      { token: 'function',        foreground: 'c084fc' },
      { token: 'variable',        foreground: 'e2e8f0' },
      { token: 'operator',        foreground: 'f43f5e' },
      { token: 'delimiter',       foreground: '94a3b8' },
    ],
    colors: {
      'editor.background':                    '#0a0c10',
      'editor.foreground':                    '#e2e8f0',
      'editor.lineHighlightBackground':       '#ffffff08',
      'editor.selectionBackground':           '#6366f130',
      'editor.inactiveSelectionBackground':   '#6366f118',
      'editorLineNumber.foreground':          '#374151',
      'editorLineNumber.activeForeground':    '#6366f1',
      'editorCursor.foreground':              '#6366f1',
      'editorIndentGuide.background1':        '#1f2937',
      'editorIndentGuide.activeBackground1':  '#374151',
      'editorBracketMatch.background':        '#6366f120',
      'editorBracketMatch.border':            '#6366f1',
      'scrollbarSlider.background':           '#ffffff10',
      'scrollbarSlider.hoverBackground':      '#ffffff20',
      'editorWidget.background':              '#0f172a',
      'editorSuggestWidget.background':       '#0f172a',
      'editorSuggestWidget.border':           '#ffffff10',
      'editorSuggestWidget.selectedBackground': '#6366f120',
    },
  });
}

// ─── Utility ──────────────────────────────────────────────────────────────────

function formatTime(seconds) {
  const m = Math.floor(Math.max(0, seconds) / 60);
  const s = Math.max(0, seconds) % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function useCountUp(target, duration = 1200) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (!target) return;
    let start = null;
    const step = (ts) => {
      if (!start) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      setValue(Math.round(progress * target));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [target, duration]);
  return value;
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function PlayerAvatar({ username, isReady, isYou }) {
  return (
    <div className="flex flex-col items-center gap-2">
      <div className={cn(
        'relative w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-black border-2 transition-all duration-500',
        isReady
          ? 'bg-gradient-to-br from-emerald-500/30 to-emerald-600/30 border-emerald-500/60 shadow-[0_0_24px_rgba(52,211,153,0.4)]'
          : 'bg-gradient-to-br from-primary/20 to-accent/20 border-primary/30'
      )}>
        {(username?.[0] ?? '?').toUpperCase()}
        {isReady && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute -bottom-1.5 -right-1.5 w-6 h-6 rounded-full bg-emerald-500 border-2 border-[#0a0c10] flex items-center justify-center"
          >
            <CheckCircle2 size={12} className="text-white" />
          </motion.div>
        )}
      </div>
      <div className="text-center">
        <p className="text-sm font-black text-white">{username ?? 'Unknown'}</p>
        {isYou && <span className="text-[9px] font-bold uppercase tracking-widest text-primary">You</span>}
        <p className={cn(
          'text-[10px] font-bold uppercase tracking-widest mt-0.5',
          isReady ? 'text-emerald-400' : 'text-slate-500'
        )}>
          {isReady ? 'Ready' : 'Waiting...'}
        </p>
      </div>
    </div>
  );
}

function CountdownOverlay({ count }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md"
    >
      <AnimatePresence mode="wait">
        <motion.div
          key={count}
          initial={{ scale: 2, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.5, opacity: 0 }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
          className="text-center"
        >
          <div className="text-[120px] font-black leading-none premium-gradient-text drop-shadow-[0_0_40px_rgba(99,102,241,0.8)]">
            {count === 0 ? 'GO!' : count}
          </div>
          <p className="text-slate-400 text-lg font-bold mt-4 uppercase tracking-widest">
            {count === 0 ? 'Race started!' : 'Get ready...'}
          </p>
        </motion.div>
      </AnimatePresence>
    </motion.div>
  );
}

function WinnerModal({ winner, isWinner, xpGained, onRematch, onLeave }) {
  const animatedXP = useCountUp(xpGained, 1500);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.85, y: 30 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.85, y: 30 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="glass-panel rounded-3xl p-8 w-full max-w-sm text-center border-primary/20 shadow-[0_0_80px_rgba(99,102,241,0.3)] relative overflow-hidden"
      >
        {/* Background glow */}
        <div className={cn(
          'absolute inset-0 opacity-20 pointer-events-none',
          isWinner
            ? 'bg-gradient-to-br from-amber-500/30 via-transparent to-primary/30'
            : 'bg-gradient-to-br from-slate-500/20 via-transparent to-slate-600/20'
        )} />

        <div className="relative z-10">
          {/* Trophy / Shield icon */}
          <motion.div
            initial={{ scale: 0, rotate: -20 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
            className={cn(
              'w-20 h-20 rounded-3xl flex items-center justify-center mx-auto mb-5 border-2',
              isWinner
                ? 'bg-gradient-to-br from-amber-500/30 to-yellow-500/30 border-amber-500/50 shadow-[0_0_40px_rgba(245,158,11,0.4)]'
                : 'bg-gradient-to-br from-slate-500/20 to-slate-600/20 border-slate-500/30'
            )}
          >
            {isWinner
              ? <Trophy size={36} className="text-amber-400 drop-shadow-[0_0_12px_rgba(245,158,11,0.8)]" />
              : <Shield size={36} className="text-slate-400" />
            }
          </motion.div>

          {/* Result text */}
          <motion.h2
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className={cn(
              'text-3xl font-black mb-1',
              isWinner ? 'premium-gradient-text' : 'text-slate-300'
            )}
          >
            {isWinner ? '🏆 Victory!' : 'Match Over'}
          </motion.h2>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="text-slate-400 text-sm mb-6"
          >
            {isWinner
              ? 'You solved it first!'
              : winner
                ? `${winner} won the match`
                : 'Match ended'
            }
          </motion.p>

          {/* XP gained */}
          {xpGained > 0 && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.5 }}
              className="flex items-center justify-center gap-2 px-5 py-3 rounded-2xl bg-amber-500/10 border border-amber-500/30 mb-6"
            >
              <Zap size={18} className="text-amber-400" fill="currentColor" />
              <span className="text-2xl font-black text-amber-400">+{animatedXP}</span>
              <span className="text-sm font-bold text-amber-400/70">XP</span>
            </motion.div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={onRematch}
              className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl bg-gradient-to-r from-primary/80 to-accent/80 border border-primary/40 text-white font-black text-sm uppercase tracking-wider hover:from-primary hover:to-accent hover:shadow-[0_0_20px_rgba(99,102,241,0.4)] transition-all duration-200"
            >
              <Swords size={14} />
              Rematch
            </button>
            <button
              onClick={onLeave}
              className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl bg-white/5 border border-white/10 text-slate-300 font-black text-sm uppercase tracking-wider hover:bg-white/10 transition-all duration-200"
            >
              <ChevronLeft size={14} />
              Arena
            </button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}

function DisconnectToast({ username, onDismiss }) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 5000);
    return () => clearTimeout(t);
  }, [onDismiss]);

  return (
    <motion.div
      initial={{ opacity: 0, y: -20, x: '-50%' }}
      animate={{ opacity: 1, y: 0, x: '-50%' }}
      exit={{ opacity: 0, y: -20, x: '-50%' }}
      className="fixed top-6 left-1/2 z-50 flex items-center gap-3 px-5 py-3 rounded-2xl bg-red-500/20 border border-red-500/40 text-red-300 text-sm font-bold shadow-[0_0_24px_rgba(239,68,68,0.3)] backdrop-blur-xl"
    >
      <WifiOff size={15} />
      {username ? `${username} disconnected` : 'Opponent disconnected'}
    </motion.div>
  );
}

function SubmittingOverlay() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="absolute inset-0 z-30 flex items-center justify-center bg-black/70 backdrop-blur-sm rounded-2xl"
    >
      <div className="flex flex-col items-center gap-3">
        <Loader2 size={28} className="text-primary animate-spin drop-shadow-[0_0_12px_rgba(99,102,241,0.8)]" />
        <p className="text-sm font-bold text-slate-300">Waiting for result...</p>
      </div>
    </motion.div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function MatchPage() {
  const { matchId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuthStore();

  // ── WebSocket state ──
  const wsRef = useRef(null);
  const [wsConnected, setWsConnected] = useState(false);

  // ── Match state ──
  const [matchState, setMatchState] = useState(null);
  const [matchStatus, setMatchStatus] = useState('loading'); // loading | waiting | countdown | active | finished
  const [participants, setParticipants] = useState([]);
  const [readySet, setReadySet] = useState(new Set());
  const [myReady, setMyReady] = useState(false);
  const [quest, setQuest] = useState(null);

  // ── Countdown ──
  const [countdownValue, setCountdownValue] = useState(COUNTDOWN_SECONDS);
  const countdownRef = useRef(null);

  // ── Race timer ──
  const [timeLeft, setTimeLeft] = useState(MATCH_DURATION_SECONDS);
  const timerRef = useRef(null);

  // ── Editor ──
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const editorRef = useRef(null);

  // ── Submission ──
  const [submitting, setSubmitting] = useState(false);
  const [myScore, setMyScore] = useState({ passed: 0, total: 0 });
  const [opponentScore, setOpponentScore] = useState({ passed: 0, total: 0, username: '' });
  const pollRef = useRef(null);
  const pollAttemptsRef = useRef(0);

  // ── Result / Winner ──
  const [winner, setWinner] = useState(null); // { username, isMe }
  const [xpGained, setXpGained] = useState(0);
  const [showWinner, setShowWinner] = useState(false);

  // ── Disconnect toast ──
  const [disconnectInfo, setDisconnectInfo] = useState(null);

  // ── Error ──
  const [loadError, setLoadError] = useState(null);

  const currentUserId = user?.id;
  const accessToken = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN) || '';

  // Stable refs for values used inside WS callbacks — avoids reconnect on state change
  const questRef = useRef(null);
  const userRef = useRef(user);
  useEffect(() => { userRef.current = user; }, [user]);
  useEffect(() => { questRef.current = quest; }, [quest]);

  // ── Cleanup ──
  const clearPoll = useCallback(() => {
    if (pollRef.current) { clearTimeout(pollRef.current); pollRef.current = null; }
    pollAttemptsRef.current = 0;
  }, []);

  const clearTimer = useCallback(() => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
  }, []);

  const clearCountdown = useCallback(() => {
    if (countdownRef.current) { clearInterval(countdownRef.current); countdownRef.current = null; }
  }, []);

  useEffect(() => () => {
    clearPoll();
    clearTimer();
    clearCountdown();
    if (wsRef.current) wsRef.current.close();
  }, [clearPoll, clearTimer, clearCountdown]);

  // ── Start race timer ──
  const startRaceTimer = useCallback(() => {
    clearTimer();
    timerRef.current = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          clearTimer();
          setMatchStatus('finished');
          setShowWinner(true);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  }, [clearTimer]);

  // ── Start countdown then race ──
  const startCountdown = useCallback(() => {
    setMatchStatus('countdown');
    setCountdownValue(COUNTDOWN_SECONDS);
    let count = COUNTDOWN_SECONDS;
    countdownRef.current = setInterval(() => {
      count -= 1;
      setCountdownValue(count);
      if (count <= 0) {
        clearCountdown();
        setMatchStatus('active');
        startRaceTimer();
      }
    }, 1000);
  }, [clearCountdown, startRaceTimer]);

  // ── Poll submission result ──
  const pollStatus = useCallback((sid, questId) => {
    if (pollAttemptsRef.current >= MAX_POLL_ATTEMPTS) {
      setSubmitting(false);
      clearPoll();
      return;
    }
    pollAttemptsRef.current += 1;
    pollRef.current = setTimeout(async () => {
      try {
        const res = await api.get(`/api/execute/status/${sid}/`);
        const data = res.data;
        if (data.status === 'pending' || data.status === 'running') {
          pollStatus(sid, questId);
          return;
        }
        clearPoll();
        setSubmitting(false);
        const result = data.execution_result || {};
        const tests = result.test_results || [];
        const passed = tests.filter(t => t.status === 'passed').length;
        const total = tests.length;
        const isWinner = data.status === 'passed' || (total > 0 && passed === total);
        setMyScore({ passed, total });
        // Broadcast result via WebSocket
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'submission_result',
            tests_passed: passed,
            tests_total: total,
            is_winner: isWinner,
          }));
        }
        if (isWinner) {
          setWinner({ username: userRef.current?.username, isMe: true });
          setXpGained(questRef.current?.xp_reward ?? 0);
          setShowWinner(true);
          setMatchStatus('finished');
          clearTimer();
        }
      } catch {
        clearPoll();
        setSubmitting(false);
      }
    }, POLL_INTERVAL_MS);
  }, [clearPoll, clearTimer]);

  // ── WebSocket message handler ──
  const handleWsMessage = useCallback((msg) => {
    const data = typeof msg === 'string' ? JSON.parse(msg) : msg;
    const type = data.type;

    if (type === 'connected') {
      const state = data.match_state;
      if (!state) return;
      setMatchState(state);
      setParticipants(state.participants || []);
      setQuest(state.quest || null);
      setCode(state.quest?.starter_code || '');
      if (state.status === 'active') {
        setMatchStatus('active');
        startRaceTimer();
      } else if (state.status === 'finished') {
        setMatchStatus('finished');
        setShowWinner(true);
      } else {
        setMatchStatus('waiting');
      }
      // Identify opponent
      const opp = (state.participants || []).find(p => p.id !== currentUserId);
      if (opp) setOpponentScore(prev => ({ ...prev, username: opp.username }));
    }

    else if (type === 'player_ready') {
      setReadySet(prev => new Set([...prev, data.user_id]));
    }

    else if (type === 'match_started') {
      startCountdown();
    }

    else if (type === 'submission_result') {
      if (data.user_id !== currentUserId) {
        setOpponentScore({ passed: data.tests_passed, total: data.tests_total, username: data.username });
        if (data.is_winner) {
          setWinner({ username: data.username, isMe: false });
          setXpGained(0);
          setShowWinner(true);
          setMatchStatus('finished');
          clearTimer();
        }
      }
    }

    else if (type === 'player_disconnected') {
      setDisconnectInfo({ username: data.username });
      // Auto-end match after disconnect
      setTimeout(() => {
        setMatchStatus('finished');
        setShowWinner(true);
        clearTimer();
      }, 3000);
    }

    else if (type === 'player_surrendered') {
      if (data.user_id !== currentUserId) {
        setWinner({ username: userRef.current?.username, isMe: true });
        setXpGained(Math.floor((questRef.current?.xp_reward ?? 0) / 2));
        setShowWinner(true);
        setMatchStatus('finished');
        clearTimer();
      }
    }
  }, [currentUserId, startCountdown, startRaceTimer, clearTimer]);

  // ── Connect WebSocket ──
  useEffect(() => {
    if (!matchId || !accessToken) {
      setLoadError('Missing match ID or authentication token.');
      return;
    }

    const wsBase = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
    const wsUrl = `${wsBase}/ws/match/${matchId}/?token=${accessToken}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => setWsConnected(true);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWsMessage(data);
      } catch (e) {
        console.error('WS parse error:', e);
      }
    };

    ws.onerror = () => {
      setLoadError('WebSocket connection failed. Please check the server is running.');
    };

    ws.onclose = (event) => {
      setWsConnected(false);
      if (event.code === 4001 || event.code === 4002 || event.code === 4003) {
        setLoadError('Authentication failed. Please log in again.');
      } else if (event.code === 4004) {
        setLoadError('You are not a participant in this match.');
      }
    };

    return () => ws.close();
  }, [matchId, accessToken, handleWsMessage]);

  // ── Actions ──
  const handleReady = () => {
    if (myReady || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    setMyReady(true);
    wsRef.current.send(JSON.stringify({ type: 'ready' }));
  };

  const handleCodeChange = (val) => {
    const v = val ?? '';
    setCode(v);
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'code_update' }));
    }
  };

  const handleSubmit = async () => {
    const currentQuest = questRef.current;
    if (!code.trim() || submitting || matchStatus !== 'active' || !currentQuest) return;
    setSubmitting(true);
    clearPoll();
    pollAttemptsRef.current = 0;
    try {
      const res = await api.post(`/api/quests/${currentQuest.id}/submit/`, { code: code.trim(), language });
      const data = res.data;
      const sid = data.submission_id || data.id;
      if (sid) {
        pollStatus(sid, currentQuest.id);
      } else {
        setSubmitting(false);
      }
    } catch (err) {
      setSubmitting(false);
      console.error('Submit error:', err);
    }
  };

  const handleReset = () => {
    setCode(questRef.current?.starter_code || '');
  };

  const handleEditorMount = (editor, monaco) => {
    editorRef.current = editor;
    defineMonacoTheme(monaco);
    monaco.editor.setTheme('skilltree-dark');
    editor.focus();
  };

  const handleRematch = () => {
    navigate('/arena');
  };

  const handleLeave = () => {
    navigate('/arena');
  };

  const langColor = LANG_COLORS[language] || LANG_COLORS.python;
  const currentLang = LANGUAGES.find(l => l.id === language) || LANGUAGES[0];
  const opponentProgressPct = opponentScore.total > 0
    ? Math.round((opponentScore.passed / opponentScore.total) * 100)
    : 0;
  const myProgressPct = myScore.total > 0
    ? Math.round((myScore.passed / myScore.total) * 100)
    : 0;

  // ── Loading / Error ──
  if (loadError) {
    return (
      <div className="fixed inset-0 bg-[#0a0c10] flex items-center justify-center p-6">
        <div className="fixed inset-0 pointer-events-none">
          <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-purple-600/10 blur-[120px] rounded-full" />
          <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-600/10 blur-[120px] rounded-full" />
        </div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel p-8 rounded-3xl max-w-md w-full text-center relative z-10"
        >
          <AlertCircle size={40} className="text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-black text-white mb-2">Connection Error</h2>
          <p className="text-slate-400 text-sm mb-6">{loadError}</p>
          <button
            onClick={() => navigate('/arena')}
            className="px-6 py-3 rounded-xl bg-primary/20 border border-primary/30 text-primary font-bold hover:bg-primary/30 transition-all duration-200"
          >
            Back to Arena
          </button>
        </motion.div>
      </div>
    );
  }

  if (matchStatus === 'loading') {
    return (
      <div className="fixed inset-0 bg-[#0a0c10] flex items-center justify-center">
        <div className="fixed inset-0 pointer-events-none">
          <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-purple-600/10 blur-[120px] rounded-full" />
          <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-600/10 blur-[120px] rounded-full" />
        </div>
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center gap-4"
        >
          <Loader2 size={32} className="text-primary animate-spin drop-shadow-[0_0_12px_rgba(99,102,241,0.8)]" />
          <p className="text-slate-400 text-sm font-medium">Connecting to match...</p>
        </motion.div>
      </div>
    );
  }

  // ── Waiting Room ──
  if (matchStatus === 'waiting') {
    return (
      <div className="fixed inset-0 bg-[#0a0c10] text-white flex flex-col items-center justify-center p-6">
        <div className="fixed inset-0 pointer-events-none -z-10">
          <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-purple-600/10 blur-[120px] rounded-full" />
          <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-600/10 blur-[120px] rounded-full" />
        </div>

        <AnimatePresence>
          {disconnectInfo && (
            <DisconnectToast
              username={disconnectInfo.username}
              onDismiss={() => setDisconnectInfo(null)}
            />
          )}
        </AnimatePresence>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel rounded-3xl p-8 w-full max-w-lg border-primary/20 shadow-[0_0_60px_rgba(99,102,241,0.15)]"
        >
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-3xl bg-gradient-to-br from-primary/30 to-accent/30 border border-primary/30 flex items-center justify-center mx-auto mb-4 shadow-[0_0_24px_rgba(99,102,241,0.3)]">
              <Swords size={28} className="text-primary drop-shadow-[0_0_8px_rgba(99,102,241,0.8)]" />
            </div>
            <h1 className="text-2xl font-black text-white mb-1">Waiting Room</h1>
            {quest && (
              <p className="text-slate-400 text-sm">
                Quest: <span className="text-primary font-bold">{quest.title}</span>
              </p>
            )}
            <div className="flex items-center justify-center gap-2 mt-2">
              <div className={cn('w-2 h-2 rounded-full', wsConnected ? 'bg-emerald-400 animate-pulse' : 'bg-red-400')} />
              <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">
                {wsConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>

          {/* Players */}
          <div className="flex items-center justify-center gap-8 mb-8">
            {participants.length > 0 ? (
              participants.map(p => (
                <PlayerAvatar
                  key={p.id}
                  username={p.username}
                  isReady={readySet.has(p.id) || (p.id === currentUserId && myReady)}
                  isYou={p.id === currentUserId}
                />
              ))
            ) : (
              <div className="flex items-center gap-8">
                <PlayerAvatar username={user?.username} isReady={myReady} isYou={true} />
                <div className="flex flex-col items-center gap-2">
                  <div className="w-16 h-16 rounded-2xl bg-white/5 border-2 border-dashed border-white/10 flex items-center justify-center">
                    <Users size={22} className="text-slate-600" />
                  </div>
                  <p className="text-xs font-bold text-slate-600">Waiting...</p>
                </div>
              </div>
            )}

            {/* VS divider */}
            {participants.length >= 2 && (
              <div className="absolute text-slate-600 font-black text-lg">VS</div>
            )}
          </div>

          {/* Ready button */}
          <button
            onClick={handleReady}
            disabled={myReady}
            className={cn(
              'w-full flex items-center justify-center gap-2 py-4 rounded-2xl text-sm font-black uppercase tracking-wider transition-all duration-300',
              myReady
                ? 'bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 cursor-default'
                : 'bg-gradient-to-r from-primary to-accent text-white hover:shadow-[0_0_28px_rgba(99,102,241,0.5)] hover:scale-[1.02]'
            )}
          >
            {myReady ? (
              <><CheckCircle2 size={16} /> Ready! Waiting for opponent...</>
            ) : (
              <><Shield size={16} /> I'm Ready</>
            )}
          </button>

          <p className="text-center text-[11px] text-slate-600 mt-4 font-medium">
            Both players must click ready to start the match
          </p>

          <button
            onClick={() => navigate('/arena')}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-white/5 border border-white/10 text-slate-500 text-xs font-bold hover:bg-white/10 hover:text-slate-300 transition-all duration-200 mt-3"
          >
            <ChevronLeft size={13} />
            Leave Match
          </button>
        </motion.div>
      </div>
    );
  }

  // ── Active Race / Finished ──
  return (
    <div className="fixed inset-0 bg-[#0a0c10] text-white flex flex-col overflow-hidden">
      {/* Ambient glows */}
      <div className="fixed inset-0 pointer-events-none -z-10">
        <div className="absolute top-[-10%] right-[-10%] w-[400px] h-[400px] bg-purple-600/8 blur-[100px] rounded-full" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[400px] h-[400px] bg-blue-600/8 blur-[100px] rounded-full" />
      </div>

      {/* Countdown overlay */}
      <AnimatePresence>
        {matchStatus === 'countdown' && (
          <CountdownOverlay count={countdownValue} />
        )}
      </AnimatePresence>

      {/* Disconnect toast */}
      <AnimatePresence>
        {disconnectInfo && (
          <DisconnectToast
            username={disconnectInfo.username}
            onDismiss={() => setDisconnectInfo(null)}
          />
        )}
      </AnimatePresence>

      {/* Winner modal */}
      <AnimatePresence>
        {showWinner && (
          <WinnerModal
            winner={winner?.username}
            isWinner={winner?.isMe ?? false}
            xpGained={xpGained}
            onRematch={handleRematch}
            onLeave={handleLeave}
          />
        )}
      </AnimatePresence>

      {/* ── Top Bar ── */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/5 bg-black/40 backdrop-blur-xl shrink-0 z-20">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/arena')}
            className="p-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all duration-200"
          >
            <ChevronLeft size={15} className="text-slate-400" />
          </button>
          <div className="flex items-center gap-2">
            <Swords size={14} className="text-primary" />
            <span className="text-sm font-black text-white">Match #{matchId}</span>
          </div>
          {quest && (
            <span className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              <Target size={10} />
              {quest.title}
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          {/* Connection indicator */}
          <div className="flex items-center gap-1.5">
            {wsConnected
              ? <Wifi size={13} className="text-emerald-400" />
              : <WifiOff size={13} className="text-red-400" />
            }
            <span className={cn('text-[10px] font-bold uppercase tracking-widest', wsConnected ? 'text-emerald-400' : 'text-red-400')}>
              {wsConnected ? 'Live' : 'Offline'}
            </span>
          </div>

          {/* My score */}
          {myScore.total > 0 && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-primary/10 border border-primary/20">
              <CheckCircle2 size={12} className="text-primary" />
              <span className="text-xs font-black text-primary">{myScore.passed}/{myScore.total}</span>
            </div>
          )}
        </div>
      </div>

      {/* ── Two-pane body ── */}
      <div className="flex flex-1 overflow-hidden">

        {/* ══ LEFT 55% — Editor ══ */}
        <div className="flex flex-col border-r border-white/5 relative" style={{ width: '55%' }}>

          {/* Editor toolbar */}
          <div className="flex items-center gap-2 px-3 py-2 border-b border-white/5 bg-black/20 shrink-0 flex-wrap">
            {/* Language badge */}
            <div className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-bold uppercase tracking-wider',
              langColor.bg, langColor.border, langColor.text
            )}>
              <Code2 size={11} />
              {currentLang.label}
            </div>

            <div className="w-px h-5 bg-white/10" />

            {/* Language selector */}
            <div className="flex items-center gap-1">
              {LANGUAGES.map(lang => (
                <button
                  key={lang.id}
                  onClick={() => setLanguage(lang.id)}
                  className={cn(
                    'px-2.5 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all duration-150',
                    language === lang.id
                      ? cn(LANG_COLORS[lang.id].bg, LANG_COLORS[lang.id].text, LANG_COLORS[lang.id].border, 'border')
                      : 'text-slate-600 hover:text-slate-400 hover:bg-white/5'
                  )}
                >
                  {lang.label}
                </button>
              ))}
            </div>

            <div className="ml-auto flex items-center gap-2">
              {/* Reset */}
              <button
                onClick={handleReset}
                disabled={submitting}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 text-slate-400 text-xs font-bold hover:bg-white/10 hover:text-white transition-all duration-200 disabled:opacity-40"
              >
                <RotateCcw size={11} />
                Reset
              </button>

              {/* Submit */}
              <button
                onClick={handleSubmit}
                disabled={submitting || matchStatus !== 'active' || !code.trim()}
                className={cn(
                  'flex items-center gap-1.5 px-4 py-1.5 rounded-xl text-xs font-black uppercase tracking-wider transition-all duration-200',
                  'bg-gradient-to-r from-primary/80 to-accent/80 border border-primary/40 text-white',
                  'hover:from-primary hover:to-accent hover:shadow-[0_0_16px_rgba(99,102,241,0.4)]',
                  (submitting || matchStatus !== 'active' || !code.trim()) && 'opacity-40 cursor-not-allowed'
                )}
              >
                {submitting ? <Loader2 size={11} className="animate-spin" /> : <Send size={11} />}
                Submit
              </button>
            </div>
          </div>

          {/* Monaco Editor */}
          <div className="flex-1 relative overflow-hidden">
            <Editor
              height="100%"
              language={currentLang.monacoId}
              value={code}
              onChange={handleCodeChange}
              onMount={handleEditorMount}
              theme="skilltree-dark"
              options={{
                fontSize: 13,
                fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", monospace',
                fontLigatures: true,
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                lineNumbers: 'on',
                renderLineHighlight: 'line',
                cursorBlinking: 'smooth',
                cursorSmoothCaretAnimation: 'on',
                smoothScrolling: true,
                padding: { top: 12, bottom: 12 },
                wordWrap: 'on',
                tabSize: 2,
                automaticLayout: true,
              }}
            />

            {/* Submitting overlay */}
            <AnimatePresence>
              {submitting && <SubmittingOverlay />}
            </AnimatePresence>
          </div>
        </div>

        {/* ══ RIGHT 45% — Quest + Timer + Opponent ══ */}
        <div className="flex flex-col overflow-hidden" style={{ width: '45%' }}>

          {/* Quest description — top */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 border-b border-white/5">
            {quest ? (
              <>
                <div className="flex items-center gap-2 mb-3">
                  <Target size={14} className="text-primary" />
                  <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Quest</span>
                </div>
                <h2 className="text-base font-black text-white mb-3">{quest.title}</h2>
                <div className="glass-card rounded-xl p-4">
                  <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
                    {quest.description || 'No description available.'}
                  </p>
                </div>
                <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-amber-500/10 border border-amber-500/20">
                  <Zap size={13} className="text-amber-400" fill="currentColor" />
                  <span className="text-xs font-black text-amber-400">{quest.xp_reward} XP reward</span>
                </div>
              </>
            ) : (
              <div className="flex items-center justify-center h-full">
                <Loader2 size={20} className="text-primary animate-spin" />
              </div>
            )}
          </div>

          {/* Timer + Opponent — bottom */}
          <div className="p-4 space-y-3 shrink-0">
            {/* Match timer */}
            <div className={cn(
              'glass-panel rounded-2xl p-4 flex items-center justify-between border',
              timeLeft <= 60
                ? 'border-red-500/30 bg-red-500/5'
                : timeLeft <= 180
                  ? 'border-amber-500/30 bg-amber-500/5'
                  : 'border-white/10'
            )}>
              <div className="flex items-center gap-2">
                <Clock size={16} className={cn(
                  timeLeft <= 60 ? 'text-red-400' : timeLeft <= 180 ? 'text-amber-400' : 'text-slate-400'
                )} />
                <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Time Left</span>
              </div>
              <span className={cn(
                'text-2xl font-black tabular-nums',
                timeLeft <= 60 ? 'text-red-400' : timeLeft <= 180 ? 'text-amber-400' : 'text-white'
              )}>
                {formatTime(timeLeft)}
              </span>
            </div>

            {/* My progress */}
            {myScore.total > 0 && (
              <div className="glass-card rounded-xl p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Your Progress</span>
                  <span className="text-xs font-black text-primary">{myScore.passed}/{myScore.total} tests</span>
                </div>
                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-primary to-accent rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${myProgressPct}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              </div>
            )}

            {/* Opponent progress */}
            <div className="glass-card rounded-xl p-3">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="w-5 h-5 rounded-full bg-gradient-to-br from-accent/40 to-rose-500/40 border border-accent/30 flex items-center justify-center text-[9px] font-black text-white">
                    {(opponentScore.username?.[0] ?? '?').toUpperCase()}
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">
                    {opponentScore.username || 'Opponent'}
                  </span>
                </div>
                <span className="text-xs font-black text-accent">
                  {opponentScore.passed}/{opponentScore.total || '?'} tests
                </span>
              </div>
              <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-accent to-rose-500 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${opponentProgressPct}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
