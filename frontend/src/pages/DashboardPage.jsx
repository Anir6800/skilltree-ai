/**
 * SkillTree AI - Developer Dashboard
 * A premium, gamified dashboard featuring real-time XP tracking and progress visualization.
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  TrendingUp, 
  Zap, 
  Target, 
  Trophy, 
  Clock, 
  ChevronRight,
  Flame,
  Layout,
  Award,
  BookOpen,
  ArrowUpRight,
  User as UserIcon,
  Shield
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { fetchDashboardData } from '../api/dashboardApi';
import useAuthStore from '../store/authStore';
import MainLayout from '../components/layout/MainLayout';
import CurriculumWidget from '../components/dashboard/CurriculumWidget';

const DashboardPage = () => {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const dashboardData = await fetchDashboardData();
        setData(dashboardData);
      } catch (err) {
        setError("Failed to load dashboard data. Please try again.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  if (loading) return <DashboardSkeleton />;
  if (error) return <ErrorMessage message={error} />;

  const { user, xp_history, active_quests, top_leaderboard, skills_progress } = data;

  // Calculate XP progress percentage
  const nextLevelXP = (user.level + 1) * 1000;
  const currentLevelXP = user.level * 1000;
  const progressInLevel = user.xp - currentLevelXP;
  const xpPercentage = Math.min(Math.max((progressInLevel / 1000) * 100, 5), 100);

  return (
    <MainLayout>
    <div className="min-h-screen bg-[#0a0c10] text-white p-4 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* BACKGROUND EFFECTS */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
        <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-purple-600/10 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-600/10 blur-[120px] rounded-full" />
      </div>

      {/* HEADER SECTION */}
      <motion.header 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row md:items-center justify-between gap-6"
      >
        <div>
          <h1 className="text-3xl md:text-4xl font-black tracking-tight text-white flex items-center gap-3">
            Welcome back, <span className="premium-gradient-text">{user.username}</span>
            <span className="text-2xl animate-bounce">👋</span>
          </h1>
          <p className="text-slate-400 mt-2 flex items-center gap-2 font-medium">
            <Shield className="w-4 h-4 text-primary" />
            Rank #{user.rank || 'N/A'} • Level {user.level} {user.role === 'admin' ? '• System Admin' : ''}
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="glass-panel px-4 py-2 rounded-2xl flex items-center gap-3 border-primary/20 shadow-[0_0_20px_rgba(99,102,241,0.1)]">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white font-bold text-lg">
              {user.username[0].toUpperCase()}
            </div>
            <div>
              <div className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Current XP</div>
              <div className="text-sm font-black text-primary">{user.xp.toLocaleString()} XP</div>
            </div>
          </div>
          
          <div className="glass-panel px-4 py-2 rounded-2xl flex items-center gap-3 border-accent/20">
            <div className="w-10 h-10 rounded-xl bg-accent/20 flex items-center justify-center text-accent">
              <Flame className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Streak</div>
              <div className="text-sm font-black text-accent">{user.streak_days} Days</div>
            </div>
          </div>
        </div>
      </motion.header>

      {/* XP PROGRESS BAR */}
      <motion.section 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
        className="glass-panel p-6 rounded-3xl relative overflow-hidden"
      >
        <div className="flex justify-between items-end mb-4 relative z-10">
          <div>
            <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">Level Progress</span>
            <h2 className="text-2xl font-black">Level {user.level}</h2>
          </div>
          <div className="text-right">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">Next Level</span>
            <div className="text-lg font-black text-primary">{(user.level + 1) * 1000} XP</div>
          </div>
        </div>
        
        <div className="h-4 w-full bg-white/5 rounded-full overflow-hidden border border-white/10 p-0.5 relative z-10">
          <motion.div 
            initial={{ width: 0 }}
            animate={{ width: `${xpPercentage}%` }}
            transition={{ duration: 1.5, ease: "easeOut" }}
            className="h-full bg-gradient-to-r from-primary via-accent to-primary bg-[length:200%_auto] animate-gradient-flow rounded-full relative"
          >
            <div className="absolute inset-0 bg-white/20 blur-sm" />
          </motion.div>
        </div>
        
        <div className="flex justify-between mt-3 text-[10px] font-bold text-slate-500 uppercase tracking-tighter relative z-10">
          <span>{progressInLevel} XP Gained</span>
          <span>{1000 - progressInLevel} XP to go</span>
        </div>

        {/* Decorative Background Icon */}
        <Zap className="absolute -right-8 -bottom-8 w-48 h-48 text-primary/5 -rotate-12" />
      </motion.section>

      {/* STATS GRID */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
        {[
          { label: 'Skills Mastered', value: skills_progress.completed, icon: Target, color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
          { label: 'Active Quests', value: active_quests.length, icon: BookOpen, color: 'text-blue-400', bg: 'bg-blue-400/10' },
          { label: 'Current Level', value: user.level, icon: Zap, color: 'text-yellow-400', bg: 'bg-yellow-400/10' },
          { label: 'Global Rank', value: `#${user.rank || 'N/A'}`, icon: Trophy, color: 'text-purple-400', bg: 'bg-purple-400/10' },
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 + (i * 0.1) }}
            className="glass-panel p-6 rounded-3xl hover:bg-white/[0.07] transition-colors group relative overflow-hidden"
          >
            <div className={`w-12 h-12 ${stat.bg} rounded-2xl flex items-center justify-center ${stat.color} mb-4 group-hover:scale-110 transition-transform`}>
              <stat.icon className="w-6 h-6" />
            </div>
            <div className="text-2xl font-black text-white">{stat.value}</div>
            <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mt-1">{stat.label}</div>
            <div className={`absolute top-0 right-0 w-1 h-full ${stat.color.replace('text', 'bg')} opacity-20`} />
          </motion.div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6 md:gap-8">
        {/* XP HISTORY CHART */}
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.6 }}
          className="lg:col-span-2 glass-panel p-6 rounded-3xl"
        >
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-xl font-black flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-primary" />
              XP Growth
            </h3>
            <div className="flex gap-2">
              <span className="px-3 py-1 bg-white/5 rounded-full text-[10px] font-bold text-slate-400">Last 7 Days</span>
            </div>
          </div>
          
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%" minWidth={0}>
              <AreaChart data={xp_history}>
                <defs>
                  <linearGradient id="colorXP" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                <XAxis 
                  dataKey="date" 
                  stroke="#64748b" 
                  fontSize={10} 
                  tickLine={false} 
                  axisLine={false}
                  tickFormatter={(val) => new Date(val).toLocaleDateString('en-US', { weekday: 'short' })}
                />
                <YAxis hide />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#0f172a', 
                    borderRadius: '16px', 
                    border: '1px solid rgba(255,255,255,0.1)',
                    boxShadow: '0 10px 30px rgba(0,0,0,0.5)'
                  }}
                  itemStyle={{ color: '#6366f1', fontWeight: 'bold' }}
                />
                <Area 
                  type="monotone" 
                  dataKey="xp_gained" 
                  stroke="#6366f1" 
                  strokeWidth={4}
                  fillOpacity={1} 
                  fill="url(#colorXP)" 
                  animationDuration={2000}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* TOP LEADERBOARD */}
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.7 }}
          className="glass-panel p-6 rounded-3xl"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-black flex items-center gap-2">
              <Trophy className="w-5 h-5 text-yellow-400" />
              Top Ranks
            </h3>
            <button className="text-[10px] font-bold text-slate-400 hover:text-white uppercase tracking-widest transition-colors flex items-center gap-1" onClick={() => navigate('/leaderboard')}>
              View All <ChevronRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-4">
            {top_leaderboard.map((player, idx) => (
              <div 
                key={player.username}
                className={`flex items-center justify-between p-3 rounded-2xl border border-transparent hover:border-white/5 hover:bg-white/[0.03] transition-all ${player.username === user.username ? 'bg-primary/10 border-primary/20' : ''}`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${idx === 0 ? 'bg-yellow-400 text-black' : idx === 1 ? 'bg-slate-300 text-black' : idx === 2 ? 'bg-orange-400 text-black' : 'bg-white/10 text-slate-400'}`}>
                    {player.rank}
                  </div>
                  <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center overflow-hidden">
                    {player.avatar_url ? (
                      <img src={player.avatar_url} alt={player.username} className="w-full h-full object-cover" />
                    ) : (
                      <UserIcon className="w-5 h-5 text-slate-500" />
                    )}
                  </div>
                  <div>
                    <div className="text-sm font-bold truncate max-w-[100px]">{player.username}</div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase">Level {player.level}</div>
                  </div>
                </div>
                <div className="text-sm font-black text-primary">
                  {player.xp.toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* ACTIVE QUESTS SECTION */}
      <motion.section 
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-2xl font-black flex items-center gap-3">
            <Layout className="w-6 h-6 text-accent" />
            Active Quests
          </h3>
          <button className="text-xs font-bold text-slate-400 hover:text-white uppercase tracking-widest transition-colors flex items-center gap-1 bg-white/5 px-4 py-2 rounded-full" onClick={() => navigate('/quests')}>
            Quest Log <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {active_quests.length > 0 ? (
          <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
            {active_quests.map((quest, i) => (
              <motion.div
                key={quest.id}
                whileHover={{ scale: 1.02, translateY: -5 }}
                onClick={() => navigate(`/editor/${quest.id}`)}
                className="glass-panel p-6 rounded-3xl group cursor-pointer border-white/5 hover:border-primary/30 transition-all relative overflow-hidden"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="p-3 bg-primary/10 rounded-2xl text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                    <Zap className="w-6 h-6" />
                  </div>
                  <div className="flex flex-col items-end">
                    <span className="text-[10px] font-black text-primary uppercase tracking-tighter mb-1">XP Reward</span>
                    <span className="text-lg font-black text-white">+{quest.xp_reward}</span>
                  </div>
                </div>
                
                <h4 className="text-lg font-black text-white mb-2 line-clamp-1">{quest.title}</h4>
                <div className="flex items-center gap-4 text-xs font-bold text-slate-500 uppercase tracking-widest">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3 text-accent" />
                    {quest.estimated_minutes}m
                  </span>
                  <span className="px-2 py-0.5 bg-white/5 rounded text-[10px]">
                    {quest.type}
                  </span>
                </div>
                
                <div className="mt-6 flex items-center justify-between">
                  <div className="flex -space-x-2">
                    {[1, 2, 3].map(n => (
                      <div key={n} className="w-6 h-6 rounded-full border-2 border-[#0a0c10] bg-slate-800 flex items-center justify-center text-[8px] font-bold">
                        {n}
                      </div>
                    ))}
                    <div className="w-6 h-6 rounded-full border-2 border-[#0a0c10] bg-primary/20 flex items-center justify-center text-[8px] font-bold text-primary">
                      +12
                    </div>
                  </div>
                  <button className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-slate-400 group-hover:bg-primary group-hover:text-white transition-all">
                    <ArrowUpRight className="w-5 h-5" />
                  </button>
                </div>

                <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-primary/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="glass-panel p-12 rounded-3xl text-center border-dashed border-white/10">
            <div className="w-20 h-20 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-6">
              <BookOpen className="w-10 h-10 text-slate-600" />
            </div>
            <h4 className="text-xl font-black text-slate-300">No Active Quests</h4>
            <p className="text-slate-500 mt-2 max-w-xs mx-auto font-medium">Head over to the Skill Tree to unlock new challenges and start earning XP.</p>
            <button className="mt-8 px-8 py-3 bg-primary text-white rounded-2xl font-black uppercase tracking-widest text-xs shadow-lg shadow-primary/20 hover:scale-105 transition-transform" onClick={() => navigate('/skills')}>
              Explore Skills
            </button>
          </div>
        )}
      </motion.section>

      {/* CURRICULUM WIDGET */}
      <CurriculumWidget />
    </div>
    </MainLayout>
  );
};

// --- SUBCOMPONENTS ---

const DashboardSkeleton = () => (
  <div className="min-h-screen bg-[#0a0c10] p-8 animate-pulse space-y-8 max-w-7xl mx-auto">
    <div className="h-12 bg-white/5 rounded-2xl w-1/3" />
    <div className="h-40 bg-white/5 rounded-3xl w-full" />
    <div className="grid grid-cols-4 gap-6">
      {[1, 2, 3, 4].map(n => <div key={n} className="h-32 bg-white/5 rounded-3xl" />)}
    </div>
    <div className="grid grid-cols-3 gap-8">
      <div className="col-span-2 h-80 bg-white/5 rounded-3xl" />
      <div className="h-80 bg-white/5 rounded-3xl" />
    </div>
  </div>
);

const ErrorMessage = ({ message }) => (
  <div className="min-h-screen bg-[#0a0c10] flex items-center justify-center p-8">
    <div className="glass-panel p-8 rounded-3xl text-center max-w-md">
      <div className="w-16 h-16 bg-red-500/10 rounded-2xl flex items-center justify-center text-red-500 mx-auto mb-4">
        <Shield className="w-8 h-8" />
      </div>
      <h3 className="text-xl font-black text-white mb-2">Access Error</h3>
      <p className="text-slate-400 font-medium">{message}</p>
      <button 
        onClick={() => window.location.reload()}
        className="mt-6 px-6 py-2 bg-white/10 hover:bg-white/20 rounded-xl font-bold transition-all"
      >
        Retry
      </button>
    </div>
  </div>
);

export default DashboardPage;