/**
 * SkillTree AI - Admin Heatmap Tab
 * Quest difficulty heatmap with analytics and AI regeneration.
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, AlertCircle, RefreshCw, Zap } from 'lucide-react';
import api from '../../api/api';
import { cn } from '../../utils/cn';

const CELL_WIDTH = 80;
const CELL_HEIGHT = 60;

function getPassRateColor(passRate) {
  if (passRate >= 85) return '#10b981';
  if (passRate >= 50) return '#eab308';
  if (passRate >= 25) return '#f97316';
  return '#ef4444';
}

function getPassRateLabel(passRate) {
  if (passRate >= 85) return 'Healthy';
  if (passRate >= 50) return 'Moderate';
  if (passRate >= 25) return 'Difficult';
  return 'Very Hard';
}

function QuestCell({ quest, onViewDetail, onRegenerate }) {
  const [showTooltip, setShowTooltip] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);

  const bgColor = getPassRateColor(quest.pass_rate);
  const hasFlag = quest.flag !== null;
  const isTooHard = quest.flag === 'too_hard';
  const isTooEasy = quest.flag === 'too_easy';

  const handleRegenerate = async (difficulty) => {
    setIsRegenerating(true);
    try {
      await onRegenerate(quest.quest_id, difficulty);
    } finally {
      setIsRegenerating(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="relative"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <div
        className={cn(
          'rounded-lg cursor-pointer transition-all duration-200 flex items-center justify-center relative overflow-hidden',
          isTooHard && 'animate-pulse',
          isTooHard && 'border-2 border-red-500',
          isTooEasy && 'border-2 border-dashed border-slate-500',
          !hasFlag && 'border border-white/20 hover:border-white/40'
        )}
        style={{
          width: `${CELL_WIDTH}px`,
          height: `${CELL_HEIGHT}px`,
          backgroundColor: bgColor,
          opacity: 0.85,
        }}
      >
        <div className="text-center">
          <p className="text-xs font-bold text-white">{quest.pass_rate.toFixed(0)}%</p>
          <p className="text-xs text-white/80">{quest.total_submissions} subs</p>
        </div>

        {hasFlag && (
          <div className="absolute top-1 right-1">
            <span className={cn(
              'text-xs font-bold px-1.5 py-0.5 rounded',
              isTooHard && 'bg-red-500/80 text-white',
              isTooEasy && 'bg-slate-500/80 text-white'
            )}>
              {isTooHard ? '🔴' : '⚪'}
            </span>
          </div>
        )}
      </div>

      {/* Tooltip */}
      <AnimatePresence>
        {showTooltip && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 z-50 pointer-events-none"
          >
            <div className="bg-slate-900 border border-white/20 rounded-lg p-3 shadow-xl whitespace-nowrap">
              <p className="text-sm font-bold text-white mb-1">{quest.title}</p>
              <div className="text-xs text-slate-300 space-y-0.5">
                <p>Pass Rate: <span className="text-white font-semibold">{quest.pass_rate.toFixed(1)}%</span></p>
                <p>Avg Attempts: <span className="text-white font-semibold">{quest.avg_attempts.toFixed(1)}</span></p>
                <p>Solve Time: <span className="text-white font-semibold">{quest.avg_solve_time_minutes.toFixed(0)}m</span></p>
                <p>Difficulty: <span className="text-white font-semibold">{quest.difficulty_score.toFixed(2)}</span></p>
              </div>
              {quest.flag && (
                <div className={cn(
                  'mt-2 pt-2 border-t border-white/10 text-xs font-bold',
                  quest.flag === 'too_hard' && 'text-red-400',
                  quest.flag === 'too_easy' && 'text-slate-400'
                )}>
                  {quest.flag === 'too_hard' ? '🔴 Too Hard' : '⚪ Too Easy'}
                </div>
              )}
              {quest.flag && (
                <div className="mt-2 pt-2 border-t border-white/10 flex gap-1">
                  {quest.flag === 'too_hard' && (
                    <button
                      onClick={() => handleRegenerate('easier')}
                      disabled={isRegenerating}
                      className="text-xs px-2 py-1 bg-emerald-500/20 border border-emerald-500/40 rounded text-emerald-400 hover:bg-emerald-500/30 disabled:opacity-50"
                    >
                      {isRegenerating ? '...' : 'Make Easier'}
                    </button>
                  )}
                  {quest.flag === 'too_easy' && (
                    <button
                      onClick={() => handleRegenerate('harder')}
                      disabled={isRegenerating}
                      className="text-xs px-2 py-1 bg-amber-500/20 border border-amber-500/40 rounded text-amber-400 hover:bg-amber-500/30 disabled:opacity-50"
                    >
                      {isRegenerating ? '...' : 'Make Harder'}
                    </button>
                  )}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default function HeatmapTab() {
  const [skills, setSkills] = useState([]);
  const [selectedSkillId, setSelectedSkillId] = useState(null);
  const [analytics, setAnalytics] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [regenerating, setRegenerating] = useState(false);

  useEffect(() => {
    loadSkills();
  }, []);

  useEffect(() => {
    if (selectedSkillId) {
      loadHeatmap();
    }
  }, [selectedSkillId]);

  const loadSkills = async () => {
    try {
      const response = await api.get('/api/admin/analytics/skills/');
      setSkills(response.data);
      if (response.data.length > 0) {
        setSelectedSkillId(response.data[0].id);
      }
    } catch (err) {
      console.error('Failed to load skills:', err);
      setError('Failed to load skills');
    }
  };

  const loadHeatmap = async () => {
    if (!selectedSkillId) return;

    try {
      setLoading(true);
      const response = await api.get('/api/admin/analytics/heatmap/', {
        params: { skill_id: selectedSkillId },
      });
      setAnalytics(response.data.analytics);
      setSummary(response.data.summary);
      setError(null);
    } catch (err) {
      console.error('Failed to load heatmap:', err);
      setError('Failed to load heatmap data');
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerate = async (questId, difficulty) => {
    setRegenerating(true);
    try {
      await api.post('/api/admin/quests/generate/', {
        quest_id: questId,
        difficulty: difficulty,
      });
      await loadHeatmap();
    } catch (err) {
      console.error('Failed to regenerate quest:', err);
      setError('Failed to regenerate quest');
    } finally {
      setRegenerating(false);
    }
  };

  const selectedSkill = skills.find(s => s.id === selectedSkillId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">Quest Difficulty Heatmap</h2>
        <p className="text-slate-400">Analyze quest difficulty and identify problematic quests</p>
      </div>

      {/* Skill Selector */}
      <div className="flex items-center gap-4">
        <label className="text-sm font-semibold text-white">Select Skill:</label>
        <select
          value={selectedSkillId || ''}
          onChange={(e) => setSelectedSkillId(parseInt(e.target.value))}
          className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-primary/50"
        >
          <option value="">Choose a skill...</option>
          {skills.map(skill => (
            <option key={skill.id} value={skill.id}>
              {skill.title}
            </option>
          ))}
        </select>
      </div>

      {/* Error */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-3 text-red-400"
        >
          <AlertCircle size={20} />
          {error}
        </motion.div>
      )}

      {/* Loading */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={32} className="animate-spin text-primary" />
        </div>
      ) : analytics.length === 0 ? (
        <div className="text-center py-12 text-slate-400">
          No quests found for this skill
        </div>
      ) : (
        <>
          {/* Summary Bar */}
          {summary && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-4 bg-white/5 border border-white/10 rounded-lg"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-6 text-sm">
                  <span className="text-slate-300">
                    <span className="font-bold text-red-400">{summary.too_hard_count}</span> too hard
                  </span>
                  <span className="text-slate-300">
                    <span className="font-bold text-slate-400">{summary.too_easy_count}</span> too easy
                  </span>
                  <span className="text-slate-300">
                    <span className="font-bold text-emerald-400">{summary.healthy_count}</span> healthy
                  </span>
                </div>
                <button
                  onClick={loadHeatmap}
                  disabled={loading}
                  className="flex items-center gap-2 px-3 py-1 bg-primary/20 border border-primary/40 rounded text-sm text-primary hover:bg-primary/30 disabled:opacity-50"
                >
                  <RefreshCw size={16} />
                  Refresh
                </button>
              </div>
            </motion.div>
          )}

          {/* Heatmap Grid */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="p-6 bg-white/5 border border-white/10 rounded-lg overflow-x-auto"
          >
            <div className="flex flex-wrap gap-4">
              {analytics.map(quest => (
                <QuestCell
                  key={quest.quest_id}
                  quest={quest}
                  onRegenerate={handleRegenerate}
                />
              ))}
            </div>
          </motion.div>

          {/* Legend */}
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 bg-white/5 border border-white/10 rounded-lg"
          >
            <h3 className="text-sm font-bold text-white mb-3">Legend</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded bg-emerald-500/85" />
                <span className="text-slate-300">≥85% Pass Rate</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded bg-yellow-500/85" />
                <span className="text-slate-300">50-85% Pass Rate</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded bg-orange-500/85" />
                <span className="text-slate-300">25-50% Pass Rate</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded bg-red-500/85" />
                <span className="text-slate-300">&lt;25% Pass Rate</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded border-2 border-red-500 animate-pulse" />
                <span className="text-slate-300">Too Hard</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded border-2 border-dashed border-slate-500" />
                <span className="text-slate-300">Too Easy</span>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </div>
  );
}
