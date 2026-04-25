/**
 * SkillTree AI - Quest Card Component
 * Glassmorphic quest card with hover glow
 * @module components/quests/QuestCard
 */

import { motion } from 'framer-motion';
import { Bug, Code, BookOpen, Clock, Zap, CheckCircle2, Circle, Loader2 } from 'lucide-react';
import { cn } from '../../utils/cn';

const QUEST_TYPE_ICONS = {
  debugging: Bug,
  coding: Code,
  mcq: BookOpen,
};

const QUEST_TYPE_LABELS = {
  debugging: 'Debug',
  coding: 'Coding',
  mcq: 'MCQ',
};

const STATUS_CONFIG = {
  not_started: {
    label: 'Not Started',
    icon: Circle,
    className: 'text-slate-500',
    glowClass: '',
  },
  in_progress: {
    label: 'In Progress',
    icon: Loader2,
    className: 'text-amber-400',
    glowClass: 'shadow-[0_0_20px_rgba(251,191,36,0.3)]',
  },
  passed: {
    label: 'Passed',
    icon: CheckCircle2,
    className: 'text-emerald-400',
    glowClass: 'shadow-[0_0_20px_rgba(52,211,153,0.4)]',
  },
};

/**
 * Quest Card Component
 * @param {Object} props
 * @param {Object} props.quest - Quest data
 * @param {Function} props.onClick - Click handler
 * @returns {JSX.Element}
 */
function QuestCard({ quest, onClick }) {
  const TypeIcon = QUEST_TYPE_ICONS[quest.type] || Code;
  const statusConfig = STATUS_CONFIG[quest.status] || STATUS_CONFIG.not_started;
  const StatusIcon = statusConfig.icon;

  // Calculate difficulty pips (1-5)
  const difficultyLevel = Math.min(5, Math.max(1, Math.round(quest.difficulty_multiplier)));

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.3 }}
      onClick={onClick}
      className={cn(
        "glass-card p-6 rounded-2xl cursor-pointer group relative overflow-hidden",
        statusConfig.glowClass
      )}
    >
      {/* Hover glow effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/0 via-primary/0 to-primary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

      {/* Content */}
      <div className="relative z-10">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className={cn(
              "p-2.5 rounded-xl bg-gradient-to-br transition-all duration-300",
              quest.type === 'debugging' && "from-red-500/20 to-orange-500/20 group-hover:shadow-[0_0_20px_rgba(239,68,68,0.3)]",
              quest.type === 'coding' && "from-blue-500/20 to-cyan-500/20 group-hover:shadow-[0_0_20px_rgba(59,130,246,0.3)]",
              quest.type === 'mcq' && "from-purple-500/20 to-pink-500/20 group-hover:shadow-[0_0_20px_rgba(168,85,247,0.3)]"
            )}>
              <TypeIcon size={20} className={cn(
                quest.type === 'debugging' && "text-red-400",
                quest.type === 'coding' && "text-blue-400",
                quest.type === 'mcq' && "text-purple-400"
              )} />
            </div>
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                {QUEST_TYPE_LABELS[quest.type]}
              </span>
            </div>
          </div>

          {/* Status Badge */}
          <div className={cn(
            "flex items-center gap-1.5 px-3 py-1.5 rounded-full backdrop-blur-sm border",
            statusConfig.className,
            quest.status === 'passed' && "bg-emerald-500/10 border-emerald-500/30",
            quest.status === 'in_progress' && "bg-amber-500/10 border-amber-500/30",
            quest.status === 'not_started' && "bg-white/5 border-white/10"
          )}>
            <StatusIcon size={12} className={quest.status === 'in_progress' ? 'animate-spin' : ''} />
            <span className="text-[10px] font-bold uppercase tracking-wider">
              {statusConfig.label}
            </span>
          </div>
        </div>

        {/* Title */}
        <h3 className="text-lg font-bold text-white mb-2 group-hover:text-primary transition-colors duration-300">
          {quest.title}
        </h3>

        {/* Difficulty Pips */}
        <div className="flex items-center gap-1 mb-4">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className={cn(
                "w-1.5 h-1.5 rounded-full transition-all duration-300",
                i < difficultyLevel
                  ? "bg-primary shadow-[0_0_8px_rgba(99,102,241,0.6)]"
                  : "bg-white/10"
              )}
            />
          ))}
          <span className="text-[10px] font-bold text-slate-500 ml-2 uppercase tracking-wider">
            Difficulty
          </span>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-4 border-t border-white/5">
          <div className="flex items-center gap-4">
            {/* XP Reward */}
            <div className="flex items-center gap-1.5">
              <Zap size={14} className="text-amber-400" fill="currentColor" />
              <span className="text-sm font-bold text-amber-400">
                {quest.xp_reward} XP
              </span>
            </div>

            {/* Estimated Time */}
            <div className="flex items-center gap-1.5">
              <Clock size={14} className="text-slate-500" />
              <span className="text-xs font-medium text-slate-400">
                {quest.estimated_minutes}m
              </span>
            </div>
          </div>

          {/* Arrow indicator */}
          <div className="text-primary opacity-0 group-hover:opacity-100 transform translate-x-0 group-hover:translate-x-1 transition-all duration-300">
            →
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default QuestCard;
