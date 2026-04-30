/**
 * SkillTree AI - Quest Page
 * Quest browsing with immersive glassmorphic design
 * @module pages/QuestPage
 */

import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, AlertCircle, TrendingUp, ArrowUpDown } from 'lucide-react';
import api from '../api/api';
import MainLayout from '../components/layout/MainLayout';
import FilterBar from '../components/quests/FilterBar';
import QuestList from '../components/quests/QuestList';
import QuestDetailModal from '../components/quests/QuestDetailModal';
import QuestListSkeleton from '../components/quests/QuestSkeleton';
import { cn } from '../utils/cn';

const SORT_OPTIONS = [
  { value: 'xp', label: 'XP Reward' },
  { value: 'difficulty', label: 'Difficulty' },
  { value: 'time', label: 'Est. Time' },
];

/**
 * Quest Page Component
 * @returns {JSX.Element}
 */
function QuestPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [quests, setQuests] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    type: null,
    difficulty: null,
    status: null,
    unlocked: false,
  });
  const [sortBy, setSortBy] = useState('xp');
  const [selectedQuest, setSelectedQuest] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const skillId = searchParams.get('skill_id');

  // Fetch quests
  useEffect(() => {
    fetchQuests();
  }, [filters, skillId]);

  const fetchQuests = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const params = {};
      if (skillId) params.skill_id = skillId;
      if (filters.type) params.type = filters.type;
      if (filters.difficulty) params.difficulty = filters.difficulty;
      if (filters.status) params.status = filters.status;
      if (filters.unlocked) params.unlocked = 'true';

      const response = await api.get('/api/quests/', { params });
      
      // Handle paginated response (DRF pagination wraps results)
      const questData = response.data.results 
        ? response.data.results 
        : Array.isArray(response.data) 
          ? response.data 
          : [];
      
      setQuests(questData);
    } catch (err) {
      console.error('Failed to fetch quests:', err);
      setError(err.response?.data?.detail || 'Failed to load quests. Please try again.');
      setQuests([]); // Set empty array on error
    } finally {
      setIsLoading(false);
    }
  };

  // Sort quests - ensure quests is an array
  const sortedQuests = Array.isArray(quests) ? [...quests].sort((a, b) => {
    switch (sortBy) {
      case 'xp':
        return b.xp_reward - a.xp_reward;
      case 'difficulty':
        return b.difficulty_multiplier - a.difficulty_multiplier;
      case 'time':
        return a.estimated_minutes - b.estimated_minutes;
      default:
        return 0;
    }
  }) : [];

  // Handle quest click
  const handleQuestClick = (quest) => {
    setSelectedQuest(quest);
    setIsModalOpen(true);
  };

  // Handle modal close
  const handleModalClose = () => {
    setIsModalOpen(false);
    setTimeout(() => setSelectedQuest(null), 300);
  };

  // Handle retry
  const handleRetry = () => {
    fetchQuests();
  };

  return (
    <MainLayout>
      <div className="min-h-screen bg-background p-6 pb-24">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="p-3 rounded-2xl bg-gradient-to-br from-primary/20 to-accent/20 shadow-[0_0_30px_rgba(99,102,241,0.3)]">
                <Sparkles size={28} className="text-primary" />
              </div>
              <div>
                <h1 className="text-4xl font-black tracking-tighter text-white">
                  QUEST <span className="premium-gradient-text">BOARD</span>
                </h1>
                <p className="text-slate-400 font-medium text-sm uppercase tracking-wide">
                  Complete missions to earn XP and unlock skills
                </p>
              </div>
            </div>

            {/* Stats Bar */}
            <div className="glass-panel p-4 rounded-2xl flex items-center justify-between">
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-2">
                  <TrendingUp size={16} className="text-emerald-400" />
                  <span className="text-sm font-bold text-slate-300">
                    {Array.isArray(quests) ? quests.length : 0} Quest{(Array.isArray(quests) ? quests.length : 0) !== 1 ? 's' : ''} Available
                  </span>
                </div>
                <div className="w-px h-6 bg-white/10" />
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-slate-300">
                    {Array.isArray(quests) ? quests.filter(q => q.status === 'passed').length : 0} Completed
                  </span>
                </div>
              </div>

              {/* Sort Dropdown */}
              <div className="flex items-center gap-2">
                <ArrowUpDown size={14} className="text-slate-500" />
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs font-bold text-slate-300 outline-none focus:border-primary/50 transition-all duration-300 cursor-pointer"
                >
                  {SORT_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      Sort by {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </motion.div>

          {/* Filter Bar */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <FilterBar filters={filters} onFilterChange={setFilters} />
          </motion.div>

          {/* Content */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <AnimatePresence mode="wait">
              {isLoading ? (
                <motion.div
                  key="loading"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <QuestListSkeleton count={6} />
                </motion.div>
              ) : error ? (
                <motion.div
                  key="error"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="glass-panel p-12 rounded-2xl text-center"
                >
                  <AlertCircle size={48} className="text-accent mx-auto mb-4" />
                  <h3 className="text-xl font-bold text-white mb-2">
                    Failed to Load Quests
                  </h3>
                  <p className="text-slate-400 mb-6">{error}</p>
                  <button
                    onClick={handleRetry}
                    className="auth-btn-primary inline-block px-8"
                  >
                    Retry
                  </button>
                </motion.div>
              ) : (
                <motion.div
                  key="content"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <QuestList quests={sortedQuests} onQuestClick={handleQuestClick} />
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>
      </div>

      {/* Quest Detail Modal */}
      <QuestDetailModal
        isOpen={isModalOpen}
        onClose={handleModalClose}
        quest={selectedQuest}
      />
    </MainLayout>
  );
}

export default QuestPage;