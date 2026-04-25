/**
 * SkillTree AI - Filter Bar Component
 * Glass chips for filtering quests
 * @module components/quests/FilterBar
 */

import { motion } from 'framer-motion';
import { Bug, Code, BookOpen, X } from 'lucide-react';
import { cn } from '../../utils/cn';

const TYPE_OPTIONS = [
  { value: 'all', label: 'All Types', icon: null },
  { value: 'coding', label: 'Coding', icon: Code },
  { value: 'debugging', label: 'Debug', icon: Bug },
  { value: 'mcq', label: 'MCQ', icon: BookOpen },
];

const DIFFICULTY_OPTIONS = [
  { value: 'all', label: 'All Levels' },
  { value: '1', label: 'Level 1' },
  { value: '2', label: 'Level 2' },
  { value: '3', label: 'Level 3' },
  { value: '4', label: 'Level 4' },
  { value: '5', label: 'Level 5' },
];

const STATUS_OPTIONS = [
  { value: 'all', label: 'All Status' },
  { value: 'not_started', label: 'Not Started' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'passed', label: 'Passed' },
];

/**
 * Filter Bar Component
 * @param {Object} props
 * @param {Object} props.filters - Current filter values
 * @param {Function} props.onFilterChange - Filter change handler
 * @returns {JSX.Element}
 */
function FilterBar({ filters, onFilterChange }) {
  const handleTypeChange = (type) => {
    onFilterChange({ ...filters, type: type === 'all' ? null : type });
  };

  const handleDifficultyChange = (difficulty) => {
    onFilterChange({ ...filters, difficulty: difficulty === 'all' ? null : difficulty });
  };

  const handleStatusChange = (status) => {
    onFilterChange({ ...filters, status: status === 'all' ? null : status });
  };

  const handleClearFilters = () => {
    onFilterChange({ type: null, difficulty: null, status: null });
  };

  const hasActiveFilters = filters.type || filters.difficulty || filters.status;

  return (
    <div className="glass-panel p-6 rounded-2xl mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400">
          Filters
        </h3>
        {hasActiveFilters && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            onClick={handleClearFilters}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-bold text-slate-400 hover:text-white transition-all duration-300"
          >
            <X size={12} />
            Clear
          </motion.button>
        )}
      </div>

      <div className="space-y-4">
        {/* Type Filter */}
        <div>
          <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">
            Quest Type
          </label>
          <div className="flex flex-wrap gap-2">
            {TYPE_OPTIONS.map((option) => {
              const Icon = option.icon;
              const isActive = filters.type === option.value || (!filters.type && option.value === 'all');
              
              return (
                <motion.button
                  key={option.value}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleTypeChange(option.value)}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-xs uppercase tracking-wider transition-all duration-300 border",
                    isActive
                      ? "bg-primary/20 border-primary/50 text-primary shadow-[0_0_20px_rgba(99,102,241,0.3)]"
                      : "bg-white/5 border-white/10 text-slate-400 hover:bg-white/10 hover:text-white"
                  )}
                >
                  {Icon && <Icon size={14} />}
                  {option.label}
                </motion.button>
              );
            })}
          </div>
        </div>

        {/* Difficulty Filter */}
        <div>
          <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">
            Difficulty
          </label>
          <div className="flex flex-wrap gap-2">
            {DIFFICULTY_OPTIONS.map((option) => {
              const isActive = filters.difficulty === option.value || (!filters.difficulty && option.value === 'all');
              
              return (
                <motion.button
                  key={option.value}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleDifficultyChange(option.value)}
                  className={cn(
                    "px-4 py-2 rounded-xl font-bold text-xs uppercase tracking-wider transition-all duration-300 border",
                    isActive
                      ? "bg-primary/20 border-primary/50 text-primary shadow-[0_0_20px_rgba(99,102,241,0.3)]"
                      : "bg-white/5 border-white/10 text-slate-400 hover:bg-white/10 hover:text-white"
                  )}
                >
                  {option.label}
                </motion.button>
              );
            })}
          </div>
        </div>

        {/* Status Filter */}
        <div>
          <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">
            Status
          </label>
          <div className="flex flex-wrap gap-2">
            {STATUS_OPTIONS.map((option) => {
              const isActive = filters.status === option.value || (!filters.status && option.value === 'all');
              
              return (
                <motion.button
                  key={option.value}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleStatusChange(option.value)}
                  className={cn(
                    "px-4 py-2 rounded-xl font-bold text-xs uppercase tracking-wider transition-all duration-300 border",
                    isActive
                      ? "bg-primary/20 border-primary/50 text-primary shadow-[0_0_20px_rgba(99,102,241,0.3)]"
                      : "bg-white/5 border-white/10 text-slate-400 hover:bg-white/10 hover:text-white"
                  )}
                >
                  {option.label}
                </motion.button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

export default FilterBar;
