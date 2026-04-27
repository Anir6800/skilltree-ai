/**
 * SkillTree AI - Leaderboard Page
 * Redis-backed global/weekly/friends rankings with animated podium and rank-change tracking.
 */

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Trophy, Flame, Zap, Users, Globe, Calendar, TrendingUp,
  TrendingDown, Minus, ChevronDown, Loader2, AlertCircle,
  RefreshCw, Crown,
} from 'lucide-react';
import api from '../api/api';
import useAuthStore from '../store/authStore';
import BottomNav from '../components/layout/BottomNav';
import MainLayout from '../components/layout/MainLayout';
import { cn } from '../utils/cn';

// ─── Constants ────────────────────────────────────────────────────────────────

const SCOPES = [
  { id: 'global',  label: 'Global',  icon: Globe    },
  { id: 'weekly',  label: 'Weekly',  icon: Calendar },
  { id: 'friends', label: 'Friends', icon: Users    },
];

const PODIUM_MEDALS = ['🥇', '🥈', '🥉'];
const PODIUM_HEIGHTS = ['h-28', 'h-20', 'h-16'];
const PODIUM_COLORS = [
  { ring: 'ring-amber-400/60',   bg: 'from-amber-500/20 to-yellow-500/20',  text: 'text-amber-400',  glow: 'shadow-[0_0_24px_rgba(245,158,11,0.4)]'  },
  { ring: 'ring-slate-300/60',   bg: 'from-slate-400/20 to-slate-300/20',   text: 'text-slate-300',  glow: 'shadow-[0_0_16px_rgba(203,213,225,0.3)]'  },
  { ring: 'ring-orange-400/60',  bg: 'from-orange-500/20 to-amber-600/20',  text: 'text-orange-400', glow: 'shadow-[0_0_16px_rgba(251,146,60,0.3)]'   },
];

// ─── Sub-components ───────────────────────────────────────────────────────────

function SkeletonRow({ index }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: index * 0.04 }}
      className="flex items-center gap-4 px-4 py-3 rounded-2xl bg-white/3 animate-pulse"
    >
      <div className="w-8 h-8 rounded-full bg-white/5 shrink-0" />
      <div className="w-10 h-10 rounded-xl bg-white/5 shrink-0" />
      <div className="flex-1 space-y-1.5">
        <div className="h-3 bg-white/5 rounded-lg w-1/3" />
        <div className="h-2.5 bg-white/5 rounded-lg w-1/5" />
      </div>
      <div className="h-4 bg-white/5 rounded-lg w-16" />
      <div className="h-4 bg-white/5 rounded-lg w-12" />
    </motion.div>
  );
}

function RankChange({ change }) {
  if (change === null || change === undefined) {
    return <span className="text-slate-600 text-xs font-bold">—</span>;
  }
  if (change === 0) {
    return (
      <span className="flex items-center gap-0.5 text-slate-500 text-xs font-bold">
        <Minus size={11} />0
      </span>
    );
  }
  if (change > 0) {
    return (
      <motion.span
        key={`up-${change}`}
        initial={{ y: 6, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex items-center gap-0.5 text-emerald-400 text-xs font-black"
      >
        <TrendingUp size={11} />+{change}
      </motion.span>
    );
  }
  return (
    <motion.span
      key={`down-${change}`}
      initial={{ y: -6, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="flex items-center gap-0.5 text-red-400 text-xs font-black"
    >
      <TrendingDown size={11} />{change}
    </motion.span>
  );
}

function RankBadge({ rank }) {
  if (rank === 1) return <span className="text-lg leading-none">🥇</span>;
  if (rank === 2) return <span className="text-lg leading-none">🥈</span>;
  if (rank === 3) return <span className="text-lg leading-none">🥉</span>;
  return (
    <span className="text-xs font-black text-slate-400 tabular-nums w-6 text-center">
      #{rank}
    </span>
  );
}

function PodiumCard({ entry, position, delay }) {
  const colors = PODIUM_COLORS[position];
  const height = PODIUM_HEIGHTS[position];
  const medal = PODIUM_MEDALS[position];
  const order = position === 0 ? 'order-2' : position === 1 ? 'order-1' : 'order-3';

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5, ease: 'easeOut' }}
      className={cn('flex flex-col items-center gap-2', order)}
    >
      {/* Crown for #1 */}
      {position === 0 && (
        <motion.div
          initial={{ scale: 0, rotate: -20 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ delay: delay + 0.3, type: 'spring', stiffness: 200 }}
        >
          <Crown size={22} className="text-amber-400 drop-shadow-[0_0_8px_rgba(245,158,11,0.8)]" />
        </motion.div>
      )}

      {/* Avatar */}
      <div className={cn(
        'w-14 h-14 rounded-2xl ring-2 flex items-center justify-center text-xl font-black text-white',
        `bg-gradient-to-br ${colors.bg}`,
        colors.ring,
        colors.glow,
      )}>
        {entry.avatar_url
          ? <img src={entry.avatar_url} alt={entry.username} className="w-full h-full object-cover rounded-2xl" />
          : (entry.username?.[0] ?? '?').toUpperCase()
        }
      </div>

      {/* Medal + name */}
      <div className="text-center">
        <div className="text-base leading-none mb-0.5">{medal}</div>
        <p className={cn('text-xs font-black truncate max-w-[80px]', colors.text)}>{entry.username}</p>
        <p className="text-[10px] font-bold text-slate-500">{entry.xp?.toLocaleString()} XP</p>
      </div>

      {/* Podium bar */}
      <motion.div
        initial={{ height: 0 }}
        animate={{ height: 'auto' }}
        transition={{ delay: delay + 0.2, duration: 0.6, ease: 'easeOut' }}
        className={cn(
          'w-20 rounded-t-xl border border-white/10 flex items-center justify-center',
          `bg-gradient-to-t ${colors.bg}`,
          height,
        )}
      >
        <span className={cn('text-2xl font-black', colors.text)}>{position + 1}</span>
      </motion.div>
    </motion.div>
  );
}

function LeaderboardRow({ entry, isCurrentUser, index }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.03, duration: 0.25 }}
      className={cn(
        'flex items-center gap-3 px-4 py-3 rounded-2xl transition-all duration-200 group',
        isCurrentUser
          ? 'bg-primary/10 border border-primary/30 shadow-[0_0_16px_rgba(99,102,241,0.15)]'
          : 'hover:bg-white/5 border border-transparent hover:border-white/5',
      )}
    >
      {/* Rank */}
      <div className="w-8 flex items-center justify-center shrink-0">
        <RankBadge rank={entry.rank} />
      </div>

      {/* Avatar */}
      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 border border-white/10 flex items-center justify-center text-sm font-black text-white shrink-0 overflow-hidden">
        {entry.avatar_url
          ? <img src={entry.avatar_url} alt={entry.username} className="w-full h-full object-cover" />
          : (entry.username?.[0] ?? '?').toUpperCase()
        }
      </div>

      {/* Username + level */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={cn(
            'text-sm font-black truncate',
            isCurrentUser ? 'text-primary' : 'text-white group-hover:text-primary transition-colors duration-200'
          )}>
            {entry.username}
          </span>
          {isCurrentUser && (
            <span className="px-1.5 py-0.5 rounded-md bg-primary/30 border border-primary/40 text-[9px] font-black text-primary uppercase tracking-widest shrink-0">
              You
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-[10px] font-bold text-slate-500">Lv.{entry.level}</span>
          {entry.streak_days > 0 && (
            <span className="flex items-center gap-0.5 text-[10px] font-bold text-orange-400">
              <Flame size={9} />
              {entry.streak_days}d
            </span>
          )}
        </div>
      </div>

      {/* XP */}
      <div className="flex items-center gap-1 shrink-0">
        <Zap size={12} className="text-amber-400" fill="currentColor" />
        <span className="text-sm font-black text-amber-400 tabular-nums">
          {entry.xp?.toLocaleString()}
        </span>
      </div>

      {/* Rank change */}
      <div className="w-12 flex justify-end shrink-0">
        <RankChange change={entry.rank_change} />
      </div>
    </motion.div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function LeaderboardPage() {
  const { user } = useAuthStore();

  const [scope, setScope] = useState('global');
  const [entries, setEntries] = useState([]);
  const [myRank, setMyRank] = useState(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const LIMIT = 50;
  const hasMore = entries.length < total;

  const fetchRankings = useCallback(async (newScope, newPage, append = false) => {
    if (!append) setLoading(true);
    else setLoadingMore(true);
    setError(null);

    try {
      const res = await api.get('/api/leaderboard/', {
        params: { scope: newScope, page: newPage, limit: LIMIT },
      });
      const data = res.data;
      const results = data.results ?? [];

      setEntries(prev => append ? [...prev, ...results] : results);
      setTotal(data.total ?? results.length);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load leaderboard.');
    } finally {
      setLoading(false);
      setLoadingMore(false);
      setRefreshing(false);
    }
  }, []);

  const fetchMyRank = useCallback(async () => {
    try {
      const res = await api.get('/api/leaderboard/my-rank/');
      setMyRank(res.data);
    } catch {
      setMyRank(null);
    }
  }, []);

  // Initial load + scope change
  useEffect(() => {
    setPage(1);
    setEntries([]);
    fetchRankings(scope, 1, false);
  }, [scope, fetchRankings]);

  // My rank on mount
  useEffect(() => {
    fetchMyRank();
  }, [fetchMyRank]);

  const handleScopeChange = (newScope) => {
    if (newScope === scope) return;
    setScope(newScope);
  };

  const handleLoadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    fetchRankings(scope, nextPage, true);
  };

  const handleRefresh = () => {
    setRefreshing(true);
    setPage(1);
    fetchRankings(scope, 1, false);
    fetchMyRank();
  };

  const top3 = entries.slice(0, 3);
  const tableEntries = entries.slice(3);

  return (
    <MainLayout>
      <div className="min-h-screen bg-[#0a0c10] text-white pb-32">
        {/* Ambient glows */}
        <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
          <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-purple-600/10 blur-[120px] rounded-full" />
          <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-600/10 blur-[120px] rounded-full" />
          <div className="absolute top-[30%] left-[20%] w-[300px] h-[300px] bg-amber-600/5 blur-[100px] rounded-full" />
        </div>

        <div className="max-w-3xl mx-auto px-4 pt-8 space-y-6">

          {/* ── Header ── */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center justify-between"
          >
            <div>
              <h1 className="text-3xl font-black tracking-tight text-white flex items-center gap-3">
                <Trophy size={28} className="text-amber-400 drop-shadow-[0_0_12px_rgba(245,158,11,0.6)]" />
                <span className="premium-gradient-text">Leaderboard</span>
              </h1>
              <p className="text-slate-400 text-sm font-medium mt-1">
                {total > 0 ? `${total.toLocaleString()} ranked developers` : 'See how you rank worldwide'}
              </p>
            </div>
            <button
              onClick={handleRefresh}
              disabled={refreshing || loading}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all duration-200 text-xs font-bold text-slate-400 hover:text-white disabled:opacity-40"
            >
              <RefreshCw size={12} className={cn(refreshing && 'animate-spin')} />
              Refresh
            </button>
          </motion.div>

          {/* ── My Rank Card ── */}
          <AnimatePresence>
            {myRank && myRank.rank && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="glass-panel rounded-2xl p-4 border-primary/20 shadow-[0_0_24px_rgba(99,102,241,0.1)] relative overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-accent/5 pointer-events-none" />
                <div className="relative z-10 flex items-center justify-between flex-wrap gap-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary/30 to-accent/30 border border-primary/30 flex items-center justify-center text-lg font-black text-white shadow-[0_0_16px_rgba(99,102,241,0.3)]">
                      {(user?.username?.[0] ?? '?').toUpperCase()}
                    </div>
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Your Rank</p>
                      <p className="text-2xl font-black text-primary">#{myRank.rank}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-6">
                    <div className="text-center">
                      <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-0.5">Score</p>
                      <p className="text-sm font-black text-white">{Math.round(myRank.score).toLocaleString()}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-0.5">Percentile</p>
                      <p className="text-sm font-black text-emerald-400">Top {100 - myRank.percentile}%</p>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* ── Scope Tabs ── */}
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="flex items-center gap-2 p-1 glass-panel rounded-2xl"
          >
            {SCOPES.map(s => {
              const Icon = s.icon;
              const isActive = scope === s.id;
              return (
                <button
                  key={s.id}
                  onClick={() => handleScopeChange(s.id)}
                  className={cn(
                    'flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-black uppercase tracking-wider transition-all duration-200',
                    isActive
                      ? 'bg-primary/20 border border-primary/40 text-primary shadow-[0_0_12px_rgba(99,102,241,0.2)]'
                      : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
                  )}
                >
                  <Icon size={13} />
                  {s.label}
                </button>
              );
            })}
          </motion.div>

          {/* ── Content ── */}
          {loading ? (
            <div className="space-y-3">
              {/* Podium skeleton */}
              <div className="glass-card rounded-3xl p-6 flex items-end justify-center gap-4 h-52 animate-pulse">
                {[1, 0, 2].map(i => (
                  <div key={i} className="flex flex-col items-center gap-2">
                    <div className="w-12 h-12 rounded-2xl bg-white/5" />
                    <div className={cn('w-20 rounded-t-xl bg-white/5', PODIUM_HEIGHTS[i])} />
                  </div>
                ))}
              </div>
              {/* Row skeletons */}
              <div className="glass-card rounded-3xl p-4 space-y-2">
                {[...Array(8)].map((_, i) => <SkeletonRow key={i} index={i} />)}
              </div>
            </div>
          ) : error ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="glass-card rounded-3xl p-10 text-center"
            >
              <AlertCircle size={32} className="text-red-400 mx-auto mb-3" />
              <p className="text-slate-400 text-sm mb-4">{error}</p>
              <button
                onClick={handleRefresh}
                className="px-5 py-2.5 rounded-xl bg-primary/20 border border-primary/30 text-primary text-sm font-bold hover:bg-primary/30 transition-all duration-200"
              >
                Retry
              </button>
            </motion.div>
          ) : entries.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card rounded-3xl p-12 text-center"
            >
              <div className="w-16 h-16 rounded-3xl bg-gradient-to-br from-amber-500/20 to-yellow-500/20 border border-amber-500/20 flex items-center justify-center mx-auto mb-4">
                <Trophy size={28} className="text-amber-400/60" />
              </div>
              <h3 className="text-lg font-black text-white mb-2">No Rankings Yet</h3>
              <p className="text-slate-500 text-sm">
                {scope === 'friends'
                  ? 'Follow other developers to see a friends leaderboard.'
                  : 'Complete quests to appear on the leaderboard.'}
              </p>
            </motion.div>
          ) : (
            <>
              {/* ── Podium (top 3) ── */}
              {top3.length >= 1 && (
                <motion.div
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="glass-card rounded-3xl p-6 relative overflow-hidden"
                >
                  <div className="absolute inset-0 bg-gradient-to-b from-amber-500/3 via-transparent to-transparent pointer-events-none" />
                  <div className="flex items-end justify-center gap-4 relative z-10">
                    {top3.map((entry, i) => (
                      <PodiumCard
                        key={entry.user_id}
                        entry={entry}
                        position={i}
                        delay={0.15 + i * 0.1}
                      />
                    ))}
                  </div>
                </motion.div>
              )}

              {/* ── Rank Table (4+) ── */}
              {tableEntries.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="glass-card rounded-3xl overflow-hidden"
                >
                  {/* Table header */}
                  <div className="flex items-center gap-3 px-4 py-3 border-b border-white/5 bg-black/20">
                    <div className="w-8 text-[10px] font-bold uppercase tracking-widest text-slate-600 text-center">Rank</div>
                    <div className="w-10 shrink-0" />
                    <div className="flex-1 text-[10px] font-bold uppercase tracking-widest text-slate-600">Player</div>
                    <div className="text-[10px] font-bold uppercase tracking-widest text-slate-600 w-20 text-right">XP</div>
                    <div className="text-[10px] font-bold uppercase tracking-widest text-slate-600 w-12 text-right">Change</div>
                  </div>

                  <div className="p-3 space-y-1">
                    <AnimatePresence mode="popLayout">
                      {tableEntries.map((entry, i) => (
                        <LeaderboardRow
                          key={entry.user_id}
                          entry={entry}
                          isCurrentUser={entry.user_id === user?.id}
                          index={i}
                        />
                      ))}
                    </AnimatePresence>
                  </div>

                  {/* Load more */}
                  {hasMore && (
                    <div className="px-4 pb-4">
                      <button
                        onClick={handleLoadMore}
                        disabled={loadingMore}
                        className={cn(
                          'w-full flex items-center justify-center gap-2 py-3 rounded-xl border text-xs font-black uppercase tracking-wider transition-all duration-200',
                          'bg-white/5 border-white/10 text-slate-400 hover:bg-white/10 hover:text-white',
                          loadingMore && 'opacity-60 cursor-not-allowed'
                        )}
                      >
                        {loadingMore
                          ? <><Loader2 size={13} className="animate-spin" /> Loading...</>
                          : <><ChevronDown size={13} /> Load More ({total - entries.length} remaining)</>
                        }
                      </button>
                    </div>
                  )}
                </motion.div>
              )}

              {/* If only top 3 exist and no table entries */}
              {tableEntries.length === 0 && top3.length > 0 && (
                <p className="text-center text-slate-600 text-xs font-bold py-4">
                  Only {top3.length} ranked player{top3.length !== 1 ? 's' : ''} so far
                </p>
              )}
            </>
          )}
        </div>

        <BottomNav />
      </div>
    </MainLayout>
  );
}
