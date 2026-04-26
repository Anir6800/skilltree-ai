/**
 * SkillTree AI - Arena Page
 * Multiplayer match lobby: create matches, browse open matches, join by invite code.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Swords, Plus, Users, Zap, Clock, RefreshCw, Copy, Check,
  X, ChevronDown, Loader2, AlertCircle, Shield, Trophy, Target,
} from 'lucide-react';
import api from '../api/api';
import useAuthStore from '../store/authStore';
import BottomNav from '../components/layout/BottomNav';
import { cn } from '../utils/cn';

// ─── Constants ────────────────────────────────────────────────────────────────

const REFRESH_INTERVAL_MS = 10000;

const DIFFICULTY_COLORS = {
  1: 'text-emerald-400',
  2: 'text-emerald-400',
  3: 'text-amber-400',
  4: 'text-orange-400',
  5: 'text-red-400',
};

// ─── Sub-components ───────────────────────────────────────────────────────────

function DifficultyPips({ level }) {
  const filled = Math.min(5, Math.max(1, Math.round(level || 1)));
  return (
    <div className="flex items-center gap-1">
      {[...Array(5)].map((_, i) => (
        <div
          key={i}
          className={cn(
            'w-1.5 h-1.5 rounded-full transition-all duration-300',
            i < filled
              ? 'bg-primary shadow-[0_0_6px_rgba(99,102,241,0.8)]'
              : 'bg-white/10'
          )}
        />
      ))}
    </div>
  );
}

function MatchCard({ match, onJoin, isJoining }) {
  const playerCount = match.participants?.length ?? 1;
  const isFull = playerCount >= 2;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      whileHover={{ y: -3 }}
      transition={{ duration: 0.25 }}
      className="glass-card p-5 rounded-2xl relative overflow-hidden group"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-primary/0 via-primary/0 to-primary/8 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

      <div className="relative z-10">
        {/* Quest title + XP */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 min-w-0 pr-3">
            <div className="flex items-center gap-2 mb-1">
              <Target size={13} className="text-primary shrink-0" />
              <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Quest</span>
            </div>
            <h3 className="text-sm font-black text-white truncate group-hover:text-primary transition-colors duration-300">
              {match.quest?.title ?? 'Unknown Quest'}
            </h3>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            <Zap size={13} className="text-amber-400" fill="currentColor" />
            <span className="text-sm font-black text-amber-400">{match.quest?.xp_reward ?? 0} XP</span>
          </div>
        </div>

        {/* Difficulty */}
        <div className="flex items-center gap-2 mb-4">
          <DifficultyPips level={match.quest?.difficulty_multiplier} />
          <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Difficulty</span>
        </div>

        {/* Footer: players + join */}
        <div className="flex items-center justify-between pt-3 border-t border-white/5">
          {/* Creator avatar + player count */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              {match.participants?.slice(0, 2).map((p, i) => (
                <div
                  key={p.id ?? i}
                  className="w-7 h-7 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white text-[10px] font-black border-2 border-black/40"
                  style={{ marginLeft: i > 0 ? '-8px' : 0, zIndex: 2 - i }}
                >
                  {(p.username?.[0] ?? '?').toUpperCase()}
                </div>
              ))}
            </div>
            <div className="flex items-center gap-1.5">
              <Users size={13} className={isFull ? 'text-red-400' : 'text-emerald-400'} />
              <span className={cn('text-xs font-black', isFull ? 'text-red-400' : 'text-emerald-400')}>
                {playerCount}/2
              </span>
            </div>
          </div>

          {/* Join button */}
          <button
            onClick={() => onJoin(match.id)}
            disabled={isFull || isJoining}
            className={cn(
              'flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-black uppercase tracking-wider transition-all duration-200',
              isFull
                ? 'bg-white/5 border border-white/10 text-slate-600 cursor-not-allowed'
                : 'bg-gradient-to-r from-primary/80 to-accent/80 border border-primary/40 text-white hover:from-primary hover:to-accent hover:shadow-[0_0_16px_rgba(99,102,241,0.4)]',
              isJoining && 'opacity-60 cursor-not-allowed'
            )}
          >
            {isJoining ? <Loader2 size={11} className="animate-spin" /> : <Swords size={11} />}
            {isFull ? 'Full' : 'Join'}
          </button>
        </div>
      </div>
    </motion.div>
  );
}

function CreateMatchModal({ onClose, onCreated }) {
  const [quests, setQuests] = useState([]);
  const [questsLoading, setQuestsLoading] = useState(true);
  const [selectedQuestId, setSelectedQuestId] = useState(null);
  const [questDropdownOpen, setQuestDropdownOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [inviteCode, setInviteCode] = useState(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(null);
  const dropdownRef = useRef(null);

  useEffect(() => {
    api.get('/api/quests/?page_size=50')
      .then(res => {
        const results = res.data?.results ?? res.data ?? [];
        setQuests(Array.isArray(results) ? results : []);
      })
      .catch(() => setError('Failed to load quests.'))
      .finally(() => setQuestsLoading(false));
  }, []);

  useEffect(() => {
    const handler = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setQuestDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const selectedQuest = quests.find(q => q.id === selectedQuestId);

  const handleCreate = async () => {
    if (!selectedQuestId) { setError('Please select a quest.'); return; }
    setCreating(true);
    setError(null);
    try {
      const res = await api.post('/api/matches/', { quest_id: selectedQuestId, max_participants: 2 });
      const data = res.data;
      setInviteCode(data.invite_code ?? `MATCH-${data.id}`);
      onCreated(data.id);
    } catch (err) {
      setError(err.response?.data?.error || err.response?.data?.detail || 'Failed to create match.');
    } finally {
      setCreating(false);
    }
  };

  const handleCopy = () => {
    if (!inviteCode) return;
    navigator.clipboard.writeText(inviteCode).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />

      <motion.div
        initial={{ opacity: 0, scale: 0.92, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.92, y: 20 }}
        transition={{ duration: 0.25 }}
        className="relative z-10 glass-panel rounded-3xl p-6 w-full max-w-md border-white/10 shadow-[0_0_60px_rgba(99,102,241,0.2)]"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-primary/30 to-accent/30 border border-primary/30 flex items-center justify-center">
              <Plus size={18} className="text-primary" />
            </div>
            <div>
              <h2 className="text-lg font-black text-white">Create Match</h2>
              <p className="text-[11px] text-slate-500 font-medium">Challenge a developer worldwide</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all duration-200"
          >
            <X size={15} className="text-slate-400" />
          </button>
        </div>

        {inviteCode ? (
          /* ── Invite code screen ── */
          <div className="space-y-4">
            <div className="glass-card rounded-2xl p-4 text-center border-emerald-500/20">
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center mx-auto mb-3">
                <Shield size={22} className="text-emerald-400" />
              </div>
              <p className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Match Created</p>
              <p className="text-sm text-slate-300 mb-4">Share this invite code with your opponent</p>
              <div className="flex items-center gap-2 bg-black/40 border border-white/10 rounded-xl px-4 py-3">
                <span className="flex-1 font-mono text-sm font-black text-primary tracking-widest">{inviteCode}</span>
                <button
                  onClick={handleCopy}
                  className="p-1.5 rounded-lg bg-primary/20 border border-primary/30 hover:bg-primary/30 transition-all duration-200"
                >
                  {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} className="text-primary" />}
                </button>
              </div>
            </div>
            <p className="text-xs text-slate-500 text-center">Waiting for opponent to join... You'll be redirected automatically.</p>
          </div>
        ) : (
          /* ── Quest selector screen ── */
          <div className="space-y-4">
            <div>
              <label className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2 block">
                Select Quest
              </label>
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setQuestDropdownOpen(v => !v)}
                  disabled={questsLoading}
                  className="w-full flex items-center justify-between px-4 py-3 rounded-xl bg-white/5 border border-white/10 hover:bg-white/8 hover:border-white/20 transition-all duration-200 text-sm"
                >
                  {questsLoading ? (
                    <span className="flex items-center gap-2 text-slate-500">
                      <Loader2 size={13} className="animate-spin" /> Loading quests...
                    </span>
                  ) : selectedQuest ? (
                    <span className="font-bold text-white truncate">{selectedQuest.title}</span>
                  ) : (
                    <span className="text-slate-500">Choose a quest...</span>
                  )}
                  <ChevronDown size={14} className={cn('text-slate-500 transition-transform duration-200 shrink-0 ml-2', questDropdownOpen && 'rotate-180')} />
                </button>

                <AnimatePresence>
                  {questDropdownOpen && quests.length > 0 && (
                    <motion.div
                      initial={{ opacity: 0, y: -6, scale: 0.97 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: -6, scale: 0.97 }}
                      transition={{ duration: 0.15 }}
                      className="absolute top-full left-0 right-0 mt-1.5 z-50 glass-panel rounded-xl overflow-hidden border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.6)] max-h-52 overflow-y-auto"
                    >
                      {quests.map(q => (
                        <button
                          key={q.id}
                          onClick={() => { setSelectedQuestId(q.id); setQuestDropdownOpen(false); }}
                          className={cn(
                            'w-full flex items-center justify-between px-4 py-3 text-sm transition-all duration-150 text-left',
                            selectedQuestId === q.id
                              ? 'bg-primary/20 text-primary border-l-2 border-primary'
                              : 'text-slate-300 hover:bg-white/5 hover:text-white'
                          )}
                        >
                          <span className="font-bold truncate">{q.title}</span>
                          <span className="text-xs text-amber-400 font-black shrink-0 ml-2">{q.xp_reward} XP</span>
                        </button>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2 px-3 py-2.5 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-bold"
              >
                <AlertCircle size={13} />
                {error}
              </motion.div>
            )}

            <button
              onClick={handleCreate}
              disabled={!selectedQuestId || creating}
              className={cn(
                'w-full flex items-center justify-center gap-2 py-3.5 rounded-xl text-sm font-black uppercase tracking-wider transition-all duration-200',
                selectedQuestId && !creating
                  ? 'bg-gradient-to-r from-primary to-accent text-white hover:shadow-[0_0_24px_rgba(99,102,241,0.5)] hover:scale-[1.02]'
                  : 'bg-white/5 border border-white/10 text-slate-600 cursor-not-allowed'
              )}
            >
              {creating ? <Loader2 size={15} className="animate-spin" /> : <Swords size={15} />}
              {creating ? 'Creating...' : 'Create Match'}
            </button>
          </div>
        )}
      </motion.div>
    </motion.div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function ArenaPage() {
  const navigate = useNavigate();
  const { user } = useAuthStore();

  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [joiningMatchId, setJoiningMatchId] = useState(null);
  const [joinError, setJoinError] = useState(null);
  const [createdMatchId, setCreatedMatchId] = useState(null);

  const intervalRef = useRef(null);

  const fetchMatches = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    else setRefreshing(true);
    setError(null);
    try {
      const res = await api.get('/api/matches/?status=waiting');
      const data = res.data;
      const results = Array.isArray(data) ? data : (data?.results ?? []);
      setMatches(results);
    } catch (err) {
      if (!silent) setError(err.response?.data?.detail || 'Failed to load matches.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchMatches();
    intervalRef.current = setInterval(() => fetchMatches(true), REFRESH_INTERVAL_MS);
    return () => clearInterval(intervalRef.current);
  }, [fetchMatches]);

  // Navigate to match once created
  useEffect(() => {
    if (createdMatchId) {
      const timer = setTimeout(() => navigate(`/match/${createdMatchId}`), 1200);
      return () => clearTimeout(timer);
    }
  }, [createdMatchId, navigate]);

  const handleJoin = async (matchId) => {
    setJoiningMatchId(matchId);
    setJoinError(null);
    try {
      await api.post('/api/matches/join/', { invite_code: `MATCH-${matchId}` });
      navigate(`/match/${matchId}`);
    } catch (err) {
      setJoinError(err.response?.data?.error || err.response?.data?.detail || 'Failed to join match.');
      setJoiningMatchId(null);
    }
  };

  const handleMatchCreated = (matchId) => {
    setCreatedMatchId(matchId);
  };

  return (
    <div className="min-h-screen bg-[#0a0c10] text-white pb-32">
      {/* Ambient glows */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
        <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-purple-600/10 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-600/10 blur-[120px] rounded-full" />
        <div className="absolute top-[40%] left-[30%] w-[300px] h-[300px] bg-rose-600/5 blur-[100px] rounded-full" />
      </div>

      <div className="max-w-4xl mx-auto px-4 pt-8 space-y-8">

        {/* ── Banner ── */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel rounded-3xl p-6 border-primary/20 shadow-[0_0_40px_rgba(99,102,241,0.1)] relative overflow-hidden"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-accent/5 pointer-events-none" />
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary/30 to-accent/30 border border-primary/30 flex items-center justify-center shadow-[0_0_20px_rgba(99,102,241,0.3)]">
                  <Swords size={22} className="text-primary drop-shadow-[0_0_8px_rgba(99,102,241,0.8)]" />
                </div>
                <div>
                  <h1 className="text-2xl md:text-3xl font-black tracking-tight text-white">
                    ⚔️ <span className="premium-gradient-text">Arena</span>
                  </h1>
                  <p className="text-slate-400 text-sm font-medium">Challenge developers worldwide</p>
                </div>
              </div>
              <div className="flex items-center gap-4 mt-3">
                <div className="flex items-center gap-1.5">
                  <Trophy size={13} className="text-amber-400" />
                  <span className="text-xs font-bold text-slate-400">Ranked Matches</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Zap size={13} className="text-primary" />
                  <span className="text-xs font-bold text-slate-400">Real-time Race</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Clock size={13} className="text-slate-500" />
                  <span className="text-xs font-bold text-slate-400">15 min limit</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-6 py-3.5 rounded-2xl bg-gradient-to-r from-primary to-accent text-white font-black text-sm uppercase tracking-wider hover:shadow-[0_0_28px_rgba(99,102,241,0.5)] hover:scale-[1.03] transition-all duration-200 shrink-0"
            >
              <Plus size={16} />
              Create Match
            </button>
          </div>
        </motion.div>

        {/* ── Join error toast ── */}
        <AnimatePresence>
          {joinError && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="flex items-center gap-3 px-4 py-3 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm font-bold"
            >
              <AlertCircle size={15} />
              {joinError}
              <button onClick={() => setJoinError(null)} className="ml-auto p-1 hover:bg-red-500/20 rounded-lg transition-colors">
                <X size={13} />
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Open Matches ── */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-black text-white">Open Matches</h2>
              {!loading && (
                <span className="px-2.5 py-1 rounded-full bg-primary/20 border border-primary/30 text-primary text-[10px] font-black uppercase tracking-widest">
                  {matches.length}
                </span>
              )}
            </div>
            <button
              onClick={() => fetchMatches(true)}
              disabled={refreshing}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all duration-200 text-xs font-bold text-slate-400 hover:text-white"
            >
              <RefreshCw size={12} className={cn(refreshing && 'animate-spin')} />
              Refresh
            </button>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="glass-card rounded-2xl p-5 animate-pulse">
                  <div className="h-4 bg-white/5 rounded-lg mb-3 w-3/4" />
                  <div className="h-3 bg-white/5 rounded-lg mb-4 w-1/2" />
                  <div className="h-8 bg-white/5 rounded-xl" />
                </div>
              ))}
            </div>
          ) : error ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="glass-card rounded-2xl p-8 text-center"
            >
              <AlertCircle size={32} className="text-red-400 mx-auto mb-3" />
              <p className="text-slate-400 text-sm mb-4">{error}</p>
              <button
                onClick={() => fetchMatches()}
                className="px-5 py-2.5 rounded-xl bg-primary/20 border border-primary/30 text-primary text-sm font-bold hover:bg-primary/30 transition-all duration-200"
              >
                Retry
              </button>
            </motion.div>
          ) : matches.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card rounded-2xl p-10 text-center"
            >
              <div className="w-16 h-16 rounded-3xl bg-gradient-to-br from-primary/20 to-accent/20 border border-primary/20 flex items-center justify-center mx-auto mb-4">
                <Swords size={28} className="text-primary/60" />
              </div>
              <h3 className="text-lg font-black text-white mb-2">No Open Matches</h3>
              <p className="text-slate-500 text-sm mb-6">Be the first to create a match and challenge the world.</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-6 py-3 rounded-xl bg-gradient-to-r from-primary/80 to-accent/80 text-white font-black text-sm uppercase tracking-wider hover:from-primary hover:to-accent transition-all duration-200"
              >
                Create First Match
              </button>
            </motion.div>
          ) : (
            <motion.div
              layout
              className="grid grid-cols-1 md:grid-cols-2 gap-4"
            >
              <AnimatePresence mode="popLayout">
                {matches.map(match => (
                  <MatchCard
                    key={match.id}
                    match={match}
                    onJoin={handleJoin}
                    isJoining={joiningMatchId === match.id}
                  />
                ))}
              </AnimatePresence>
            </motion.div>
          )}
        </div>
      </div>

      {/* ── Create Match Modal ── */}
      <AnimatePresence>
        {showCreateModal && (
          <CreateMatchModal
            onClose={() => setShowCreateModal(false)}
            onCreated={handleMatchCreated}
          />
        )}
      </AnimatePresence>

      <BottomNav />
    </div>
  );
}
