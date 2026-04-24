import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Code, Zap, BarChart3, Clock } from 'lucide-react';

const Fragment = ({ children, delay, x, y, rotate }) => (
  <motion.div
    initial={{ opacity: 0, scale: 0, x: 0, y: 0, rotate: 0 }}
    animate={{ opacity: 1, scale: 1, x, y, rotate }}
    exit={{ opacity: 0, scale: 0, x: 0, y: 0, rotate: 0 }}
    transition={{ type: "spring", stiffness: 100, damping: 15, delay }}
    className="absolute glass-card p-6 rounded-2xl w-64 pointer-events-auto"
  >
    {children}
  </motion.div>
);

const ExplodingCard = ({ isOpen, onClose, data }) => {
  if (!data) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center pointer-events-none">
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={onClose}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm pointer-events-auto"
            />

            {/* Central Node Hub */}
            <motion.div
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              exit={{ scale: 0, rotate: 180 }}
              className="relative w-32 h-32 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-[0_0_50px_rgba(99,102,241,0.8)] z-10 pointer-events-auto"
            >
              <Zap size={48} className="text-white fill-white" />
              <button 
                onClick={onClose}
                className="absolute -top-4 -right-4 w-8 h-8 rounded-full bg-white text-black flex items-center justify-center hover:bg-accent hover:text-white transition-colors"
              >
                <X size={16} />
              </button>
            </motion.div>

            {/* Fragments */}
            <Fragment x={-300} y={-150} rotate={-5} delay={0.1}>
              <div className="flex items-center space-x-3 mb-4 text-primary">
                <Code size={20} />
                <h3 className="font-bold uppercase tracking-widest text-xs">Overview</h3>
              </div>
              <p className="text-sm text-slate-300 font-light">{data.description}</p>
            </Fragment>

            <Fragment x={300} y={-100} rotate={5} delay={0.2}>
              <div className="flex items-center space-x-3 mb-4 text-accent">
                <Clock size={20} />
                <h3 className="font-bold uppercase tracking-widest text-xs">Quest Details</h3>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500 uppercase">Estimated Time</span>
                  <span className="text-white">45 MINS</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500 uppercase">Complexity</span>
                  <span className="text-white">TIER 3</span>
                </div>
              </div>
            </Fragment>

            <Fragment x={-280} y={150} rotate={3} delay={0.3}>
              <div className="flex items-center space-x-3 mb-4 text-emerald-400">
                <BarChart3 size={20} />
                <h3 className="font-bold uppercase tracking-widest text-xs">Rewards</h3>
              </div>
              <div className="text-3xl font-black text-white">+500 XP</div>
              <span className="text-[10px] text-slate-500 uppercase font-bold">Base Cognitive Multiplier</span>
            </Fragment>

            <Fragment x={280} y={180} rotate={-3} delay={0.4}>
              <button className="w-full py-4 bg-white text-black font-black uppercase tracking-tighter hover:bg-primary hover:text-white transition-all duration-300 rounded-lg">
                INITIALIZE QUEST
              </button>
            </Fragment>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ExplodingCard;
