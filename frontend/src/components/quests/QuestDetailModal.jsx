/**
 * SkillTree AI - Quest Detail Modal Component
 * Glassmorphic modal with blur + glow border
 * @module components/quests/QuestDetailModal
 */

import { motion, AnimatePresence } from 'framer-motion';
import { X, Code, Zap, Clock, CheckCircle2, Play } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { cn } from '../../utils/cn';

/**
 * Quest Detail Modal Component
 * @param {Object} props
 * @param {boolean} props.isOpen - Modal open state
 * @param {Function} props.onClose - Close handler
 * @param {Object} props.quest - Quest data
 * @returns {JSX.Element}
 */
function QuestDetailModal({ isOpen, onClose, quest }) {
  const navigate = useNavigate();
  if (!quest) return null;

  const handleStart = () => {
    onClose();
    navigate(quest.type === 'mcq' ? `/quests/${quest.id}/mcq` : `/editor/${quest.id}`);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <div className="fixed inset-0 z-50 flex items-center justify-center p-6 pointer-events-none">
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="glass-panel p-8 rounded-3xl border-white/10 shadow-[0_0_60px_rgba(99,102,241,0.3)] max-w-2xl w-full max-h-[80vh] overflow-y-auto pointer-events-auto relative"
            >
              {/* Close Button */}
              <button
                onClick={onClose}
                className="absolute top-6 right-6 p-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-400 hover:text-white transition-all duration-300"
              >
                <X size={20} />
              </button>

              {/* Header */}
              <div className="mb-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-3 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 shadow-[0_0_20px_rgba(99,102,241,0.3)]">
                    <Code size={24} className="text-primary" />
                  </div>
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                      {quest.type}
                    </span>
                    <h2 className="text-2xl font-black text-white">
                      {quest.title}
                    </h2>
                  </div>
                </div>

                {/* Meta Info */}
                <div className="flex items-center gap-4 mt-4">
                  <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30">
                    <Zap size={14} className="text-amber-400" fill="currentColor" />
                    <span className="text-sm font-bold text-amber-400">
                      {quest.xp_reward} XP
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/5 border border-white/10">
                    <Clock size={14} className="text-slate-400" />
                    <span className="text-sm font-medium text-slate-400">
                      {quest.estimated_minutes} min
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    {[...Array(5)].map((_, i) => (
                      <div
                        key={i}
                        className={cn(
                          "w-1.5 h-1.5 rounded-full",
                          i < Math.round(quest.difficulty_multiplier)
                            ? "bg-primary shadow-[0_0_8px_rgba(99,102,241,0.6)]"
                            : "bg-white/10"
                        )}
                      />
                    ))}
                  </div>
                </div>
              </div>

              {/* Description */}
              <div className="mb-6">
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-3">
                  Description
                </h3>
                <p className="text-slate-300 leading-relaxed">
                  {quest.description}
                </p>
              </div>

              {/* Starter Code (for coding/debugging quests) */}
              {quest.type !== 'mcq' && quest.starter_code && (
                <div className="mb-6">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-3">
                    Starter Code
                  </h3>
                  <div className="bg-black/40 border border-white/10 rounded-xl p-4 overflow-x-auto">
                    <pre className="text-sm text-slate-300 font-mono">
                      <code>{quest.starter_code}</code>
                    </pre>
                  </div>
                </div>
              )}

              {/* Test Cases Count */}
              {quest.test_cases && quest.test_cases.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-3">
                    Test Cases
                  </h3>
                  <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-white/5 border border-white/10">
                    <CheckCircle2 size={16} className="text-emerald-400" />
                    <span className="text-sm font-medium text-slate-300">
                      {quest.test_cases.length} test case{quest.test_cases.length !== 1 ? 's' : ''} to pass
                    </span>
                  </div>
                </div>
              )}

              {/* Action Button */}
              <button
                onClick={handleStart}
                className="w-full py-4 flex items-center justify-center gap-2 bg-gradient-to-r from-primary to-accent text-white font-bold uppercase tracking-widest text-xs rounded-xl shadow-[0_10px_30px_rgba(99,102,241,0.3)] hover:shadow-[0_10px_40px_rgba(99,102,241,0.5)] hover:scale-[1.02] active:scale-[0.98] transition-all duration-300"
              >
                <Play size={14} />
                Start Quest
              </button>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}

export default QuestDetailModal;
