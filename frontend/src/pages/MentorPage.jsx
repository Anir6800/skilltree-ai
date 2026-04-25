/**
 * SkillTree AI - AI Mentor Page
 * Chat interface with RAG-powered mentoring and learning path suggestions
 * Design: Matches Login/Dashboard/Quests/Editor glassmorphism theme
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bot, Send, Sparkles, Lightbulb, TrendingUp, Loader2,
  MessageCircle, Zap, BookOpen, Target, ChevronDown, User,
  Home, Network, Swords, Trophy, Menu, X, LogOut
} from 'lucide-react';
import api from '../api/api';
import useAuthStore from '../store/authStore';
import { cn } from '../utils/cn';

// ─── Constants ────────────────────────────────────────────────────────────────

const STORAGE_KEY = 'skilltree_mentor_chat';
const CONTEXT_OPTIONS = [
  { value: null, label: 'General Chat' },
  { value: 'skills', label: 'About Skills' },
  { value: 'quests', label: 'About Quests' },
];

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Home', icon: Home, path: '/dashboard' },
  { id: 'skills', label: 'Skills', icon: Network, path: '/skills' },
  { id: 'quests', label: 'Quests', icon: Target, path: '/quests' },
  { id: 'arena', label: 'Arena', icon: Swords, path: '/arena' },
  { id: 'leaderboard', label: 'Ranks', icon: Trophy, path: '/leaderboard' },
];

// ─── Sub-components ───────────────────────────────────────────────────────────

function FloatingNav({ isOpen, onToggle, onNavigate, onLogout, user }) {
  return (
    <div className="fixed bottom-6 left-6 z-50">
      {/* Navigation Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.9 }}
            transition={{ duration: 0.2 }}
            className="absolute bottom-20 left-0 glass-panel rounded-2xl p-3 border border-white/10 shadow-2xl backdrop-blur-3xl min-w-[200px]"
          >
            {/* Glow effects */}
            <div className="absolute -top-12 -left-12 w-32 h-32 bg-primary/10 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute -bottom-12 -right-12 w-32 h-32 bg-accent/10 rounded-full blur-3xl pointer-events-none" />

            {/* User Info */}
            {user && (
              <div className="relative mb-3 pb-3 border-b border-white/10">
                <div className="flex items-center gap-3 px-4 py-2">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary/30 to-accent/30 border-2 border-primary/40 flex items-center justify-center">
                    <User size={20} className="text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold text-white truncate">
                      {user.username}
                    </p>
                    <p className="text-xs text-slate-500">
                      Level {user.level || 1}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Nav Items */}
            <div className="relative space-y-1">
              {NAV_ITEMS.map((item, index) => {
                const Icon = item.icon;
                return (
                  <motion.button
                    key={item.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    onClick={() => onNavigate(item.path)}
                    className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-slate-300 hover:text-primary hover:bg-primary/10 transition-all duration-200 group"
                  >
                    <Icon
                      size={18}
                      className="shrink-0 group-hover:drop-shadow-[0_0_8px_rgba(99,102,241,0.8)] transition-all duration-200"
                    />
                    <span className="text-sm font-bold uppercase tracking-wider">
                      {item.label}
                    </span>
                  </motion.button>
                );
              })}
              
              {/* Divider */}
              <div className="h-px bg-white/10 my-2" />
              
              {/* Profile Button */}
              <motion.button
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: NAV_ITEMS.length * 0.05 }}
                onClick={() => onNavigate(`/profile/${user?.id || ''}`)}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-slate-300 hover:text-primary hover:bg-primary/10 transition-all duration-200 group"
              >
                <User
                  size={18}
                  className="shrink-0 group-hover:drop-shadow-[0_0_8px_rgba(99,102,241,0.8)] transition-all duration-200"
                />
                <span className="text-sm font-bold uppercase tracking-wider">
                  Profile
                </span>
              </motion.button>
              
              {/* Logout Button */}
              <motion.button
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: (NAV_ITEMS.length + 1) * 0.05 }}
                onClick={onLogout}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-all duration-200 group"
              >
                <LogOut
                  size={18}
                  className="shrink-0 group-hover:drop-shadow-[0_0_8px_rgba(239,68,68,0.8)] transition-all duration-200"
                />
                <span className="text-sm font-bold uppercase tracking-wider">
                  Logout
                </span>
              </motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Toggle Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onToggle}
        className={cn(
          'relative flex items-center justify-center w-14 h-14 rounded-2xl transition-all duration-300',
          'glass-panel border border-white/10 shadow-2xl backdrop-blur-3xl',
          isOpen
            ? 'bg-primary/20 border-primary/40 text-primary'
            : 'text-slate-300 hover:text-primary hover:bg-primary/10'
        )}
      >
        {/* Glow effect */}
        {isOpen && (
          <motion.div
            className="absolute inset-0 bg-primary/20 rounded-2xl blur-xl"
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

        {/* Icon */}
        <div className="relative z-10">
          <AnimatePresence mode="wait">
            {isOpen ? (
              <motion.div
                key="close"
                initial={{ rotate: -90, opacity: 0 }}
                animate={{ rotate: 0, opacity: 1 }}
                exit={{ rotate: 90, opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <X size={24} className={isOpen ? 'drop-shadow-[0_0_8px_rgba(99,102,241,0.8)]' : ''} />
              </motion.div>
            ) : (
              <motion.div
                key="menu"
                initial={{ rotate: 90, opacity: 0 }}
                animate={{ rotate: 0, opacity: 1 }}
                exit={{ rotate: -90, opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <Menu size={24} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.button>
    </div>
  );
}

function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      className="flex items-start gap-3 mb-4"
    >
      <div className="p-2.5 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 shadow-[0_0_20px_rgba(99,102,241,0.3)] shrink-0">
        <Bot size={18} className="text-primary" />
      </div>
      <div className="glass-card rounded-2xl px-4 py-3 max-w-[80%]">
        <div className="flex items-center gap-1.5">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="w-2 h-2 rounded-full bg-primary"
              animate={{
                opacity: [0.3, 1, 0.3],
                scale: [0.8, 1, 0.8],
              }}
              transition={{
                duration: 1.2,
                repeat: Infinity,
                delay: i * 0.2,
              }}
            />
          ))}
        </div>
      </div>
    </motion.div>
  );
}

function ChatMessage({ message, isUser }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        'flex items-start gap-3 mb-4',
        isUser && 'flex-row-reverse'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'p-2.5 rounded-xl shrink-0',
          isUser
            ? 'bg-gradient-to-br from-primary/30 to-accent/30 border border-primary/40'
            : 'bg-gradient-to-br from-primary/20 to-accent/20 shadow-[0_0_20px_rgba(99,102,241,0.3)]'
        )}
      >
        {isUser ? (
          <User size={18} className="text-primary" />
        ) : (
          <Bot size={18} className="text-primary" />
        )}
      </div>

      {/* Message bubble */}
      <div
        className={cn(
          'rounded-2xl px-4 py-3 max-w-[80%]',
          isUser
            ? 'bg-gradient-to-br from-primary/20 to-accent/20 border border-primary/30 text-white shadow-[0_0_16px_rgba(99,102,241,0.2)]'
            : 'glass-card text-slate-200'
        )}
      >
        <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
          {message.content}
        </p>
        {message.timestamp && (
          <span className="text-[10px] text-slate-500 mt-2 block">
            {new Date(message.timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        )}
      </div>
    </motion.div>
  );
}

function SuggestedSkillCard({ skill }) {
  const difficultyPips = Math.min(5, Math.max(1, skill.difficulty));

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      transition={{ duration: 0.2 }}
      className="glass-card p-4 rounded-2xl group cursor-pointer hover:shadow-[0_0_24px_rgba(99,102,241,0.2)] transition-all duration-300"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <BookOpen size={16} className="text-primary shrink-0" />
          <h4 className="text-sm font-bold text-white group-hover:text-primary transition-colors duration-300">
            {skill.title}
          </h4>
        </div>
        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-primary/20 border border-primary/30 text-primary">
          {skill.category}
        </span>
      </div>

      {/* Description */}
      <p className="text-xs text-slate-400 mb-3 leading-relaxed">
        {skill.description}
      </p>

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-white/5">
        {/* Difficulty */}
        <div className="flex items-center gap-1">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className={cn(
                'w-1.5 h-1.5 rounded-full transition-all duration-300',
                i < difficultyPips
                  ? 'bg-primary shadow-[0_0_6px_rgba(99,102,241,0.8)]'
                  : 'bg-white/10'
              )}
            />
          ))}
        </div>

        {/* XP */}
        <div className="flex items-center gap-1">
          <Zap size={12} className="text-amber-400" fill="currentColor" />
          <span className="text-xs font-bold text-amber-400">
            {skill.xp_required} XP
          </span>
        </div>
      </div>

      {/* Reason */}
      {skill.reason && (
        <div className="mt-3 pt-3 border-t border-white/5">
          <div className="flex items-start gap-1.5">
            <Lightbulb size={11} className="text-amber-400 mt-0.5 shrink-0" />
            <p className="text-[11px] text-slate-400 italic">{skill.reason}</p>
          </div>
        </div>
      )}
    </motion.div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

function MentorPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [contextType, setContextType] = useState(null);
  const [contextDropdownOpen, setContextDropdownOpen] = useState(false);
  const [suggestions, setSuggestions] = useState(null);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [navOpen, setNavOpen] = useState(false);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const contextDropdownRef = useRef(null);

  // Load chat history from sessionStorage
  useEffect(() => {
    const stored = sessionStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setMessages(parsed);
      } catch (e) {
        console.error('Failed to parse stored messages:', e);
      }
    }
  }, []);

  // Save chat history to sessionStorage
  useEffect(() => {
    if (messages.length > 0) {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    }
  }, [messages]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (
        contextDropdownRef.current &&
        !contextDropdownRef.current.contains(e.target)
      ) {
        setContextDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSendMessage = useCallback(async () => {
    const trimmed = inputValue.trim();
    if (!trimmed || isLoading) return;

    // Add user message
    const userMessage = {
      id: Date.now(),
      content: trimmed,
      isUser: true,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const payload = { message: trimmed };

      // Add context if selected (simplified - in production, you'd select specific IDs)
      // For now, we just send the message without specific context IDs
      // You can extend this to include skill/quest selection UI

      const response = await api.post('/api/mentor/chat/', payload);

      // Add AI response
      const aiMessage = {
        id: Date.now() + 1,
        content: response.data.response,
        isUser: false,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error('Chat error:', error);

      // Add error message
      const errorMessage = {
        id: Date.now() + 1,
        content:
          error.response?.data?.error ||
          'Sorry, I encountered an error. Please try again.',
        isUser: false,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  }, [inputValue, isLoading]);

  const handleKeyPress = useCallback(
    (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    },
    [handleSendMessage]
  );

  const handleSuggestPath = useCallback(async () => {
    setLoadingSuggestions(true);
    setSuggestions(null);

    try {
      const response = await api.get('/api/mentor/suggest-path/');
      setSuggestions(response.data);
    } catch (error) {
      console.error('Suggestions error:', error);

      // Add error message to chat
      const errorMessage = {
        id: Date.now(),
        content:
          'Sorry, I couldn\'t generate path suggestions right now. Please try again later.',
        isUser: false,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoadingSuggestions(false);
    }
  }, []);

  const handleNavToggle = useCallback(() => {
    setNavOpen((prev) => !prev);
  }, []);

  const handleNavigate = useCallback((path) => {
    setNavOpen(false);
    navigate(path);
  }, [navigate]);

  const handleLogout = useCallback(() => {
    setNavOpen(false);
    logout();
    navigate('/login');
  }, [logout, navigate]);

  const currentContext =
    CONTEXT_OPTIONS.find((opt) => opt.value === contextType) ||
    CONTEXT_OPTIONS[0];

  return (
    <div className="fixed inset-0 bg-[#0a0c10] text-white overflow-hidden">
      {/* Ambient glows */}
      <div className="fixed inset-0 pointer-events-none -z-10">
        <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-purple-600/10 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-600/10 blur-[120px] rounded-full" />
      </div>

      <div className="h-full overflow-y-auto p-6">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="p-3 rounded-2xl bg-gradient-to-br from-primary/20 to-accent/20 shadow-[0_0_30px_rgba(99,102,241,0.3)]">
                <Bot size={28} className="text-primary" />
              </div>
              <div>
                <h1 className="text-4xl font-black tracking-tighter text-white">
                  AI <span className="premium-gradient-text">MENTOR</span>
                </h1>
                <p className="text-slate-400 font-medium text-sm uppercase tracking-wide">
                  Your personal coding guide
                </p>
              </div>
            </div>

            {/* Action Bar */}
            <div className="glass-panel p-4 rounded-2xl flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-3">
                <MessageCircle size={16} className="text-primary" />
                <span className="text-sm font-bold text-slate-300">
                  {messages.length} message{messages.length !== 1 ? 's' : ''}
                </span>
              </div>

              {/* Suggest Path Button */}
              <button
                onClick={handleSuggestPath}
                disabled={loadingSuggestions}
                className={cn(
                  'flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider transition-all duration-300',
                  'bg-gradient-to-r from-primary/80 to-accent/80 border border-primary/40 text-white',
                  'hover:from-primary hover:to-accent hover:shadow-[0_0_20px_rgba(99,102,241,0.4)]',
                  loadingSuggestions && 'opacity-50 cursor-not-allowed'
                )}
              >
                {loadingSuggestions ? (
                  <Loader2 size={13} className="animate-spin" />
                ) : (
                  <Target size={13} />
                )}
                Suggest My Path
              </button>
            </div>
          </motion.div>

          {/* Chat Container */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass-panel rounded-3xl overflow-hidden"
          >
            {/* Messages Area */}
            <div className="h-[500px] overflow-y-auto p-6 space-y-4">
              {messages.length === 0 && !isLoading && (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <div className="p-4 rounded-2xl bg-gradient-to-br from-primary/10 to-accent/10 mb-4">
                    <Sparkles size={32} className="text-primary" />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">
                    Welcome to AI Mentor!
                  </h3>
                  <p className="text-slate-400 text-sm max-w-md">
                    Ask me anything about coding, get help with quests, or
                    request personalized learning path suggestions.
                  </p>
                  <div className="flex flex-wrap gap-2 mt-6">
                    {[
                      'How do I get started?',
                      'Explain algorithms',
                      'Help with debugging',
                    ].map((prompt) => (
                      <button
                        key={prompt}
                        onClick={() => setInputValue(prompt)}
                        className="px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 text-xs font-medium text-slate-300 hover:bg-white/10 hover:border-primary/30 hover:text-primary transition-all duration-200"
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} isUser={msg.isUser} />
              ))}

              {isLoading && <TypingIndicator />}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="border-t border-white/5 p-4 bg-black/20 backdrop-blur-xl">
              <div className="flex items-end gap-3">
                {/* Context Selector */}
                <div className="relative shrink-0" ref={contextDropdownRef}>
                  <button
                    onClick={() => setContextDropdownOpen((v) => !v)}
                    className="flex items-center gap-2 px-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-xs font-bold text-slate-400 hover:bg-white/10 hover:border-primary/30 hover:text-primary transition-all duration-200"
                  >
                    <span>{currentContext.label}</span>
                    <ChevronDown
                      size={11}
                      className={cn(
                        'transition-transform duration-200',
                        contextDropdownOpen && 'rotate-180'
                      )}
                    />
                  </button>

                  <AnimatePresence>
                    {contextDropdownOpen && (
                      <motion.div
                        initial={{ opacity: 0, y: -6, scale: 0.97 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -6, scale: 0.97 }}
                        transition={{ duration: 0.15 }}
                        className="absolute bottom-full left-0 mb-2 z-50 glass-panel rounded-xl overflow-hidden border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.5)] min-w-[160px]"
                      >
                        {CONTEXT_OPTIONS.map((opt) => (
                          <button
                            key={opt.value || 'null'}
                            onClick={() => {
                              setContextType(opt.value);
                              setContextDropdownOpen(false);
                            }}
                            className={cn(
                              'w-full flex items-center gap-2 px-4 py-2.5 text-xs font-bold transition-all duration-150',
                              opt.value === contextType
                                ? 'bg-primary/20 text-primary border-l-2 border-primary'
                                : 'text-slate-400 hover:bg-white/5 hover:text-white'
                            )}
                          >
                            {opt.label}
                          </button>
                        ))}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* Input */}
                <div className="flex-1 relative">
                  <textarea
                    ref={inputRef}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask me anything about coding..."
                    disabled={isLoading}
                    rows={1}
                    className={cn(
                      'w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-sm text-white placeholder-slate-500',
                      'focus:outline-none focus:border-primary/50 focus:bg-white/10',
                      'transition-all duration-300 resize-none',
                      'disabled:opacity-50 disabled:cursor-not-allowed'
                    )}
                    style={{
                      minHeight: '44px',
                      maxHeight: '120px',
                    }}
                  />
                </div>

                {/* Send Button */}
                <button
                  onClick={handleSendMessage}
                  disabled={!inputValue.trim() || isLoading}
                  className={cn(
                    'flex items-center justify-center w-11 h-11 rounded-xl transition-all duration-300 shrink-0',
                    'bg-gradient-to-r from-primary/80 to-accent/80 border border-primary/40 text-white',
                    'hover:from-primary hover:to-accent hover:shadow-[0_0_20px_rgba(99,102,241,0.4)]',
                    'disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:shadow-none'
                  )}
                >
                  {isLoading ? (
                    <Loader2 size={18} className="animate-spin" />
                  ) : (
                    <Send size={18} />
                  )}
                </button>
              </div>

              {/* Hint */}
              <div className="flex items-center gap-2 mt-2 px-1">
                <kbd className="text-[9px] font-bold text-slate-600 uppercase px-1.5 py-0.5 rounded bg-white/5 border border-white/5">
                  Enter
                </kbd>
                <span className="text-[10px] text-slate-600">to send</span>
                <span className="text-slate-700 mx-1">•</span>
                <kbd className="text-[9px] font-bold text-slate-600 uppercase px-1.5 py-0.5 rounded bg-white/5 border border-white/5">
                  Shift+Enter
                </kbd>
                <span className="text-[10px] text-slate-600">for new line</span>
              </div>
            </div>
          </motion.div>

          {/* Suggested Skills */}
          <AnimatePresence>
            {suggestions && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                transition={{ delay: 0.2 }}
                className="mt-6"
              >
                <div className="glass-panel rounded-3xl p-6">
                  {/* Header */}
                  <div className="flex items-center gap-3 mb-4">
                    <TrendingUp size={20} className="text-primary" />
                    <div>
                      <h3 className="text-lg font-black text-white">
                        Your Learning Path
                      </h3>
                      <p className="text-xs text-slate-400">
                        {suggestions.reasoning}
                      </p>
                    </div>
                  </div>

                  {/* Level Badge */}
                  <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/20 border border-primary/30 text-primary text-xs font-bold uppercase tracking-wider mb-4">
                    <Zap size={12} fill="currentColor" />
                    {suggestions.current_level}
                  </div>

                  {/* Skills Grid */}
                  {suggestions.suggested_skills.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {suggestions.suggested_skills.map((skill) => (
                        <SuggestedSkillCard key={skill.id} skill={skill} />
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-slate-400 text-sm">
                        No new skills to suggest right now. Keep completing
                        quests!
                      </p>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Floating Navigation */}
      <FloatingNav
        isOpen={navOpen}
        onToggle={handleNavToggle}
        onNavigate={handleNavigate}
        onLogout={handleLogout}
        user={user}
      />
    </div>
  );
}

export default MentorPage;
