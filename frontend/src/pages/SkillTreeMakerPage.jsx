/**
 * SkillTree AI - Skill Tree Maker Page
 * AI-powered skill tree generation with onboarding integration
 * Allows users to generate personalized learning paths for any topic
 */

import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  ChevronRight,
  Zap,
  AlertCircle,
  CheckCircle,
  X,
  Copy,
  Share2,
  Lock,
  Unlock,
  BookOpen,
  Clock,
  Target,
  Loader,
  RefreshCw,
  Crown,
} from 'lucide-react';
import api from '../api/api';
import useAuthStore from '../store/authStore';
import MainLayout from '../components/layout/MainLayout';

/**
 * Animated skill tree SVG that grows nodes
 */
const AnimatedSkillTree = ({ nodeCount = 8 }) => {
  return (
    <motion.svg
      width="200"
      height="200"
      viewBox="0 0 200 200"
      className="mx-auto"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      {/* Center node */}
      <motion.circle
        cx="100"
        cy="100"
        r="12"
        fill="url(#gradient)"
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0, duration: 0.4 }}
      />

      {/* Surrounding nodes */}
      {Array.from({ length: Math.min(nodeCount, 8) }).map((_, i) => {
        const angle = (i / 8) * Math.PI * 2;
        const radius = 60;
        const x = 100 + radius * Math.cos(angle);
        const y = 100 + radius * Math.sin(angle);

        return (
          <g key={i}>
            {/* Connection line */}
            <motion.line
              x1="100"
              y1="100"
              x2={x}
              y2={y}
              stroke="url(#gradient)"
              strokeWidth="2"
              opacity="0.3"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ delay: i * 0.05, duration: 0.3 }}
            />

            {/* Node */}
            <motion.circle
              cx={x}
              cy={y}
              r="8"
              fill="url(#gradient)"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: i * 0.05 + 0.1, duration: 0.4 }}
            />
          </g>
        );
      })}

      <defs>
        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#6366f1" />
          <stop offset="100%" stopColor="#a855f7" />
        </linearGradient>
      </defs>
    </motion.svg>
  );
};

/**
 * Difficulty pips component
 */
const DifficultyPips = ({ level }) => {
  return (
    <div className="flex gap-1">
      {Array.from({ length: 5 }).map((_, i) => (
        <div
          key={i}
          className={`w-1.5 h-1.5 rounded-full transition-colors ${
            i < level ? 'bg-gradient-to-r from-primary to-accent' : 'bg-slate-700'
          }`}
        />
      ))}
    </div>
  );
};

/**
 * Skill card component for preview
 */
const SkillCard = ({ skill, index }) => {
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1 }}
      className="glass-panel rounded-xl p-4 min-w-[280px] border border-primary/20 hover:border-primary/40 transition-all hover:shadow-[0_0_30px_rgba(99,102,241,0.2)]"
    >
      <div className="space-y-3">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold text-white text-sm leading-tight flex-1">
            {skill.title}
          </h3>
          <div className="flex-shrink-0">
            <Unlock className="w-4 h-4 text-primary" />
          </div>
        </div>

        <DifficultyPips level={skill.difficulty} />

        <div className="space-y-2 pt-2 border-t border-slate-700/50">
          <p className="text-xs text-slate-400 font-medium">Quest Stubs:</p>
          <div className="space-y-1">
            {skill.quest_titles?.slice(0, 2).map((quest, i) => (
              <div key={i} className="flex items-center gap-2 text-xs text-slate-300">
                <div className="w-1 h-1 rounded-full bg-primary/60" />
                <span className="truncate">{quest}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-400 pt-2 border-t border-slate-700/50">
          <Clock className="w-3 h-3" />
          <span>{skill.estimated_hours || 5}h est.</span>
        </div>
      </div>
    </motion.div>
  );
};

/**
 * Status message cycler
 */
const StatusCycler = () => {
  const messages = [
    'Analyzing topic structure...',
    'Identifying prerequisite skills...',
    'Designing learning progression...',
    'Writing quest descriptions...',
    'Finalizing your tree ✦',
  ];

  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % messages.length);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <AnimatePresence mode="wait">
      <motion.p
        key={messageIndex}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ duration: 0.3 }}
        className="text-slate-300 text-center font-medium"
      >
        {messages[messageIndex]}
      </motion.p>
    </AnimatePresence>
  );
};

/**
 * Main SkillTreeMakerPage component
 */
const SkillTreeMakerPage = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();

  // State
  const [topic, setTopic] = useState('');
  const [depth, setDepth] = useState(3);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [generatedTree, setGeneratedTree] = useState(null);
  const [generatedTrees, setGeneratedTrees] = useState([]);
  const [onboardingProfile, setOnboardingProfile] = useState(null);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [copiedTreeId, setCopiedTreeId] = useState(null);
  const [autoFillLoading, setAutoFillLoading] = useState(false);
  const [autoFillProgress, setAutoFillProgress] = useState(null);
  const [autoFillError, setAutoFillError] = useState(null);
  const inputRef = useRef(null);
  const wsRef = useRef(null);

  // Default suggestions
  const defaultSuggestions = [
    'Machine Learning',
    'DevOps',
    'Web3',
    'System Design',
    'Game Dev',
    'Data Engineering',
    'Cybersecurity',
    'Mobile Dev',
  ];

  // Get personalized suggestions from onboarding
  const getPersonalizedSuggestions = () => {
    if (!onboardingProfile?.selected_interests) {
      return defaultSuggestions;
    }

    const interestMap = {
      arrays: 'Data Structures',
      graphs: 'Graph Algorithms',
      sorting: 'Algorithm Optimization',
      dynamic_programming: 'Dynamic Programming',
      trees: 'Tree Structures',
      linked_lists: 'Linked Lists',
      hash_tables: 'Hash Tables',
      strings: 'String Algorithms',
    };

    const personalized = onboardingProfile.selected_interests
      .slice(0, 3)
      .map((interest) => interestMap[interest] || interest)
      .filter(Boolean);

    return [...personalized, ...defaultSuggestions].slice(0, 8);
  };

  const suggestions = getPersonalizedSuggestions();

  // Load onboarding profile and generated trees
  useEffect(() => {
    const loadData = async () => {
      try {
        // Load onboarding profile
        try {
          const profileRes = await api.get('/api/onboarding/profile/');
          setOnboardingProfile(profileRes.data);
        } catch (err) {
          // Profile might not exist, that's okay
          console.log('No onboarding profile found');
        }

        // Load user's generated trees
        try {
          const treesRes = await api.get('/api/skills/generated/');
          setGeneratedTrees(treesRes.data || []);
        } catch (err) {
          console.error('Failed to load generated trees:', err);
        }
      } catch (err) {
        console.error('Failed to load data:', err);
      }
    };

    loadData();
  }, []);

  // Handle topic input
  const handleTopicChange = (e) => {
    setTopic(e.target.value);
    setError(null);
  };

  // Handle suggestion click
  const handleSuggestionClick = (suggestion) => {
    setTopic(suggestion);
    setShowSuggestions(false);
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  // Generate tree
  const handleGenerate = async () => {
    if (!topic.trim()) {
      setError('Please enter a topic');
      return;
    }

    if (topic.trim().length < 2) {
      setError('Topic must be at least 2 characters');
      return;
    }

    setLoading(true);
    setError(null);
    setGeneratedTree(null);

    try {
      const response = await api.post('/api/skills/generate/', {
        topic: topic.trim(),
        depth,
      });

      const treeId = response.data.tree_id;

      // Poll for completion
      let attempts = 0;
      const maxAttempts = 60; // 60 seconds max

      const pollForCompletion = async () => {
        try {
          const detailRes = await api.get(`/api/skills/generated/${treeId}/`);

          if (detailRes.data.status === 'ready') {
            setGeneratedTree(detailRes.data);
            setTopic('');
            setShowSuggestions(true);

            // Add to generated trees list
            setGeneratedTrees((prev) => [detailRes.data, ...prev]);

            // Update onboarding if applicable
            if (onboardingProfile && !onboardingProfile.path_generated) {
              try {
                await api.post('/api/onboarding/update-profile/', {
                  generated_topic: topic.trim(),
                  path_generated: true,
                  generated_tree_id: treeId,
                });
              } catch (err) {
                console.log('Could not update onboarding profile');
              }
            }

            return true;
          } else if (detailRes.data.status === 'failed') {
            setError('Tree generation failed. Please try again.');
            return true;
          }

          return false;
        } catch (err) {
          console.error('Poll error:', err);
          return false;
        }
      };

      // Poll with exponential backoff
      while (attempts < maxAttempts) {
        const completed = await pollForCompletion();
        if (completed) break;

        attempts++;
        await new Promise((resolve) =>
          setTimeout(resolve, Math.min(1000 + attempts * 100, 3000))
        );
      }

      if (attempts >= maxAttempts) {
        setError('Tree generation took too long. Please try again.');
      }
    } catch (err) {
      setError(
        err.response?.data?.error ||
        err.message ||
        'Failed to generate tree. Please try again.'
      );
      console.error('Generation error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Handle keyboard enter
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
      handleGenerate();
    }
  };

  // Copy tree ID
  const handleCopyTreeId = (treeId) => {
    navigator.clipboard.writeText(treeId);
    setCopiedTreeId(treeId);
    setTimeout(() => setCopiedTreeId(null), 2000);
  };

  // Navigate to skill tree
  const handleViewTree = () => {
    // Store generated tree info in session for skill tree view
    sessionStorage.setItem('lastGeneratedTreeId', generatedTree?.id);
    sessionStorage.setItem('lastGeneratedTopic', generatedTree?.topic);
    
    // Navigate to skill tree with highlight flag
    navigate('/skill-tree', { 
      state: { 
        highlightNewSkills: true,
        generatedTreeId: generatedTree?.id,
        generatedTopic: generatedTree?.topic
      } 
    });
  };

  // Generate another
  const handleGenerateAnother = () => {
    setGeneratedTree(null);
    setTopic('');
    setShowSuggestions(true);
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  // Publish tree (staff only)
  const handlePublishTree = async (treeId) => {
    try {
      await api.post(`/api/skills/generated/${treeId}/publish/`);
      // Update tree in list
      setGeneratedTrees((prev) =>
        prev.map((t) => (t.id === treeId ? { ...t, is_public: true } : t))
      );
      if (generatedTree?.id === treeId) {
        setGeneratedTree({ ...generatedTree, is_public: true });
      }
    } catch (err) {
      setError('Failed to publish tree');
      console.error('Publish error:', err);
    }
  };

  // Auto-fill quests
  const handleAutoFillQuests = async () => {
    if (!generatedTree?.id) return;

    setAutoFillLoading(true);
    setAutoFillError(null);
    setAutoFillProgress({ filled: 0, total: 0 });

    try {
      // Start auto-fill task
      const response = await api.post(
        `/api/skills/generated/${generatedTree.id}/autofill-quests/`
      );

      const { quests_to_fill } = response.data;
      setAutoFillProgress({ filled: 0, total: quests_to_fill });

      // Connect to WebSocket for progress updates
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/skills/autofill/${generatedTree.id}/`;

      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('Connected to quest autofill WebSocket');
      };

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'quest_filled') {
          setAutoFillProgress((prev) => ({
            ...prev,
            filled: prev.filled + 1,
          }));
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setAutoFillError('Connection error during quest filling');
      };

      wsRef.current.onclose = () => {
        console.log('Disconnected from quest autofill WebSocket');
        setAutoFillLoading(false);

        // Check if all quests were filled
        if (autoFillProgress && autoFillProgress.filled === autoFillProgress.total) {
          // Show success toast
          console.log('All quests filled successfully!');
        }
      };
    } catch (err) {
      setAutoFillError(
        err.response?.data?.error ||
        err.message ||
        'Failed to start quest auto-fill'
      );
      setAutoFillLoading(false);
      console.error('Auto-fill error:', err);
    }
  };

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Cancel generation
  const handleCancel = async () => {
    if (generatedTree?.id) {
      try {
        await api.delete(`/api/skills/generated/${generatedTree.id}/`);
      } catch (err) {
        console.error('Cancel error:', err);
      }
    }
    setGeneratedTree(null);
    setLoading(false);
  };

  return (
    <MainLayout>
      <div className="min-h-screen bg-[#0a0c10] text-white p-4 md:p-8">
        {/* Background effects */}
        <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
          <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-purple-600/10 blur-[120px] rounded-full" />
          <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-600/10 blur-[120px] rounded-full" />
        </div>

        <div className="max-w-2xl mx-auto space-y-12">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center space-y-4"
          >
            <div className="flex items-center justify-center gap-2 text-primary font-semibold text-sm tracking-widest uppercase">
              <Sparkles className="w-4 h-4" />
              AI Skill Tree Generator
            </div>

            <h1 className="text-4xl md:text-5xl font-black tracking-tight">
              Generate a skill tree for{' '}
              <span className="premium-gradient-text">anything.</span>
            </h1>

            <p className="text-slate-400 text-lg leading-relaxed max-w-xl mx-auto">
              Type any topic — from Kubernetes to Watercolor Painting — and AI builds your
              personalized learning path in seconds.
            </p>
          </motion.div>

          {/* Main content */}
          <AnimatePresence mode="wait">
            {!loading && !generatedTree ? (
              // Input section
              <motion.div
                key="input"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
              >
                {/* Topic input */}
                <div className="space-y-3">
                  <label className="block text-sm font-semibold text-slate-300">
                    What do you want to learn?
                  </label>

                  <input
                    ref={inputRef}
                    type="text"
                    value={topic}
                    onChange={handleTopicChange}
                    onKeyPress={handleKeyPress}
                    onFocus={() => setShowSuggestions(true)}
                    placeholder="e.g. Machine Learning, DevOps, Game Dev, Web3..."
                    className="w-full h-12 px-4 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 font-mono text-sm focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/30 transition-all"
                  />

                  {/* Suggestions */}
                  {showSuggestions && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex flex-wrap gap-2 pt-2"
                    >
                      {suggestions.map((suggestion, i) => (
                        <motion.button
                          key={suggestion}
                          initial={{ opacity: 0, scale: 0.9 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: i * 0.05 }}
                          onClick={() => handleSuggestionClick(suggestion)}
                          className="px-3 py-1.5 text-xs font-medium rounded-full bg-slate-800/50 border border-slate-700 text-slate-300 hover:border-primary/50 hover:text-primary transition-all hover:bg-slate-800"
                        >
                          {suggestion}
                        </motion.button>
                      ))}
                    </motion.div>
                  )}
                </div>

                {/* Depth selector */}
                <div className="space-y-3">
                  <label className="block text-sm font-semibold text-slate-300">
                    Learning depth
                  </label>

                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { value: 2, label: 'Quick', desc: '2 levels' },
                      { value: 3, label: 'Standard', desc: '3 levels' },
                      { value: 4, label: 'Deep', desc: '4 levels' },
                    ].map((option) => (
                      <motion.button
                        key={option.value}
                        onClick={() => setDepth(option.value)}
                        className={`p-3 rounded-lg border-2 transition-all ${
                          depth === option.value
                            ? 'border-primary bg-primary/10'
                            : 'border-slate-700 bg-slate-900/30 hover:border-slate-600'
                        }`}
                      >
                        <div className="font-semibold text-sm">{option.label}</div>
                        <div className="text-xs text-slate-400">{option.desc}</div>
                      </motion.button>
                    ))}
                  </div>
                </div>

                {/* Error message */}
                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center gap-3 p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300"
                  >
                    <AlertCircle className="w-5 h-5 flex-shrink-0" />
                    <span className="text-sm">{error}</span>
                  </motion.div>
                )}

                {/* Generate button */}
                <motion.button
                  onClick={handleGenerate}
                  disabled={loading}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full h-12 rounded-lg bg-gradient-to-r from-primary to-accent text-white font-semibold text-base flex items-center justify-center gap-2 hover:shadow-[0_0_30px_rgba(99,102,241,0.4)] disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  {loading ? (
                    <>
                      <Loader className="w-5 h-5 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      Generate My Tree
                      <Sparkles className="w-5 h-5" />
                    </>
                  )}
                </motion.button>
              </motion.div>
            ) : loading ? (
              // Loading state
              <motion.div
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-8 py-12"
              >
                <AnimatedSkillTree nodeCount={8} />

                <div className="space-y-4 text-center">
                  <StatusCycler />

                  <motion.button
                    onClick={handleCancel}
                    className="text-sm text-slate-400 hover:text-slate-300 transition-colors"
                  >
                    Cancel
                  </motion.button>
                </div>
              </motion.div>
            ) : generatedTree ? (
              // Result state
              <motion.div
                key="result"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-8"
              >
                {/* Success banner */}
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-3 p-4 rounded-lg bg-green-500/10 border border-green-500/30 text-green-300"
                >
                  <CheckCircle className="w-5 h-5 flex-shrink-0" />
                  <span className="text-sm font-medium">
                    Your {generatedTree.topic} skill tree is ready! (
                    {generatedTree.skills?.length || 0} skills,{' '}
                    {generatedTree.skills?.reduce((sum, s) => sum + (s.quest_titles?.length || 0), 0) || 0}{' '}
                    quests)
                  </span>
                </motion.div>

                {/* Skills preview */}
                {generatedTree.skills && generatedTree.skills.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="text-sm font-semibold text-slate-300">Skills Preview</h3>
                    <div className="overflow-x-auto pb-2">
                      <div className="flex gap-4">
                        {generatedTree.skills.map((skill, i) => (
                          <SkillCard key={skill.id} skill={skill} index={i} />
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Action buttons */}
                <div className="space-y-3">
                  {autoFillLoading && autoFillProgress ? (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="space-y-3 p-4 rounded-lg bg-blue-500/10 border border-blue-500/30"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-blue-300">
                          Filling quests…
                        </span>
                        <span className="text-sm text-blue-300/70">
                          {autoFillProgress.filled}/{autoFillProgress.total} complete
                        </span>
                      </div>
                      <div className="w-full h-2 bg-blue-900/30 rounded-full overflow-hidden">
                        <motion.div
                          className="h-full bg-gradient-to-r from-blue-500 to-cyan-500"
                          initial={{ width: 0 }}
                          animate={{
                            width: `${
                              autoFillProgress.total > 0
                                ? (autoFillProgress.filled / autoFillProgress.total) * 100
                                : 0
                            }%`,
                          }}
                          transition={{ duration: 0.3 }}
                        />
                      </div>
                    </motion.div>
                  ) : autoFillError ? (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex items-center gap-3 p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300"
                    >
                      <AlertCircle className="w-5 h-5 flex-shrink-0" />
                      <span className="text-sm">{autoFillError}</span>
                    </motion.div>
                  ) : autoFillProgress && autoFillProgress.filled === autoFillProgress.total && autoFillProgress.total > 0 ? (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex items-center gap-3 p-4 rounded-lg bg-green-500/10 border border-green-500/30 text-green-300"
                    >
                      <CheckCircle className="w-5 h-5 flex-shrink-0" />
                      <span className="text-sm font-medium">
                        All quests ready — tree is fully playable!
                      </span>
                    </motion.div>
                  ) : null}

                  <motion.button
                    onClick={handleViewTree}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="w-full h-12 rounded-lg bg-gradient-to-r from-primary to-accent text-white font-semibold flex items-center justify-center gap-2 hover:shadow-[0_0_30px_rgba(99,102,241,0.4)] transition-all"
                  >
                    View in Skill Tree
                    <ChevronRight className="w-5 h-5" />
                  </motion.button>

                  {!autoFillLoading && !autoFillProgress && (
                    <motion.button
                      onClick={handleAutoFillQuests}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="w-full h-12 rounded-lg border border-cyan-500/30 bg-cyan-500/10 text-cyan-300 font-semibold flex items-center justify-center gap-2 hover:border-cyan-500/50 transition-all"
                    >
                      <Sparkles className="w-5 h-5" />
                      Auto-Fill Quests
                    </motion.button>
                  )}

                  <motion.button
                    onClick={handleGenerateAnother}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="w-full h-12 rounded-lg border border-slate-700 text-slate-300 font-semibold flex items-center justify-center gap-2 hover:border-slate-600 hover:text-white transition-all"
                  >
                    <RefreshCw className="w-5 h-5" />
                    Generate Another
                  </motion.button>

                  {user?.is_staff && !generatedTree.is_public && (
                    <motion.button
                      onClick={() => handlePublishTree(generatedTree.id)}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="w-full h-12 rounded-lg border border-amber-500/30 bg-amber-500/10 text-amber-300 font-semibold flex items-center justify-center gap-2 hover:border-amber-500/50 transition-all"
                    >
                      <Crown className="w-5 h-5" />
                      Publish for All Users
                    </motion.button>
                  )}
                </div>
              </motion.div>
            ) : null}
          </AnimatePresence>

          {/* Generated trees history */}
          {generatedTrees.length > 0 && !loading && !generatedTree && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-4 pt-8 border-t border-slate-800"
            >
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-primary" />
                My Generated Trees
              </h2>

              <div className="space-y-2">
                {generatedTrees.map((tree) => (
                  <motion.div
                    key={tree.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="glass-panel rounded-lg p-4 border border-slate-700/50 hover:border-slate-600 transition-all flex items-center justify-between group"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-white truncate">{tree.topic}</h3>
                        {tree.is_public && (
                          <span className="text-xs px-2 py-1 rounded-full bg-green-500/20 text-green-300 border border-green-500/30 flex-shrink-0">
                            Published
                          </span>
                        )}
                        <span
                          className={`text-xs px-2 py-1 rounded-full flex-shrink-0 ${
                            tree.status === 'ready'
                              ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                              : 'bg-slate-700/50 text-slate-400 border border-slate-600'
                          }`}
                        >
                          {tree.status}
                        </span>
                      </div>

                      <div className="flex items-center gap-4 text-xs text-slate-400">
                        <span>{tree.skills_count} skills</span>
                        <span>
                          {new Date(tree.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 ml-4 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                      <motion.button
                        onClick={() => handleCopyTreeId(tree.id)}
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.95 }}
                        className="p-2 rounded-lg hover:bg-slate-700/50 transition-colors"
                        title="Copy tree ID"
                      >
                        {copiedTreeId === tree.id ? (
                          <CheckCircle className="w-4 h-4 text-green-400" />
                        ) : (
                          <Copy className="w-4 h-4 text-slate-400" />
                        )}
                      </motion.button>

                      <motion.button
                        onClick={handleViewTree}
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.95 }}
                        className="p-2 rounded-lg hover:bg-slate-700/50 transition-colors"
                        title="View tree"
                      >
                        <ChevronRight className="w-4 h-4 text-primary" />
                      </motion.button>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </MainLayout>
  );
};

export default SkillTreeMakerPage;
