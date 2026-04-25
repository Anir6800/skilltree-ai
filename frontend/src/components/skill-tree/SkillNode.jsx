/**
 * SkillTree AI - Custom Skill Node Component
 * Themed node for React Flow with glassmorphism
 * @module components/skill-tree/SkillNode
 */

import { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Lock, CheckCircle2, Zap } from 'lucide-react';
import { motion } from 'framer-motion';
import { SKILL_STATUS } from '../../constants';
import { cn } from '../../utils/cn';

/**
 * Category color mapping
 */
const CATEGORY_COLORS = {
  algorithms: 'bg-purple-500',
  'data-structures': 'bg-cyan-500',
  systems: 'bg-amber-500',
  'web-dev': 'bg-pink-500',
  'ai-ml': 'bg-emerald-500',
};

/**
 * Difficulty dots renderer
 */
const DifficultyIndicator = ({ difficulty }) => {
  return (
    <div className="flex items-center gap-0.5">
      {[...Array(5)].map((_, i) => (
        <div
          key={i}
          className={cn(
            'w-1 h-1 rounded-full transition-all duration-300',
            i < difficulty
              ? 'bg-primary shadow-[0_0_4px_rgba(99,102,241,0.6)]'
              : 'bg-white/10'
          )}
        />
      ))}
    </div>
  );
};

/**
 * Custom Skill Node Component
 */
const SkillNode = ({ data, selected }) => {
  const { name, status, difficulty, xpRequired, category, onClick } = data;

  const isLocked = status === SKILL_STATUS.LOCKED;
  const isAvailable = status === SKILL_STATUS.AVAILABLE;
  const isCompleted = status === SKILL_STATUS.COMPLETED;
  const isInProgress = status === SKILL_STATUS.IN_PROGRESS;

  const handleClick = () => {
    if (!isLocked && onClick) {
      onClick(data);
    }
  };

  return (
    <>
      {/* Connection Handles */}
      <Handle
        type="target"
        position={Position.Left}
        className="!w-2 !h-2 !bg-primary/50 !border-2 !border-primary"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!w-2 !h-2 !bg-primary/50 !border-2 !border-primary"
      />

      {/* Node Content */}
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        whileHover={!isLocked ? { scale: 1.05, y: -2 } : {}}
        transition={{ duration: 0.3, ease: 'easeOut' }}
        onClick={handleClick}
        className={cn(
          'relative min-w-[180px] rounded-2xl border backdrop-blur-xl transition-all duration-300',
          'shadow-lg',
          isLocked && 'opacity-40 blur-[0.5px] cursor-not-allowed',
          isAvailable && 'border-primary/50 bg-primary/5 hover:bg-primary/10 hover:border-primary cursor-pointer hover:shadow-[0_0_20px_rgba(99,102,241,0.4)]',
          isInProgress && 'border-cyan-500/50 bg-cyan-500/5 hover:bg-cyan-500/10 cursor-pointer hover:shadow-[0_0_20px_rgba(6,182,212,0.4)]',
          isCompleted && 'border-emerald-500/50 bg-emerald-500/5 hover:bg-emerald-500/10 cursor-pointer hover:shadow-[0_0_20px_rgba(16,185,129,0.3)]',
          isLocked && 'border-white/10 bg-black/40',
          selected && 'ring-2 ring-primary ring-offset-2 ring-offset-background'
        )}
      >
        {/* Category Indicator */}
        <div className="absolute -top-1.5 -left-1.5 z-10">
          <div
            className={cn(
              'w-3 h-3 rounded-full shadow-lg',
              CATEGORY_COLORS[category] || 'bg-slate-500'
            )}
          />
        </div>

        {/* Completion Badge */}
        {isCompleted && (
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            className="absolute -top-2 -right-2 z-10"
          >
            <div className="bg-emerald-500 rounded-full p-1 shadow-lg shadow-emerald-500/50">
              <CheckCircle2 size={14} className="text-white" />
            </div>
          </motion.div>
        )}

        {/* Lock Icon */}
        {isLocked && (
          <div className="absolute -top-2 -right-2 z-10">
            <div className="bg-slate-700 rounded-full p-1 shadow-lg">
              <Lock size={14} className="text-slate-400" />
            </div>
          </div>
        )}

        {/* Content */}
        <div className="p-4 space-y-2">
          {/* Title */}
          <h3
            className={cn(
              'font-bold text-sm leading-tight transition-colors',
              isLocked ? 'text-slate-500' : 'text-white'
            )}
          >
            {name}
          </h3>

          {/* Metadata */}
          <div className="flex items-center justify-between">
            <DifficultyIndicator difficulty={difficulty || 1} />
            
            {/* XP Badge */}
            {xpRequired > 0 && (
              <div
                className={cn(
                  'flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold backdrop-blur-md border',
                  isLocked
                    ? 'bg-white/5 border-white/10 text-slate-500'
                    : 'bg-primary/10 border-primary/30 text-primary'
                )}
              >
                <Zap size={10} fill="currentColor" />
                {xpRequired}
              </div>
            )}
          </div>
        </div>

        {/* Animated Glow Effect */}
        {isAvailable && (
          <motion.div
            className="absolute inset-0 rounded-2xl bg-primary/5 blur-xl"
            animate={{
              opacity: [0.3, 0.6, 0.3],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        )}
      </motion.div>
    </>
  );
};

export default memo(SkillNode);
