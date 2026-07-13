/**
 * SkillTree AI - Onboarding Page
 * Immersive multi-step wizard for user personalization
 * Design: Matches Login/Dashboard/Quests/Editor/Mentor glassmorphism theme
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Briefcase, Zap, TrendingUp, Heart, ArrowRight, ArrowLeft,
  Code, Database, Server, Globe, Brain, Sparkles, Target, CheckCircle2,
  AlertTriangle, RefreshCw, Gamepad2
} from 'lucide-react';
import api from '../api/api';
import { cn } from '../utils/cn';
import DinoGame from '../components/DinoGame';
import SnakeGame from '../components/SnakeGame';
import MemoryGame from '../components/MemoryGame';

// ─── Constants ────────────────────────────────────────────────────────────────

const GOALS = [
  {
    id: 'job_prep',
    label: 'Job Preparation',
    icon: Briefcase,
    description: 'Land your dream developer role',
    color: 'from-blue-500/20 to-cyan-500/20',
    glow: 'shadow-[0_0_30px_rgba(59,130,246,0.3)]'
  },
  {
    id: 'interview',
    label: 'Interview Cracker',
    icon: Zap,
    description: 'Ace technical interviews',
    color: 'from-amber-500/20 to-orange-500/20',
    glow: 'shadow-[0_0_30px_rgba(245,158,11,0.3)]'
  },
  {
    id: 'upskill',
    label: 'Upskilling',
    icon: TrendingUp,
    description: 'Level up your skills',
    color: 'from-emerald-500/20 to-green-500/20',
    glow: 'shadow-[0_0_30px_rgba(16,185,129,0.3)]'
  },
  {
    id: 'passion',
    label: 'Passion Project',
    icon: Heart,
    description: 'Build what you love',
    color: 'from-pink-500/20 to-rose-500/20',
    glow: 'shadow-[0_0_30px_rgba(236,72,153,0.3)]'
  },
];

const CATEGORIES = [
  { id: 'algorithms', label: 'Algorithms', icon: Code },
  { id: 'ds', label: 'Data Structures', icon: Database },
  { id: 'systems', label: 'Systems', icon: Server },
  { id: 'webdev', label: 'Web Dev', icon: Globe },
  { id: 'aiml', label: 'AI/ML', icon: Brain },
];

const LEVELS = ['beginner', 'intermediate', 'advanced'];

const INTERESTS = [
  'Arrays', 'Strings', 'Linked Lists', 'Trees', 'Graphs',
  'Sorting', 'Searching', 'Dynamic Programming', 'Greedy',
  'Backtracking', 'Recursion', 'Hash Tables', 'Stacks', 'Queues',
  'Binary Search', 'DFS', 'BFS', 'React', 'Node.js', 'Python',
  'JavaScript', 'TypeScript', 'SQL', 'MongoDB', 'Docker',
  'Kubernetes', 'AWS', 'Machine Learning', 'Deep Learning', 'NLP'
];

const QUICK_HOURS = [2, 5, 10, 20];

// Dynamic role suggestions — adapt step 2 to the goal chosen in step 1
const ROLE_SUGGESTIONS = {
  job_prep: ['Full Stack Developer', 'Backend Developer', 'Frontend Developer', 'Data Scientist'],
  interview: ['SDE at Big Tech', 'Backend Engineer', 'Full Stack Engineer', 'ML Engineer'],
  upskill: ['Senior System Architect', 'DevOps Engineer', 'Cloud Engineer', 'Tech Lead'],
  passion: ['Indie Hacker', 'Game Developer', 'Open Source Contributor', 'AI App Builder'],
};

// Interest → category, used to suggest interests based on step-3 self-ratings
const INTEREST_CATEGORY = {
  Arrays: 'ds', Strings: 'ds', 'Linked Lists': 'ds', Trees: 'ds', Graphs: 'ds',
  'Hash Tables': 'ds', Stacks: 'ds', Queues: 'ds',
  Sorting: 'algorithms', Searching: 'algorithms', 'Dynamic Programming': 'algorithms',
  Greedy: 'algorithms', Backtracking: 'algorithms', Recursion: 'algorithms',
  'Binary Search': 'algorithms', DFS: 'algorithms', BFS: 'algorithms',
  React: 'webdev', 'Node.js': 'webdev', JavaScript: 'webdev', TypeScript: 'webdev',
  SQL: 'webdev', MongoDB: 'webdev',
  Docker: 'systems', Kubernetes: 'systems', AWS: 'systems',
  Python: 'aiml', 'Machine Learning': 'aiml', 'Deep Learning': 'aiml', NLP: 'aiml',
};

// ─── Sub-components ───────────────────────────────────────────────────────────

function ProgressBar({ currentStep, totalSteps }) {
  const progress = (currentStep / totalSteps) * 100;
  
  return (
    <div className="w-full max-w-2xl mx-auto mb-8">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-bold uppercase tracking-widest text-slate-400">
          Step {currentStep} of {totalSteps}
        </span>
        <span className="text-xs font-bold text-red-400">
          {Math.round(progress)}%
        </span>
      </div>
      <div className="h-2 bg-white/5 rounded-full overflow-hidden border border-white/10">
        <motion.div
          className="h-full bg-gradient-to-r from-red-600 to-red-800"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      </div>
    </div>
  );
}

function GoalCard({ goal, selected, onClick }) {
  const Icon = goal.icon;
  
  return (
    <motion.button
      whileHover={{ y: -8, scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={cn(
        'relative p-6 rounded-2xl transition-all duration-300 text-left w-full',
        'glass-card border',
        selected
          ? `border-red-500/60 ${goal.glow}`
          : 'border-white/10 hover:border-red-500/30'
      )}
    >
      {/* Glow effect */}
      {selected && (
        <motion.div
          className="absolute inset-0 bg-red-500/10 rounded-2xl blur-xl"
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
      
      {/* Content */}
      <div className="relative z-10">
        <div className={cn(
          'p-3 rounded-xl mb-4 inline-block bg-gradient-to-br',
          goal.color
        )}>
          <Icon size={28} className={selected ? 'text-red-400' : 'text-slate-300'} />
        </div>
        <h3 className={cn(
          'text-lg font-bold mb-2 transition-colors duration-300',
          selected ? 'text-red-400' : 'text-white'
        )}>
          {goal.label}
        </h3>
        <p className="text-sm text-slate-400">
          {goal.description}
        </p>
      </div>
      
      {/* Selected indicator */}
      {selected && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="absolute top-4 right-4 w-6 h-6 rounded-full bg-red-500 flex items-center justify-center"
        >
          <CheckCircle2 size={16} className="text-white" />
        </motion.div>
      )}
    </motion.button>
  );
}

function CategoryLevel({ category, level, onSelect }) {
  const Icon = category.icon;
  
  return (
    <div className="glass-card p-4 rounded-xl">
      <div className="flex items-center gap-3 mb-3">
        <div className="p-2 rounded-lg bg-red-500/15">
          <Icon size={18} className="text-red-400" />
        </div>
        <span className="text-sm font-bold text-white">{category.label}</span>
      </div>
      
      <div className="flex gap-2">
        {LEVELS.map((lvl) => (
          <button
            key={lvl}
            onClick={() => onSelect(category.id, lvl)}
            className={cn(
              'flex-1 px-3 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all duration-200',
              level === lvl
                ? 'bg-red-500/25 border-2 border-red-500 text-red-400 shadow-[0_0_12px_rgba(255, 45, 45, 0.4)]'
                : 'bg-white/5 border border-white/10 text-slate-400 hover:bg-white/10 hover:text-white'
            )}
          >
            {lvl.slice(0, 3)}
          </button>
        ))}
      </div>
    </div>
  );
}

function InterestChip({ interest, selected, onClick }) {
  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className={cn(
        'px-4 py-2 rounded-xl text-sm font-bold transition-all duration-200',
        selected
          ? 'bg-red-500/25 border-2 border-red-500 text-red-400 shadow-[0_0_12px_rgba(255, 45, 45, 0.4)]'
          : 'bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10 hover:border-red-500/30 hover:text-red-400'
      )}
    >
      {interest}
    </motion.button>
  );
}

function formatEta(seconds) {
  if (seconds == null || seconds <= 0) return null;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `~${m}m ${String(s).padStart(2, '0')}s remaining` : `~${s}s remaining`;
}

const MICRO_GAMES = [
  { id: 'dino', label: 'Dino Run', hint: 'Space or tap to jump', Game: DinoGame },
  { id: 'snake', label: 'Snake', hint: 'Arrow keys / WASD to steer', Game: SnakeGame },
  { id: 'memory', label: 'Memory', hint: 'Find all the matching pairs', Game: MemoryGame },
];

function GenerationScreen({ gen, onRetry }) {
  const [gameId, setGameId] = useState('dino');
  const { Game, hint } = MICRO_GAMES.find((g) => g.id === gameId) || MICRO_GAMES[0];

  const percent = gen?.percent ?? 0;
  const failed = gen?.status === 'failed';
  const ready = gen?.status === 'ready';
  const eta = formatEta(gen?.eta_seconds);
  const stage = ready
    ? 'Your path is ready! 🎉'
    : (gen?.stage || 'Queued — warming up the AI...');

  return (
    <div className="fixed inset-0 bg-[#050505] overflow-y-auto">
      {/* Animated background */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-red-600/10 blur-[120px] rounded-full animate-pulse" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-red-900/10 blur-[120px] rounded-full animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      <div className="relative z-10 flex flex-col items-center max-w-2xl mx-auto px-6 py-12 text-center">
        <motion.div
          className="inline-block p-5 rounded-3xl bg-gradient-to-br from-red-500/20 to-red-800/20 mb-6"
          animate={failed ? {} : { scale: [1, 1.1, 1], rotate: [0, 5, -5, 0] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        >
          {failed
            ? <AlertTriangle size={44} className="text-red-400" />
            : <Sparkles size={44} className="text-red-400 drop-shadow-[0_0_20px_rgba(255,45,45,0.8)]" />}
        </motion.div>

        <h2 className="text-3xl font-black text-white mb-2">
          {failed ? 'Generation Hit a Snag' : 'Personalizing Your Plan'}
        </h2>
        {!failed && !ready && (
          <p className="text-sm text-slate-500 mb-4">
            This takes a few minutes — play our micro games while you wait 🎮
          </p>
        )}

        {failed ? (
          <>
            <p className="text-slate-300 mb-2">
              The AI couldn't finish your roadmap. Nothing is lost — it resumes
              from where it stopped.
            </p>
            {gen?.error && (
              <p className="text-xs text-red-400/80 font-mono mb-4 max-w-md break-words">{gen.error}</p>
            )}
            <button
              onClick={onRetry}
              className="flex items-center gap-2 px-8 py-3 rounded-xl font-bold bg-gradient-to-r from-red-600 to-red-800 text-white hover:shadow-[0_0_20px_rgba(255,45,45,0.4)] transition-all duration-200 mb-8"
            >
              <RefreshCw size={18} />
              Resume Generation
            </button>
          </>
        ) : (
          <>
            {/* Node counter — the headline number */}
            {gen?.total_nodes > 0 && (
              <p className="mb-4">
                <span className="text-4xl font-black text-red-400">{gen.nodes_completed}</span>
                <span className="text-2xl font-black text-slate-500"> / {gen.total_nodes}</span>
                <span className="block text-xs font-bold uppercase tracking-widest text-slate-400 mt-1">
                  nodes generated
                </span>
              </p>
            )}

            <div className="w-full max-w-md mb-2">
              <div className="h-3 bg-white/5 rounded-full overflow-hidden border border-white/10 mb-3">
                <motion.div
                  className="h-full bg-gradient-to-r from-red-600 via-red-400 to-red-600 bg-[length:200%_100%]"
                  animate={{
                    width: `${Math.max(percent, 3)}%`,
                    backgroundPosition: ['0% 0%', '100% 0%'],
                  }}
                  transition={{
                    width: { duration: 0.3 },
                    backgroundPosition: { duration: 2, repeat: Infinity, ease: 'linear' },
                  }}
                />
              </div>
              <div className="flex items-center justify-between text-sm font-bold">
                <span className="text-red-400">{Math.round(percent)}%</span>
                {eta && <span className="text-slate-500">{eta}</span>}
              </div>
            </div>

            {/* Current step */}
            <AnimatePresence mode="wait">
              <motion.p
                key={stage}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                className="text-sm text-slate-400 font-mono"
              >
                {stage}
              </motion.p>
            </AnimatePresence>
          </>
        )}

        {!ready && (
          <div className="w-full mt-8">
            <div className="flex items-center justify-center gap-2 mb-3 text-slate-400 text-sm font-bold uppercase tracking-widest">
              <Gamepad2 size={16} className="text-red-400" />
              Micro games
            </div>
            <div className="flex justify-center gap-2 mb-4">
              {MICRO_GAMES.map((g) => (
                <button
                  key={g.id}
                  onClick={() => setGameId(g.id)}
                  className={cn(
                    'px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider transition-all duration-200',
                    gameId === g.id
                      ? 'bg-red-500/25 border-2 border-red-500 text-red-400'
                      : 'bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10'
                  )}
                >
                  {g.label}
                </button>
              ))}
            </div>
            <Game />
            <p className="text-center text-xs text-slate-500 mt-3">{hint}</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

function OnboardingPage() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [isGenerating, setIsGenerating] = useState(false);
  const [genInfo, setGenInfo] = useState(null);
  const pollRef = useRef(null);
  const treeIdRef = useRef(null);

  // Form state
  const [formData, setFormData] = useState({
    primary_goal: '',
    target_role: '',
    experience_years: 0,
    category_levels: {},
    selected_interests: [],
    weekly_hours: 5,
  });

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  // Poll real generation progress. Until the tree exists we ask the onboarding
  // status endpoint; once we know the tree_id we poll the tree status endpoint
  // (richer: ETA + server-side auto-resume of stalled generations).
  const pollOnce = useCallback(async () => {
    try {
      if (!treeIdRef.current) {
        const { data } = await api.get('/api/onboarding/status/');
        const gen = data.generation;
        if (gen?.tree_id) {
          treeIdRef.current = gen.tree_id;
          setGenInfo(gen);
        }
        return;
      }
      const { data } = await api.get(`/api/skills/generated/${treeIdRef.current}/status/`);
      setGenInfo(data);
      if (data.status === 'ready') {
        stopPolling();
        setTimeout(() => navigate('/skills'), 1500);
      } else if (data.status === 'failed') {
        stopPolling();
      }
    } catch (error) {
      console.error('Generation poll failed:', error);
    }
  }, [navigate, stopPolling]);

  const startPolling = useCallback(() => {
    setIsGenerating(true);
    if (pollRef.current) return;
    pollOnce();
    pollRef.current = setInterval(pollOnce, 2500);
  }, [pollOnce]);

  useEffect(() => stopPolling, [stopPolling]);

  // Check onboarding state on mount: resume the loading screen after a
  // refresh while the tree is still generating (or failed), otherwise leave.
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await api.get('/api/onboarding/status/');
        if (response.data.completed) {
          const gen = response.data.generation;
          if (gen && gen.status !== 'ready') {
            treeIdRef.current = gen.tree_id;
            setGenInfo(gen);
            startPolling();
          } else {
            navigate('/dashboard');
          }
        }
      } catch (error) {
        console.error('Failed to check onboarding status:', error);
      }
    };
    checkStatus();
  }, [navigate, startPolling]);
  
  const handleNext = useCallback(() => {
    setCurrentStep((prev) => Math.min(prev + 1, 6));
  }, []);
  
  const handleBack = useCallback(() => {
    setCurrentStep((prev) => Math.max(prev - 1, 0));
  }, []);
  
  const handleGoalSelect = useCallback((goalId) => {
    setFormData((prev) => ({ ...prev, primary_goal: goalId }));
  }, []);
  
  const handleCategoryLevel = useCallback((category, level) => {
    setFormData((prev) => ({
      ...prev,
      category_levels: {
        ...prev.category_levels,
        [category]: level,
      },
    }));
  }, []);
  
  const handleInterestToggle = useCallback((interest) => {
    setFormData((prev) => {
      const interests = prev.selected_interests.includes(interest)
        ? prev.selected_interests.filter((i) => i !== interest)
        : [...prev.selected_interests, interest];
      return { ...prev, selected_interests: interests };
    });
  }, []);
  
  const handleSubmit = useCallback(async () => {
    setIsGenerating(true);
    setGenInfo(null);

    try {
      await api.post('/api/onboarding/submit/', formData);
      startPolling();
    } catch (error) {
      console.error('Onboarding submission failed:', error);
      setIsGenerating(false);
    }
  }, [formData, startPolling]);

  const handleRetry = useCallback(async () => {
    if (!treeIdRef.current) return;
    try {
      await api.post(`/api/skills/generated/${treeIdRef.current}/resume/`);
      setGenInfo((g) => (g ? { ...g, status: 'generating', error: null } : g));
      startPolling();
    } catch (error) {
      console.error('Failed to resume generation:', error);
    }
  }, [startPolling]);
  
  // Validation
  const canProceed = useCallback(() => {
    switch (currentStep) {
      case 0:
        return true; // Welcome
      case 1:
        return formData.primary_goal !== '';
      case 2:
        return formData.target_role.trim() !== '';
      case 3:
        return Object.keys(formData.category_levels).length === 5;
      case 4:
        return formData.selected_interests.length >= 2;
      case 5:
        return formData.weekly_hours >= 1;
      default:
        return false;
    }
  }, [currentStep, formData]);
  
  if (isGenerating) {
    return <GenerationScreen gen={genInfo} onRetry={handleRetry} />;
  }
  
  return (
    <div className="fixed inset-0 bg-[#050505] text-white overflow-hidden">
      {/* Ambient glows */}
      <div className="fixed inset-0 pointer-events-none -z-10">
        <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-red-600/10 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-red-900/10 blur-[120px] rounded-full" />
      </div>
      
      <div className="h-full overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto py-12">
          {/* Progress bar */}
          {currentStep > 0 && (
            <ProgressBar currentStep={currentStep} totalSteps={6} />
          )}
          
          {/* Steps */}
          <AnimatePresence mode="wait">
            {/* Step 0: Welcome */}
            {currentStep === 0 && (
              <motion.div
                key="welcome"
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -20, scale: 0.95 }}
                transition={{ duration: 0.4 }}
                className="text-center"
              >
                <motion.div
                  className="inline-block p-6 rounded-3xl bg-gradient-to-br from-red-500/20 to-red-800/20 mb-8"
                  animate={{
                    scale: [1, 1.05, 1],
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: 'easeInOut',
                  }}
                >
                  <Target size={64} className="text-red-400 drop-shadow-[0_0_20px_rgba(255, 45, 45, 0.8)]" />
                </motion.div>
                
                <h1 className="text-5xl font-black mb-4">
                  Welcome to <span className="text-transparent bg-clip-text bg-gradient-to-r from-red-500 to-white">SkillTree AI</span>
                </h1>
                
                <p className="text-xl text-slate-300 mb-8 max-w-2xl mx-auto">
                  Let's personalize your learning journey. We'll create a custom path
                  tailored to your goals, experience, and interests.
                </p>
                
                <button
                  onClick={handleNext}
                  className="bg-red-600 hover:bg-red-500 text-white font-bold uppercase tracking-widest rounded-xl shadow-[0_10px_30px_rgba(255,45,45,0.25)] hover:shadow-[0_10px_40px_rgba(255,45,45,0.4)] transition-all duration-300 inline-flex items-center gap-2 px-8 py-4 text-lg"
                >
                  Let's Get Started
                  <ArrowRight size={20} />
                </button>
                
                <button
                  onClick={() => navigate('/dashboard')}
                  className="block mx-auto mt-4 text-sm text-slate-500 hover:text-slate-300 transition-colors"
                >
                  Skip for now
                </button>
              </motion.div>
            )}
            
            {/* Step 1: Goal Selection */}
            {currentStep === 1 && (
              <motion.div
                key="goal"
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                transition={{ duration: 0.3 }}
              >
                <h2 className="text-3xl font-black text-center mb-3">
                  What's Your Primary Goal?
                </h2>
                <p className="text-center text-slate-400 mb-8">
                  Choose the path that resonates with you
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl mx-auto">
                  {GOALS.map((goal) => (
                    <GoalCard
                      key={goal.id}
                      goal={goal}
                      selected={formData.primary_goal === goal.id}
                      onClick={() => handleGoalSelect(goal.id)}
                    />
                  ))}
                </div>
              </motion.div>
            )}
            
            {/* Step 2: Target Role */}
            {currentStep === 2 && (
              <motion.div
                key="role"
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                transition={{ duration: 0.3 }}
                className="max-w-2xl mx-auto"
              >
                <h2 className="text-3xl font-black text-center mb-3">
                  What's Your Target Role?
                </h2>
                <p className="text-center text-slate-400 mb-8">
                  Tell us what you're aiming for
                </p>
                
                <div className="glass-panel p-8 rounded-3xl">
                  <input
                    type="text"
                    value={formData.target_role}
                    onChange={(e) => setFormData((prev) => ({ ...prev, target_role: e.target.value }))}
                    placeholder="e.g., Full Stack Developer, Data Scientist, ML Engineer"
                    className="w-full px-6 py-4 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 text-lg focus:outline-none focus:border-red-500/50 focus:bg-white/10 transition-all duration-300"
                  />

                  {/* Dynamic suggestions based on the goal picked in step 1 */}
                  <div className="flex flex-wrap gap-2 mt-4">
                    {(ROLE_SUGGESTIONS[formData.primary_goal] || ROLE_SUGGESTIONS.upskill).map((role) => (
                      <button
                        key={role}
                        onClick={() => setFormData((prev) => ({ ...prev, target_role: role }))}
                        className={cn(
                          'px-3 py-1.5 rounded-lg text-xs font-bold transition-all duration-200',
                          formData.target_role === role
                            ? 'bg-red-500/25 border border-red-500 text-red-400'
                            : 'bg-white/5 border border-white/10 text-slate-400 hover:text-red-400 hover:border-red-500/30'
                        )}
                      >
                        {role}
                      </button>
                    ))}
                  </div>

                  <div className="mt-6">
                    <label className="block text-sm font-bold text-slate-400 mb-3">
                      Years of Experience
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="50"
                      value={formData.experience_years}
                      onChange={(e) => setFormData((prev) => ({ ...prev, experience_years: parseInt(e.target.value) || 0 }))}
                      className="w-full px-6 py-4 rounded-xl bg-white/5 border border-white/10 text-white text-lg focus:outline-none focus:border-red-500/50 focus:bg-white/10 transition-all duration-300"
                    />
                  </div>
                </div>
              </motion.div>
            )}
            
            {/* Step 3: Category Levels */}
            {currentStep === 3 && (
              <motion.div
                key="categories"
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                transition={{ duration: 0.3 }}
              >
                <h2 className="text-3xl font-black text-center mb-3">
                  Rate Your Experience
                </h2>
                <p className="text-center text-slate-400 mb-8">
                  Help us understand your current skill level
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl mx-auto">
                  {CATEGORIES.map((category) => (
                    <CategoryLevel
                      key={category.id}
                      category={category}
                      level={formData.category_levels[category.id]}
                      onSelect={handleCategoryLevel}
                    />
                  ))}
                </div>
              </motion.div>
            )}
            
            {/* Step 4: Interests */}
            {currentStep === 4 && (
              <motion.div
                key="interests"
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                transition={{ duration: 0.3 }}
              >
                <h2 className="text-3xl font-black text-center mb-3">
                  What Interests You?
                </h2>
                <p className="text-center text-slate-400 mb-2">
                  Select at least 2 topics you'd like to explore
                </p>
                <p className="text-center text-sm text-red-400 mb-8">
                  {formData.selected_interests.length} selected
                </p>

                {/* Dynamic: interests in categories rated beginner/intermediate
                    in step 3 surface first as growth areas */}
                {(() => {
                  const growth = new Set(
                    Object.entries(formData.category_levels)
                      .filter(([, lvl]) => lvl === 'beginner' || lvl === 'intermediate')
                      .map(([cat]) => cat)
                  );
                  const suggested = INTERESTS.filter((i) => growth.has(INTEREST_CATEGORY[i]));
                  const rest = INTERESTS.filter((i) => !growth.has(INTEREST_CATEGORY[i]));
                  return (
                    <>
                      {suggested.length > 0 && (
                        <>
                          <p className="text-center text-xs font-bold uppercase tracking-widest text-slate-500 mb-3">
                            Suggested from your skill ratings
                          </p>
                          <div className="flex flex-wrap gap-3 max-w-4xl mx-auto justify-center mb-6">
                            {suggested.map((interest) => (
                              <InterestChip
                                key={interest}
                                interest={interest}
                                selected={formData.selected_interests.includes(interest)}
                                onClick={() => handleInterestToggle(interest)}
                              />
                            ))}
                          </div>
                          {rest.length > 0 && (
                            <p className="text-center text-xs font-bold uppercase tracking-widest text-slate-600 mb-3">
                              Everything else
                            </p>
                          )}
                        </>
                      )}
                      <div className="flex flex-wrap gap-3 max-w-4xl mx-auto justify-center">
                        {rest.map((interest) => (
                          <InterestChip
                            key={interest}
                            interest={interest}
                            selected={formData.selected_interests.includes(interest)}
                            onClick={() => handleInterestToggle(interest)}
                          />
                        ))}
                      </div>
                    </>
                  );
                })()}
              </motion.div>
            )}
            
            {/* Step 5: Weekly Commitment */}
            {currentStep === 5 && (
              <motion.div
                key="commitment"
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                transition={{ duration: 0.3 }}
                className="max-w-2xl mx-auto"
              >
                <h2 className="text-3xl font-black text-center mb-3">
                  Weekly Time Commitment
                </h2>
                <p className="text-center text-slate-400 mb-8">
                  How many hours can you dedicate per week?
                </p>
                
                <div className="glass-panel p-8 rounded-3xl">
                  <div className="text-center mb-6">
                    <span className="text-6xl font-black text-red-400">
                      {formData.weekly_hours}
                    </span>
                    <span className="text-2xl text-slate-400 ml-2">hours/week</span>
                  </div>
                  
                  <input
                    type="range"
                    min="1"
                    max="40"
                    value={formData.weekly_hours}
                    onChange={(e) => setFormData((prev) => ({ ...prev, weekly_hours: parseInt(e.target.value) }))}
                    className="w-full h-3 bg-white/5 rounded-full appearance-none cursor-pointer slider"
                    style={{
                      background: `linear-gradient(to right, #ff2d2d 0%, #ff2d2d ${(formData.weekly_hours / 40) * 100}%, rgba(255,255,255,0.05) ${(formData.weekly_hours / 40) * 100}%, rgba(255,255,255,0.05) 100%)`
                    }}
                  />
                  
                  <div className="flex gap-2 mt-6">
                    {QUICK_HOURS.map((hours) => (
                      <button
                        key={hours}
                        onClick={() => setFormData((prev) => ({ ...prev, weekly_hours: hours }))}
                        className={cn(
                          'flex-1 px-4 py-2 rounded-xl text-sm font-bold transition-all duration-200',
                          formData.weekly_hours === hours
                            ? 'bg-red-500/25 border-2 border-red-500 text-red-400'
                            : 'bg-white/5 border border-white/10 text-slate-400 hover:bg-white/10'
                        )}
                      >
                        {hours}h
                      </button>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          
          {/* Navigation */}
          {currentStep > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center justify-between max-w-4xl mx-auto mt-12"
            >
              <button
                onClick={handleBack}
                className="flex items-center gap-2 px-6 py-3 rounded-xl bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10 hover:text-white transition-all duration-200"
              >
                <ArrowLeft size={18} />
                Back
              </button>
              
              {currentStep < 5 ? (
                <button
                  onClick={handleNext}
                  disabled={!canProceed()}
                  className={cn(
                    'flex items-center gap-2 px-8 py-3 rounded-xl font-bold transition-all duration-200',
                    canProceed()
                      ? 'bg-gradient-to-r from-red-600 to-red-800 text-white hover:shadow-[0_0_20px_rgba(255, 45, 45, 0.4)]'
                      : 'bg-white/5 border border-white/10 text-slate-600 cursor-not-allowed'
                  )}
                >
                  Continue
                  <ArrowRight size={18} />
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={!canProceed()}
                  className={cn(
                    'flex items-center gap-2 px-8 py-3 rounded-xl font-bold transition-all duration-200',
                    canProceed()
                      ? 'bg-gradient-to-r from-red-600 to-red-800 text-white hover:shadow-[0_0_20px_rgba(255, 45, 45, 0.4)]'
                      : 'bg-white/5 border border-white/10 text-slate-600 cursor-not-allowed'
                  )}
                >
                  Generate My Path
                  <Sparkles size={18} />
                </button>
              )}
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}

export default OnboardingPage;
