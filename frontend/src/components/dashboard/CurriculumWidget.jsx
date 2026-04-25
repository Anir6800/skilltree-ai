/**
 * SkillTree AI - Curriculum Widget
 * Interactive weekly learning plan with AI-generated motivational summaries
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Calendar,
  ChevronDown,
  ChevronUp,
  Clock,
  Target,
  CheckCircle2,
  Circle,
  RefreshCw,
  Sparkles,
  TrendingUp,
  TrendingDown,
  Minus,
  Play,
  Award
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/api';

// Simple confetti effect without external dependency
const triggerConfetti = () => {
  // Create confetti particles
  const colors = ['#6366f1', '#f43f5e', '#3dd68c', '#fbbf24'];
  const particleCount = 50;
  
  for (let i = 0; i < particleCount; i++) {
    const particle = document.createElement('div');
    particle.style.position = 'fixed';
    particle.style.width = '10px';
    particle.style.height = '10px';
    particle.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
    particle.style.left = '50%';
    particle.style.top = '50%';
    particle.style.borderRadius = Math.random() > 0.5 ? '50%' : '0';
    particle.style.pointerEvents = 'none';
    particle.style.zIndex = '9999';
    
    document.body.appendChild(particle);
    
    const angle = (Math.PI * 2 * i) / particleCount;
    const velocity = 5 + Math.random() * 5;
    const vx = Math.cos(angle) * velocity;
    const vy = Math.sin(angle) * velocity - 5;
    
    let x = 0;
    let y = 0;
    let opacity = 1;
    
    const animate = () => {
      x += vx;
      y += vy + (0.5 * Math.pow(y / 100, 2));
      opacity -= 0.02;
      
      particle.style.transform = `translate(${x}px, ${y}px)`;
      particle.style.opacity = opacity;
      
      if (opacity > 0) {
        requestAnimationFrame(animate);
      } else {
        document.body.removeChild(particle);
      }
    };
    
    requestAnimationFrame(animate);
  }
};

const CurriculumWidget = () => {
  const navigate = useNavigate();
  const [curriculum, setCurriculum] = useState(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [expandedWeeks, setExpandedWeeks] = useState(new Set([1])); // Week 1 expanded by default
  const [error, setError] = useState(null);

  useEffect(() => {
    loadCurriculum();
  }, []);

  const loadCurriculum = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/api/curriculum/my-curriculum/');
      
      if (response.data.status === 'generating') {
        // Curriculum is being generated, poll after delay
        setTimeout(loadCurriculum, 3000);
        return;
      }
      
      setCurriculum(response.data);
    } catch (err) {
      console.error('Failed to load curriculum:', err);
      setError('Failed to load your learning path');
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerate = async () => {
    try {
      setRegenerating(true);
      await api.post('/api/curriculum/regenerate/');
      
      // Poll for new curriculum
      setTimeout(() => {
        loadCurriculum();
        setRegenerating(false);
      }, 3000);
    } catch (err) {
      console.error('Failed to regenerate curriculum:', err);
      setRegenerating(false);
    }
  };

  const toggleWeek = (weekNumber) => {
    setExpandedWeeks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(weekNumber)) {
        newSet.delete(weekNumber);
      } else {
        newSet.add(weekNumber);
      }
      return newSet;
    });
  };

  const getProgressStatus = (week) => {
    const { completed_count, total_count } = week;
    const expectedProgress = 100; // Assume each week should be 100% complete by its end
    const actualProgress = week.progress_percentage;
    
    if (actualProgress === 100) {
      return { status: 'completed', label: 'Completed', icon: CheckCircle2, color: 'text-emerald-400' };
    } else if (actualProgress >= expectedProgress * 0.8) {
      return { status: 'on-track', label: 'On Track', icon: TrendingUp, color: 'text-blue-400' };
    } else if (actualProgress >= expectedProgress * 0.5) {
      return { status: 'behind', label: 'Behind', icon: Minus, color: 'text-yellow-400' };
    } else {
      return { status: 'behind', label: 'Behind', icon: TrendingDown, color: 'text-red-400' };
    }
  };

  const handleStartQuest = (questId) => {
    navigate(`/editor/${questId}`);
  };

  // Check if any week just completed
  useEffect(() => {
    if (curriculum?.weeks) {
      curriculum.weeks.forEach(week => {
        if (week.progress_percentage === 100 && week.completed_count === week.total_count) {
          // Week completed, trigger confetti
          triggerConfetti();
        }
      });
    }
  }, [curriculum]);

  if (loading) {
    return <CurriculumSkeleton />;
  }

  if (error) {
    return (
      <div className="glass-panel p-6 rounded-3xl">
        <div className="text-center py-8">
          <div className="w-16 h-16 bg-red-500/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Target className="w-8 h-8 text-red-500" />
          </div>
          <p className="text-slate-400 font-medium">{error}</p>
          <button
            onClick={loadCurriculum}
            className="mt-4 px-6 py-2 bg-white/10 hover:bg-white/20 rounded-xl font-bold transition-all"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!curriculum || !curriculum.weeks || curriculum.weeks.length === 0) {
    return (
      <div className="glass-panel p-6 rounded-3xl">
        <div className="text-center py-8">
          <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Calendar className="w-8 h-8 text-primary" />
          </div>
          <h4 className="text-lg font-bold text-white mb-2">No Learning Path Yet</h4>
          <p className="text-slate-400 font-medium mb-4">
            Complete your onboarding to generate your personalized curriculum
          </p>
          <button
            onClick={() => navigate('/onboarding')}
            className="px-6 py-2 bg-primary text-white rounded-xl font-bold hover:scale-105 transition-transform"
          >
            Start Onboarding
          </button>
        </div>
      </div>
    );
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.9 }}
      className="glass-panel p-6 rounded-3xl relative overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-primary/20 to-accent/20 rounded-2xl flex items-center justify-center">
            <Calendar className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h3 className="text-xl font-black text-white">Your Learning Path</h3>
            <p className="text-xs text-slate-400 font-medium">
              {curriculum.total_quests} quests • {curriculum.weeks.length} weeks • {curriculum.weekly_hours}h/week
            </p>
          </div>
        </div>

        <button
          onClick={handleRegenerate}
          disabled={regenerating}
          className="p-3 bg-white/5 hover:bg-white/10 rounded-xl transition-all group relative"
          title="Regenerate curriculum"
        >
          <RefreshCw
            className={`w-5 h-5 text-slate-400 group-hover:text-primary transition-colors ${
              regenerating ? 'animate-spin' : ''
            }`}
          />
          <div className="absolute -top-8 right-0 bg-black/90 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
            Regenerate
          </div>
        </button>
      </div>

      {/* Overall Progress */}
      <div className="mb-6 p-4 bg-white/5 rounded-2xl border border-white/10">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">
            Overall Progress
          </span>
          <span className="text-sm font-black text-primary">
            {curriculum.overall_progress}%
          </span>
        </div>
        <div className="h-2 bg-white/5 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${curriculum.overall_progress}%` }}
            transition={{ duration: 1, ease: 'easeOut' }}
            className="h-full bg-gradient-to-r from-primary to-accent"
          />
        </div>
      </div>

      {/* Weeks Accordion */}
      <div className="space-y-3">
        {curriculum.weeks.map((week, index) => {
          const isExpanded = expandedWeeks.has(week.week);
          const progressStatus = getProgressStatus(week);
          const StatusIcon = progressStatus.icon;

          return (
            <motion.div
              key={week.week}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="border border-white/10 rounded-2xl overflow-hidden bg-white/[0.02] hover:bg-white/[0.04] transition-colors"
            >
              {/* Week Header */}
              <button
                onClick={() => toggleWeek(week.week)}
                className="w-full p-4 flex items-center justify-between text-left"
              >
                <div className="flex items-center gap-4 flex-1">
                  {/* Week Number Badge */}
                  <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                    <span className="text-sm font-black text-primary">W{week.week}</span>
                  </div>

                  {/* Week Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="text-sm font-bold text-white">Week {week.week}</h4>
                      <div className={`flex items-center gap-1 px-2 py-0.5 rounded-full bg-white/5 ${progressStatus.color}`}>
                        <StatusIcon className="w-3 h-3" />
                        <span className="text-[10px] font-bold uppercase tracking-wider">
                          {progressStatus.label}
                        </span>
                      </div>
                    </div>
                    <p className="text-xs text-slate-400 line-clamp-1 font-medium">
                      {week.focus}
                    </p>
                  </div>

                  {/* Progress Ring */}
                  <div className="relative w-12 h-12">
                    <svg className="w-12 h-12 transform -rotate-90">
                      <circle
                        cx="24"
                        cy="24"
                        r="20"
                        stroke="currentColor"
                        strokeWidth="3"
                        fill="none"
                        className="text-white/10"
                      />
                      <circle
                        cx="24"
                        cy="24"
                        r="20"
                        stroke="currentColor"
                        strokeWidth="3"
                        fill="none"
                        strokeDasharray={`${2 * Math.PI * 20}`}
                        strokeDashoffset={`${2 * Math.PI * 20 * (1 - week.progress_percentage / 100)}`}
                        className="text-primary transition-all duration-500"
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-[10px] font-black text-white">
                        {week.completed_count}/{week.total_count}
                      </span>
                    </div>
                  </div>

                  {/* Expand Icon */}
                  <div className="text-slate-400">
                    {isExpanded ? (
                      <ChevronUp className="w-5 h-5" />
                    ) : (
                      <ChevronDown className="w-5 h-5" />
                    )}
                  </div>
                </div>
              </button>

              {/* Week Content (Quests) */}
              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    className="border-t border-white/10"
                  >
                    <div className="p-4 space-y-3">
                      {/* Week Focus */}
                      <div className="flex items-start gap-3 p-3 bg-primary/5 rounded-xl border border-primary/20">
                        <Sparkles className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                        <div>
                          <div className="text-[10px] font-bold text-primary uppercase tracking-widest mb-1">
                            Weekly Focus
                          </div>
                          <p className="text-sm text-slate-300 font-medium leading-relaxed">
                            {week.focus}
                          </p>
                        </div>
                      </div>

                      {/* Quest Cards */}
                      {week.quests.length > 0 ? (
                        <div className="space-y-2">
                          {week.quests.map((quest, qIndex) => (
                            <motion.div
                              key={quest.quest_id}
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: qIndex * 0.05 }}
                              className={`p-3 rounded-xl border transition-all ${
                                quest.completed
                                  ? 'bg-emerald-500/5 border-emerald-500/20'
                                  : 'bg-white/5 border-white/10 hover:border-primary/30'
                              }`}
                            >
                              <div className="flex items-center justify-between gap-3">
                                {/* Quest Info */}
                                <div className="flex items-center gap-3 flex-1 min-w-0">
                                  {/* Completion Icon */}
                                  <div>
                                    {quest.completed ? (
                                      <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                                    ) : (
                                      <Circle className="w-5 h-5 text-slate-600" />
                                    )}
                                  </div>

                                  {/* Quest Details */}
                                  <div className="flex-1 min-w-0">
                                    <h5 className={`text-sm font-bold truncate ${
                                      quest.completed ? 'text-slate-400 line-through' : 'text-white'
                                    }`}>
                                      {quest.title}
                                    </h5>
                                    <div className="flex items-center gap-2 mt-1">
                                      <span className="px-2 py-0.5 bg-primary/20 text-primary text-[10px] font-bold rounded uppercase">
                                        {quest.skill_title}
                                      </span>
                                      <span className="flex items-center gap-1 text-[10px] text-slate-500 font-medium">
                                        <Clock className="w-3 h-3" />
                                        {quest.est_minutes}m
                                      </span>
                                      <span className="flex items-center gap-1 text-[10px] text-accent font-bold">
                                        <Award className="w-3 h-3" />
                                        +{quest.xp_reward} XP
                                      </span>
                                    </div>
                                  </div>
                                </div>

                                {/* Start Button */}
                                {!quest.completed && (
                                  <button
                                    onClick={() => handleStartQuest(quest.quest_id)}
                                    className="px-4 py-2 bg-primary hover:bg-primary/80 text-white rounded-lg text-xs font-bold uppercase tracking-wider transition-all flex items-center gap-2 group"
                                  >
                                    <Play className="w-3 h-3 group-hover:scale-110 transition-transform" />
                                    Start
                                  </button>
                                )}
                              </div>
                            </motion.div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-6 text-slate-500 text-sm">
                          No quests scheduled for this week
                        </div>
                      )}

                      {/* Week Stats */}
                      <div className="flex items-center justify-between pt-3 border-t border-white/10">
                        <div className="text-xs text-slate-500 font-medium">
                          Total time: ~{week.total_minutes} minutes
                        </div>
                        <div className="text-xs font-bold text-primary">
                          {week.completed_count} of {week.total_count} completed
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}
      </div>

      {/* Decorative Background */}
      <Target className="absolute -right-8 -bottom-8 w-48 h-48 text-primary/5 -rotate-12 pointer-events-none" />
    </motion.section>
  );
};

const CurriculumSkeleton = () => (
  <div className="glass-panel p-6 rounded-3xl animate-pulse">
    <div className="flex items-center justify-between mb-6">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 bg-white/5 rounded-2xl" />
        <div>
          <div className="h-5 w-32 bg-white/5 rounded mb-2" />
          <div className="h-3 w-48 bg-white/5 rounded" />
        </div>
      </div>
      <div className="w-10 h-10 bg-white/5 rounded-xl" />
    </div>
    <div className="space-y-3">
      {[1, 2, 3].map(n => (
        <div key={n} className="h-16 bg-white/5 rounded-2xl" />
      ))}
    </div>
  </div>
);

export default CurriculumWidget;
