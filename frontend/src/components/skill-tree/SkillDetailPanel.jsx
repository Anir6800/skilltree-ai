/**
 * SkillTree AI - Skill Detail Sidebar Panel
 * Glassmorphic sidebar with skill details, depth indicator, and quest navigation
 * @module components/skill-tree/SkillDetailPanel
 */

import { motion, AnimatePresence } from 'framer-motion';
import { X, Zap, CheckCircle2, Lock, ArrowRight, Target, Layers } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { SKILL_STATUS } from '../../constants';
import { cn } from '../../utils/cn';
import { useState } from 'react';

/**
 * Category color mapping
 */
const CATEGORY_COLORS = {
  algorithms: 'text-purple-400 bg-purple-500/10 border-purple-500/30',
  'data-structures': 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30',
  systems: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
  'web-dev': 'text-pink-400 bg-pink-500/10 border-pink-500/30',
  'ai-ml': 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
};

/**
 * Difficulty dots renderer
 */
const DifficultyIndicator = ({ difficulty }) => {
  return (
    <div className="flex items-center gap-1">
      {[...Array(5)].map((_, i) => (
        <div
          key={i}
          className={cn(
            'w-2 h-2 rounded-full transition-all duration-300',
            i < difficulty
              ? 'bg-primary shadow-[0_0_6px_rgba(99,102,241,0.8)]'
              : 'bg-white/10'
          )}
        />
      ))}
    </div>
  );
};

/**
 * Depth level indicator
 */
const DepthIndicator = ({ depth }) => {
  return (
    <div className="flex items-center gap-2">
      <Layers size={14} className="text-slate-400" />
      <span className="text-xs font-bold text-slate-300">Level {depth}</span>
    </div>
  );
};

/**
 * Skill Detail Panel Component
 */
const SkillDetailPanel = ({ skill, onClose, onStartSkill }) => {
  const navigate = useNavigate();
  const [isStarting, setIsStarting] = useState(false);

  if (!skill) return null;

  const isLocked = skill.status === SKILL_STATUS.LOCKED;
  const isAvailable = skill.status === SKILL_STATUS.AVAILABLE;
  const isCompleted = skill.status === SKILL_STATUS.COMPLETED;
  const isInProgress = skill.status === SKILL_STATUS.IN_PROGRESS;

  const handleStartSkill = async () => {
    if (isAvailable && onStartSkill) {
      setIsStarting(true);
      try {
        await onStartSkill(skill.id);
      } finally {
        setIsStarting(false);
      }
    }
  };

  const handleViewQuests = () => {
    navigate(`/quests?skill_id=${skill.id}`);
  };

  const handleStartQuest = () => {
    // Navigate to quest board filtered by this skill's quests
    navigate(`/quests?skill_id=${skill.id}`);
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ x: 400, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: 400, opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        className="fixed right-0 top-0 h-screen w-[350px] z-50 flex flex-col"
      >
        {/* Glass Panel */}
        <div className="glass-panel h-full border-l border-white/10 shadow-2xl backdrop-blur-3xl flex flex-col">
          {/* Header */}
          <div className="relative p-6 border-b border-white/5">
            {/* Subtle glow */}
            <div className="absolute -top-12 -right-12 w-32 h-32 bg-primary/20 rounded-full blur-3xl" />
            
            <div className="relative flex items-start justify-between">
              <div className="flex-1">
                <h2 className="text-2xl font-black tracking-tight text-white mb-2">
                  {skill.name}
                </h2>
                
                {/* Category Badge */}
                <div
                  className={cn(
                    'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border backdrop-blur-md',
                    CATEGORY_COLORS[skill.category] || 'text-slate-400 bg-slate-500/10 border-slate-500/30'
                  )}
                >
                  <div className="w-1.5 h-1.5 rounded-full bg-current" />
                  {skill.category?.replace('-', ' ')}
                </div>
              </div>

              {/* Close Button */}
              <button
                onClick={onClose}
                className="p-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all duration-300 hover:scale-110"
              >
                <X size={18} className="text-slate-400 hover:text-white transition-colors" />
              </button>
            </div>
          </div>

          {/* Scrollable Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Description */}
            <div>
              <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-3">
                Overview
              </h3>
              <p className="text-sm text-slate-300 leading-relaxed">
                {skill.description || 'No description available.'}
              </p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-3">
              {/* Difficulty */}
              <div className="glass-card p-4 rounded-xl">
                <div className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2">
                  Difficulty
                </div>
                <DifficultyIndicator difficulty={skill.difficulty || 1} />
              </div>

              {/* Depth Level */}
              <div className="glass-card p-4 rounded-xl">
                <div className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2">
                  Tree Depth
                </div>
                <DepthIndicator depth={skill.tree_depth || 0} />
              </div>

              {/* XP Required */}
              <div className="glass-card p-4 rounded-xl col-span-2">
                <div className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2">
                  XP Required
                </div>
                <div className="flex items-center gap-1.5 text-primary font-bold">
                  <Zap size={14} fill="currentColor" />
                  <span>{skill.xpRequired || 0}</span>
                </div>
              </div>
            </div>

            {/* Prerequisites */}
            {skill.prerequisites && skill.prerequisites.length > 0 && (
              <div>
                <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-3 flex items-center gap-2">
                  <Lock size={12} />
                  Prerequisites
                </h3>
                <div className="space-y-2">
                  {skill.prerequisites.map((prereq, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/10"
                    >
                      <div
                        className={cn(
                          'flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center',
                          prereq.completed
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : 'bg-slate-500/20 text-slate-500'
                        )}
                      >
                        {prereq.completed ? (
                          <CheckCircle2 size={12} />
                        ) : (
                          <Lock size={10} />
                        )}
                      </div>
                      <span
                        className={cn(
                          'text-sm font-medium',
                          prereq.completed ? 'text-slate-300' : 'text-slate-500'
                        )}
                      >
                        {prereq.name}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Linked Quests */}
            {skill.questCount > 0 && (
              <div>
                <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-3 flex items-center gap-2">
                  <Target size={12} />
                  Linked Quests
                </h3>
                <div className="glass-card p-4 rounded-xl flex items-center justify-between">
                  <div>
                    <div className="text-2xl font-black text-white">
                      {skill.questCount}
                    </div>
                    <div className="text-xs text-slate-400">
                      {skill.questCount === 1 ? 'Quest' : 'Quests'} Available
                    </div>
                  </div>
                  <button
                    onClick={handleViewQuests}
                    className="p-2 rounded-lg bg-primary/10 hover:bg-primary/20 border border-primary/30 transition-all duration-300 group"
                  >
                    <ArrowRight
                      size={16}
                      className="text-primary group-hover:translate-x-1 transition-transform"
                    />
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Actions Footer */}
          <div className="p-6 border-t border-white/5 space-y-3">
            {isAvailable && (
              <button
                onClick={handleStartSkill}
                disabled={isStarting}
                className="auth-btn-primary group flex items-center justify-center space-x-2"
              >
                <span>{isStarting ? 'Starting...' : 'Start Skill'}</span>
                {!isStarting && (
                  <ArrowRight
                    size={16}
                    className="group-hover:translate-x-1 transition-transform"
                  />
                )}
              </button>
            )}

            {isInProgress && (
              <>
                <button
                  onClick={handleStartQuest}
                  className="auth-btn-primary group flex items-center justify-center space-x-2"
                >
                  <span>Start Quest</span>
                  <ArrowRight
                    size={16}
                    className="group-hover:translate-x-1 transition-transform"
                  />
                </button>
                <button
                  onClick={handleViewQuests}
                  className="w-full py-3 bg-white/5 border border-white/10 rounded-xl flex items-center justify-center gap-2 text-xs font-bold text-slate-400 hover:bg-white/10 hover:text-white transition-all duration-300 group"
                >
                  View All Quests
                  <ArrowRight
                    size={14}
                    className="group-hover:translate-x-1 transition-transform"
                  />
                </button>
              </>
            )}

            {isCompleted && (
              <div className="glass-card p-4 rounded-xl border-emerald-500/30 bg-emerald-500/5">
                <div className="flex items-center gap-3">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
                    <CheckCircle2 size={20} className="text-emerald-400" />
                  </div>
                  <div>
                    <div className="text-sm font-bold text-emerald-400">
                      Completed
                    </div>
                    <div className="text-xs text-slate-400">
                      Skill mastered!
                    </div>
                  </div>
                </div>
              </div>
            )}

            {isLocked && (
              <div className="glass-card p-4 rounded-xl border-slate-500/30 bg-slate-500/5">
                <div className="flex items-center gap-3">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-slate-500/20 flex items-center justify-center">
                    <Lock size={20} className="text-slate-400" />
                  </div>
                  <div>
                    <div className="text-sm font-bold text-slate-400">
                      Locked
                    </div>
                    <div className="text-xs text-slate-500">
                      Complete prerequisites first
                    </div>
                  </div>
                </div>
              </div>
            )}

            {!isAvailable && !isInProgress && !isCompleted && !isLocked && (
              <button
                onClick={handleViewQuests}
                className="w-full py-3 bg-white/5 border border-white/10 rounded-xl flex items-center justify-center gap-2 text-xs font-bold text-slate-400 hover:bg-white/10 hover:text-white transition-all duration-300 group"
              >
                View All Quests
                <ArrowRight
                  size={14}
                  className="group-hover:translate-x-1 transition-transform"
                />
              </button>
            )}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default SkillDetailPanel;
