/**
 * SkillTree AI - Skill Radar Chart
 * 5-axis radar chart showing mastery across core skill categories
 * @module components/profile/SkillRadarChart
 */

import React, { useEffect, useState, useRef, useLayoutEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, AlertCircle, Zap } from 'lucide-react';
import { getSkillRadar } from '../../api/skillApi';

/**
 * Inner chart component with dimension guards
 */
const RadarChartContent = ({ data }) => {
  return (
    <div className="w-full min-h-[350px] h-[350px] relative">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
          <PolarGrid stroke="rgba(255,255,255,0.05)" strokeDasharray="5 5" radialLines={false} />
          <PolarAngleAxis 
            dataKey="name" 
            stroke="rgba(255,255,255,0.3)"
            tick={{ fill: '#94a3b8', fontSize: 12, fontWeight: 600 }}
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
            fill="#6366f1"
            fillOpacity={0.3}
            dot={(props) => <RadarDot {...props} />}
            animationDuration={800}
            animationEasing="ease-out"
          />
          <Tooltip content={<CustomTooltip />} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};

/**
 * Main SkillRadarChart component that handles data fetching
 */
const SkillRadarChart = () => {
  const [radarData, setRadarData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [animationKey, setAnimationKey] = useState(0);

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

  const chartData = radarData?.map(cat => ({
    name: cat.category,
    value: cat.mastery_pct,
    fullData: cat,
  })) || [];

  const strongest = radarData?.reduce((max, cat) => cat.mastery_pct > max.mastery_pct ? cat : max, radarData[0]);
  const weakest = radarData?.reduce((min, cat) => cat.mastery_pct < min.mastery_pct ? cat : min, radarData[0]);

  if (loading) {
    return (
      <div className="glass-panel rounded-3xl p-8 border border-white/10 min-h-[400px] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 rounded-full border-2 border-primary/30 border-t-primary animate-spin mx-auto mb-4" />
          <p className="text-slate-400 font-medium">Loading skill radar...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-panel rounded-3xl p-8 border border-white/10 min-h-[400px] flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-slate-400 font-medium">{error}</p>
          <button onClick={loadRadarData} className="mt-4 px-4 py-2 bg-primary/20 border border-primary/40 text-primary rounded-lg font-bold text-sm hover:bg-primary/30 transition-all">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!chartData || chartData.length === 0) {
    return (
      <div className="glass-panel rounded-3xl p-8 border border-white/10 min-h-[400px] flex items-center justify-center text-center">
        <div>
          <Zap className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400 font-medium">Start learning skills to see your radar</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      key={animationKey}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel rounded-3xl p-8 border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.37)]"
    >
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
        <button onClick={loadRadarData} className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-xs font-bold text-slate-400 transition-all">
          Refresh
        </button>
      </div>

      <div className="w-full mb-8">
        <RadarChartContent data={chartData} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {strongest && (
          <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20">
            <p className="text-xs font-bold text-emerald-400 uppercase tracking-widest">Strongest</p>
            <p className="text-lg font-black text-white mt-1">{strongest.category}</p>
            <p className="text-2xl font-black text-emerald-400 mt-1">{strongest.mastery_pct}%</p>
          </div>
        )}
        {weakest && (
          <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20">
            <p className="text-xs font-bold text-amber-400 uppercase tracking-widest">Focus Area</p>
            <p className="text-lg font-black text-white mt-1">{weakest.category}</p>
            <p className="text-2xl font-black text-amber-400 mt-1">{weakest.mastery_pct}%</p>
          </div>
        )}
      </div>
    </motion.div>
  );
};

const RadarDot = (props) => {
  const { cx, cy } = props;
  if (typeof cx !== 'number' || typeof cy !== 'number') return null;
  return (
    <g>
      <circle cx={cx} cy={cy} r={6} fill="#6366f1" stroke="#ffffff" strokeWidth={2} />
    </g>
  );
};

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload || !payload[0]) return null;
  const data = payload[0].payload;
  return (
    <div className="glass-panel rounded-xl p-4 border border-white/20 shadow-xl">
      <p className="text-sm font-black text-white mb-2">{data.name}</p>
      <p className="text-primary font-bold">{data.value}% Mastery</p>
    </div>
  );
};

export default SkillRadarChart;
