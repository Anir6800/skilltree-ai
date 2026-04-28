/**
 * SkillTree AI - Skill Radar Chart
 * 5-axis radar chart showing mastery across core skill categories
 * @module components/profile/SkillRadarChart
 */

import React, { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, AlertCircle, Zap } from 'lucide-react';
import { getSkillRadar } from '../../api/skillApi';

const SkillRadarChart = () => {
  const [radarData, setRadarData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [animationKey, setAnimationKey] = useState(0);
  const prevDataRef = useRef(null);

  useEffect(() => {
    loadRadarData();
  }, []);

  const loadRadarData = async () => {
    try {
      setLoading(true);
      const response = await getSkillRadar();
      
      if (response?.data) {
        setRadarData(response.data);
        setLastUpdated(new Date());
        prevDataRef.current = response.data;
        setAnimationKey(prev => prev + 1);
      }
      setError(null);
    } catch (err) {
      console.error('Failed to load skill radar:', err);
      setError('Failed to load skill radar data');
    } finally {
      setLoading(false);
    }
  };

  const getMinutesAgo = () => {
    if (!lastUpdated) return null;
    const now = new Date();
    const diffMs = now - lastUpdated;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins === 0) return 'just now';
    if (diffMins === 1) return '1 minute ago';
    if (diffMins < 60) return `${diffMins} minutes ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours === 1) return '1 hour ago';
    return `${diffHours} hours ago`;
  };

  const getStrongestCategory = () => {
    if (!radarData || radarData.length === 0) return null;
    return radarData.reduce((max, cat) => 
      cat.mastery_pct > max.mastery_pct ? cat : max
    );
  };

  const getWeakestCategory = () => {
    if (!radarData || radarData.length === 0) return null;
    return radarData.reduce((min, cat) => 
      cat.mastery_pct < min.mastery_pct ? cat : min
    );
  };

  const chartData = radarData?.map(cat => ({
    name: cat.category,
    value: cat.mastery_pct,
    fullData: cat,
  })) || [];

  const strongest = getStrongestCategory();
  const weakest = getWeakestCategory();

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass-panel rounded-3xl p-8 border border-white/10"
      >
        <div className="h-96 flex items-center justify-center">
          <div className="text-center">
            <div className="w-12 h-12 rounded-full border-2 border-primary/30 border-t-primary animate-spin mx-auto mb-4" />
            <p className="text-slate-400 font-medium">Loading skill radar...</p>
          </div>
        </div>
      </motion.div>
    );
  }

  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass-panel rounded-3xl p-8 border border-white/10"
      >
        <div className="h-96 flex items-center justify-center">
          <div className="text-center">
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <p className="text-slate-400 font-medium">{error}</p>
            <button
              onClick={loadRadarData}
              className="mt-4 px-4 py-2 bg-primary/20 border border-primary/40 text-primary rounded-lg font-bold text-sm hover:bg-primary/30 transition-all"
            >
              Retry
            </button>
          </div>
        </div>
      </motion.div>
    );
  }

  if (!chartData || chartData.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass-panel rounded-3xl p-8 border border-white/10"
      >
        <div className="h-96 flex items-center justify-center">
          <div className="text-center">
            <Zap className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <p className="text-slate-400 font-medium">Start learning skills to see your radar</p>
            <p className="text-slate-500 text-sm mt-2">Complete quests to build mastery across categories</p>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      key={animationKey}
      initial={{ opacity: 0, scale: 0.95, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      className="glass-panel rounded-3xl p-8 border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.37)]"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center text-primary">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-xl font-black text-white">Skill Mastery Radar</h3>
            <p className="text-xs text-slate-500 font-bold uppercase tracking-widest mt-0.5">
              Last updated: {getMinutesAgo()}
            </p>
          </div>
        </div>
        <button
          onClick={loadRadarData}
          className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-xs font-bold text-slate-400 hover:text-slate-300 transition-all"
        >
          Refresh
        </button>
      </div>

      {/* Radar Chart */}
      <div className="h-96 w-full mb-8">
        <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0} debounce={50}>
          <RadarChart data={chartData} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <defs>
              <linearGradient id="radarGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#6366f1" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#f43f5e" stopOpacity={0.1} />
              </linearGradient>
            </defs>
            
            <PolarGrid 
              stroke="rgba(255,255,255,0.05)" 
              strokeDasharray="5 5"
              radialLines={false}
            />
            
            <PolarAngleAxis 
              dataKey="name" 
              stroke="rgba(255,255,255,0.3)"
              tick={{ fill: '#94a3b8', fontSize: 12, fontWeight: 600 }}
              angle={90}
              orientation="outer"
            />
            
            <PolarRadiusAxis 
              angle={90}
              domain={[0, 100]}
              stroke="rgba(255,255,255,0.1)"
              tick={{ fill: '#64748b', fontSize: 10 }}
              tickCount={6}
            />
            
            <Radar 
              name="Mastery %" 
              dataKey="value" 
              stroke="#6366f1"
              strokeWidth={3}
              fill="url(#radarGradient)"
              fillOpacity={0.6}
              dot={(props) => <RadarDot {...props} />}
              animationDuration={800}
              animationEasing="ease-out"
            />
            
            <Tooltip content={<CustomTooltip />} />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Insights Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Strongest Category */}
        {strongest && (
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="p-4 rounded-2xl bg-gradient-to-br from-emerald-500/10 to-emerald-600/5 border border-emerald-500/20"
          >
            <div className="flex items-start justify-between mb-2">
              <div>
                <p className="text-xs font-bold text-emerald-400 uppercase tracking-widest">Strongest</p>
                <p className="text-lg font-black text-white mt-1">{strongest.category}</p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-black text-emerald-400">{strongest.mastery_pct}%</div>
                <div className="text-xs text-emerald-400/70 font-bold">{strongest.skills_completed}/{strongest.skills_total}</div>
              </div>
            </div>
            {strongest.top_skill && (
              <p className="text-xs text-slate-400 font-medium">
                Top: <span className="text-emerald-300">{strongest.top_skill.title}</span>
              </p>
            )}
          </motion.div>
        )}

        {/* Weakest Category */}
        {weakest && (
          <motion.div
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="p-4 rounded-2xl bg-gradient-to-br from-amber-500/10 to-amber-600/5 border border-amber-500/20"
          >
            <div className="flex items-start justify-between mb-2">
              <div>
                <p className="text-xs font-bold text-amber-400 uppercase tracking-widest">Focus Area</p>
                <p className="text-lg font-black text-white mt-1">{weakest.category}</p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-black text-amber-400">{weakest.mastery_pct}%</div>
                <div className="text-xs text-amber-400/70 font-bold">{weakest.skills_completed}/{weakest.skills_total}</div>
              </div>
            </div>
            <p className="text-xs text-slate-400 font-medium">
              Complete more quests to improve your mastery
            </p>
          </motion.div>
        )}
      </div>

      {/* Category Breakdown */}
      <div className="space-y-2">
        <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Category Breakdown</p>
        {chartData.map((cat, idx) => (
          <motion.div
            key={cat.name}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 + (idx * 0.05) }}
            className="flex items-center gap-3"
          >
            <div className="flex-1">
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-bold text-slate-300">{cat.name}</span>
                <span className="text-xs font-black text-primary">{cat.value}%</span>
              </div>
              <div className="h-2 bg-white/5 rounded-full overflow-hidden border border-white/10">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${cat.value}%` }}
                  transition={{ duration: 1, delay: 0.5 + (idx * 0.05), ease: 'easeOut' }}
                  className="h-full bg-gradient-to-r from-primary to-accent rounded-full shadow-[0_0_12px_rgba(99,102,241,0.6)]"
                />
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};

/**
 * Custom radar dot with pulsing animation
 */
const RadarDot = (props) => {
  const { cx, cy, fill, payload } = props;
  
  const { cx, cy, payload } = props;
  
  if (typeof cx !== 'number' || typeof cy !== 'number') return null;

  return (
    <g>
      {/* Glow pulse effect */}
      <motion.circle
        cx={cx}
        cy={cy}
        fill="none"
        stroke="#6366f1"
        strokeWidth={2}
        initial={{ r: 8, opacity: 0.3 }}
        animate={{
          r: [8, 14, 8],
          opacity: [0.3, 0, 0.3],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />
      
      {/* Main dot */}
      <motion.circle
        cx={cx}
        cy={cy}
        r={6}
        fill="#6366f1"
        stroke="#ffffff"
        strokeWidth={2}
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{
          duration: 0.6,
          ease: 'easeOut',
          type: 'spring',
          stiffness: 100,
        }}
      />
    </g>
  );
};

/**
 * Custom tooltip for radar chart
 */
const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload || !payload[0]) return null;

  const data = payload[0].payload;
  const fullData = data.fullData;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass-panel rounded-xl p-4 border border-white/20 shadow-[0_8px_32px_rgba(0,0,0,0.5)]"
    >
      <p className="text-sm font-black text-white mb-2">{data.name}</p>
      <div className="space-y-1 text-xs">
        <div className="flex justify-between gap-4">
          <span className="text-slate-400">Mastery:</span>
          <span className="text-primary font-bold">{data.value}%</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-slate-400">Skills:</span>
          <span className="text-slate-300 font-bold">
            {fullData.skills_completed}/{fullData.skills_total}
          </span>
        </div>
        {fullData.top_skill && (
          <div className="flex justify-between gap-4 pt-1 border-t border-white/10">
            <span className="text-slate-400">Top Skill:</span>
            <span className="text-emerald-400 font-bold">{fullData.top_skill.title}</span>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default SkillRadarChart;
