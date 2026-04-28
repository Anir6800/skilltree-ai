/**
 * SkillTree AI - Focus Mode Toggle
 * Moon icon button to toggle focus mode globally
 * Positioned top-right with tooltip
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Moon, Sun } from 'lucide-react';
import useUIStore from '../store/uiStore';
import './FocusModeToggle.css';

const FocusModeToggle = () => {
  const { focusMode, toggleFocusMode } = useUIStore();
  const [showTooltip, setShowTooltip] = React.useState(false);

  const handleToggle = () => {
    toggleFocusMode();
  };

  return (
    <div className="focus-mode-toggle-container">
      <motion.button
        className={`focus-mode-toggle-btn ${focusMode ? 'active' : ''}`}
        onClick={handleToggle}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        aria-label={focusMode ? 'Exit Focus Mode' : 'Enter Focus Mode'}
      >
        <motion.div
          initial={false}
          animate={{ rotate: focusMode ? 180 : 0 }}
          transition={{ duration: 0.3 }}
        >
          {focusMode ? (
            <Sun size={20} className="text-amber-400" />
          ) : (
            <Moon size={20} className="text-slate-400" />
          )}
        </motion.div>
      </motion.button>

      {/* Tooltip */}
      <motion.div
        className="focus-mode-tooltip"
        initial={{ opacity: 0, y: 10 }}
        animate={showTooltip ? { opacity: 1, y: 0 } : { opacity: 0, y: 10 }}
        transition={{ duration: 0.2 }}
        pointerEvents={showTooltip ? 'auto' : 'none'}
      >
        {focusMode ? 'Exit Focus Mode' : 'Focus Mode — hide XP & ranks'}
      </motion.div>
    </div>
  );
};

export default FocusModeToggle;
