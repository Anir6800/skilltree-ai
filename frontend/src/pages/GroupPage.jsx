/**
 * SkillTree AI - Study Groups Page
 * Create, join, and manage study groups with real-time chat and shared goals.
 * Redesigned with glassmorphism design system.
 */

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users, MessageCircle, Target, Plus, LogOut, Copy, Check,
  Loader2, AlertCircle, Send, Trophy, Calendar,
} from 'lucide-react';
import {
  createGroup, joinGroup, getMyGroup, getGroupLeaderboard,
  getGroupGoals, createGroupGoal, getGroupMessages, leaveGroup,
} from '../api/groupsApi';
import { getSkills } from '../api/skillApi';
import { useGroupChat } from '../hooks/useGroupChat';
import MainLayout from '../components/layout/MainLayout';
import { cn } from '../utils/cn';

const TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: Users },
  { id: 'goals',     label: 'Goals',     icon: Target },
  { id: 'chat',      label: 'Chat',      icon: MessageCircle },
];

export default function GroupPage() {
  const [group, setGroup] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [copied, setCopied] = useState(false);

  const [createGroupName, setCreateGroupName] = useState('');
  const [joinInviteCode, setJoinInviteCode] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showJoinForm, setShowJoinForm] = useState(false);

  const [leaderboard, setLeaderboard] = useState([]);
  const [goals, setGoals] = useState([]);
  const [skills, setSkills] = useState([]);
  const [newGoalSkillId, setNewGoalSkillId] = useState('');
  const [newGoalDate, setNewGoalDate] = useState('');

  const { messages, typingUsers, isConnected, sendMessage, sendTyping } = useGroupChat(group?.id);
  const [messageText, setMessageText] = useState('');
  const messagesEndRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  useEffect(() => { loadGroup(); }, []);

  useEffect(() => {
    if (group) {
      loadLeaderboard();
      loadGoals();
      loadSkills();
    }
  }, [group]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadGroup = async () => {
    try {
      setLoading(true);
      const data = await getMyGroup();
      setGroup(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      setGroup(null);
    } finally {
      setLoading(false);
    }
  };

  const loadLeaderboard = async () => {
    try {
      const data = await getGroupLeaderboard(group.id);
      setLeaderboard(data.leaderboard || []);
    } catch { /* silent */ }
  };

  const loadGoals = async () => {
    try {
      const data = await getGroupGoals(group.id);
      setGoals(data);
    } catch { /* silent */ }
  };

  const loadSkills = async () => {
    try {
      const data = await getSkills();
      setSkills(data.results || data);
    } catch { /* silent */ }
  };

  const handleCreateGroup = async (e) => {
    e.preventDefault();
    if (!createGroupName.trim()) return;
    try {
      const newGroup = await createGroup(createGroupName);
      setGroup(newGroup);
      setCreateGroupName('');
      setShowCreateForm(false);
      setError(null);
    } catch (err) { setError(err.message); }
  };

  const handleJoinGroup = async (e) => {
    e.preventDefault();
    if (!joinInviteCode.trim()) return;
    try {
      const newGroup = await joinGroup(joinInviteCode);
      setGroup(newGroup);
      setJoinInviteCode('');
      setShowJoinForm(false);
      setError(null);
    } catch (err) { setError(err.message); }
  };

  const handleCreateGoal = async (e) => {
    e.preventDefault();
    if (!newGoalSkillId || !newGoalDate) return;
    try {
      await createGroupGoal(group.id, newGoalSkillId, newGoalDate);
      setNewGoalSkillId('');
      setNewGoalDate('');
      await loadGoals();
    } catch (err) { setError(err.message); }
  };

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!messageText.trim() || !isConnected) return;
    sendMessage(messageText);
    setMessageText('');
  };

  const handleMessageChange = (e) => {
    setMessageText(e.target.value);
    if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    sendTyping('');
    typingTimeoutRef.current = setTimeout(() => { typingTimeoutRef.current = null; }, 3000);
  };

  const handleLeaveGroup = async () => {
    if (!window.confirm('Are you sure you want to leave this group?')) return;
    try {
      await leaveGroup(group.id);
      setGroup(null);
      setError(null);
    } catch (err) { setError(err.message); }
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(group.invite_code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  // ── Loading ──
  if (loading) {
    return (
      <MainLayout>
        <div className="min-h-screen bg-[#0a0c10] flex items-center justify-center">
          <div className="glass-panel p-12 rounded-3xl text-center">
            <Loader2 size={40} className="text-primary animate-spin mx-auto mb-4" />
            <p className="text-slate-400 text-sm">Loading group...</p>
          </div>
        </div>
      </MainLayout>
    );
  }

  // ── No group — join/create ──
  if (!group) {
    return (
      <MainLayout>
        <div className="min-h-screen bg-[#0a0c10] text-white p-6 flex items-center justify-center">
          <div className="fixed inset-0 pointer-events-none">
            <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-purple-600/10 blur-[120px] rounded-full" />
            <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-600/10 blur-[120px] rounded-full" />
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="relative z-10 glass-panel p-10 rounded-3xl max-w-md w-full text-center"
          >
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-accent/20 border border-primary/30 flex items-center justify-center mx-auto mb-6">
              <Users size={28} className="text-primary" />
            </div>
            <h1 className="text-2xl font-black mb-2">Study Groups</h1>
            <p className="text-slate-400 text-sm mb-8">
              Join or create a study group to collaborate with other learners.
            </p>

            {error && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm mb-6"
              >
                <AlertCircle size={16} />
                {error}
              </motion.div>
            )}

            <AnimatePresence mode="wait">
              {!showCreateForm && !showJoinForm && (
                <motion.div
                  key="buttons"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex gap-3"
                >
                  <button
                    onClick={() => setShowCreateForm(true)}
                    className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl bg-gradient-to-r from-primary to-accent text-white font-bold text-sm uppercase tracking-wider hover:shadow-[0_0_20px_rgba(99,102,241,0.4)] transition-all"
                  >
                    <Plus size={16} /> Create
                  </button>
                  <button
                    onClick={() => setShowJoinForm(true)}
                    className="flex-1 py-3 rounded-xl bg-white/5 border border-white/10 text-slate-300 font-bold text-sm uppercase tracking-wider hover:bg-white/10 transition-all"
                  >
                    Join
                  </button>
                </motion.div>
              )}

              {showCreateForm && (
                <motion.form
                  key="create"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  onSubmit={handleCreateGroup}
                  className="space-y-3"
                >
                  <input
                    type="text"
                    placeholder="Group name"
                    value={createGroupName}
                    onChange={(e) => setCreateGroupName(e.target.value)}
                    maxLength={100}
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-primary/50 transition-all"
                  />
                  <div className="flex gap-2">
                    <button type="submit" className="flex-1 py-3 rounded-xl bg-gradient-to-r from-primary to-accent text-white font-bold text-sm">Create</button>
                    <button type="button" onClick={() => setShowCreateForm(false)} className="flex-1 py-3 rounded-xl bg-white/5 border border-white/10 text-slate-300 font-bold text-sm">Cancel</button>
                  </div>
                </motion.form>
              )}

              {showJoinForm && (
                <motion.form
                  key="join"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  onSubmit={handleJoinGroup}
                  className="space-y-3"
                >
                  <input
                    type="text"
                    placeholder="Invite code (e.g., ABC123)"
                    value={joinInviteCode}
                    onChange={(e) => setJoinInviteCode(e.target.value.toUpperCase())}
                    maxLength={6}
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-primary/50 transition-all font-mono tracking-widest"
                  />
                  <div className="flex gap-2">
                    <button type="submit" className="flex-1 py-3 rounded-xl bg-gradient-to-r from-primary to-accent text-white font-bold text-sm">Join</button>
                    <button type="button" onClick={() => setShowJoinForm(false)} className="flex-1 py-3 rounded-xl bg-white/5 border border-white/10 text-slate-300 font-bold text-sm">Cancel</button>
                  </div>
                </motion.form>
              )}
            </AnimatePresence>
          </motion.div>
        </div>
      </MainLayout>
    );
  }

  // ── Group view ──
  return (
    <MainLayout>
      <div className="min-h-screen bg-[#0a0c10] text-white p-4 md:p-8 max-w-5xl mx-auto">
        <div className="fixed inset-0 pointer-events-none -z-10">
          <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-purple-600/10 blur-[120px] rounded-full" />
          <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-600/10 blur-[120px] rounded-full" />
        </div>

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel p-6 rounded-3xl mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4"
        >
          <div>
            <h1 className="text-2xl font-black text-white mb-1">{group.name}</h1>
            <div className="flex items-center gap-4 text-sm text-slate-400">
              <span className="flex items-center gap-1.5">
                <Users size={14} />
                {group.member_count}/{group.max_members} members
              </span>
              <button
                onClick={handleCopyCode}
                className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-all font-mono text-xs"
              >
                {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                {group.invite_code}
              </button>
            </div>
          </div>
          <button
            onClick={handleLeaveGroup}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 font-bold text-sm hover:bg-red-500/20 transition-all"
          >
            <LogOut size={16} /> Leave Group
          </button>
        </motion.div>

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-2 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm mb-6"
            >
              <AlertCircle size={16} /> {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  'flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all duration-200',
                  activeTab === tab.id
                    ? 'bg-primary/20 border border-primary/40 text-primary'
                    : 'bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10'
                )}
              >
                <Icon size={15} /> {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          {/* Dashboard */}
          {activeTab === 'dashboard' && (
            <motion.div
              key="dashboard"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="space-y-6"
            >
              {/* Members */}
              <div className="glass-panel p-6 rounded-3xl">
                <h2 className="text-lg font-black mb-4 flex items-center gap-2">
                  <Users size={18} className="text-primary" /> Members
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {group.members?.map((member) => (
                    <div key={member.user_id} className="glass-card p-4 rounded-2xl flex items-center gap-3">
                      <img
                        src={member.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${member.username}`}
                        alt={member.username}
                        className="w-10 h-10 rounded-full border border-white/20"
                      />
                      <div className="min-w-0">
                        <p className="text-sm font-bold text-white truncate">{member.username}</p>
                        <p className="text-xs text-slate-400">Lv {member.level} · {member.xp} XP</p>
                        {member.role === 'owner' && (
                          <span className="text-[10px] font-bold text-primary uppercase tracking-wider">Owner</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Weekly XP Leaderboard */}
              <div className="glass-panel p-6 rounded-3xl">
                <h2 className="text-lg font-black mb-4 flex items-center gap-2">
                  <Trophy size={18} className="text-amber-400" /> This Week's XP
                </h2>
                <div className="space-y-3">
                  {leaderboard.map((member, index) => (
                    <div key={member.user_id} className="flex items-center gap-3">
                      <span className={cn(
                        'w-7 h-7 rounded-full flex items-center justify-center text-xs font-black',
                        index === 0 ? 'bg-yellow-400 text-black' :
                        index === 1 ? 'bg-slate-300 text-black' :
                        index === 2 ? 'bg-orange-400 text-black' : 'bg-white/10 text-slate-400'
                      )}>
                        {index + 1}
                      </span>
                      <span className="text-sm font-bold text-white flex-1">{member.username}</span>
                      <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-primary to-accent rounded-full"
                          style={{ width: `${Math.min((member.xp_this_week / 1000) * 100, 100)}%` }}
                        />
                      </div>
                      <span className="text-sm font-black text-primary w-16 text-right">{member.xp_this_week} XP</span>
                    </div>
                  ))}
                  {leaderboard.length === 0 && (
                    <p className="text-slate-500 text-sm text-center py-4">No XP earned this week yet.</p>
                  )}
                </div>
              </div>
            </motion.div>
          )}

          {/* Goals */}
          {activeTab === 'goals' && (
            <motion.div
              key="goals"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="space-y-6"
            >
              <div className="glass-panel p-6 rounded-3xl">
                <h2 className="text-lg font-black mb-4 flex items-center gap-2">
                  <Target size={18} className="text-primary" /> Shared Goals
                </h2>
                {goals.length === 0 ? (
                  <p className="text-slate-500 text-sm text-center py-6">No goals yet. Create one below!</p>
                ) : (
                  <div className="space-y-3">
                    {goals.map((goal) => (
                      <div key={goal.id} className="glass-card p-4 rounded-2xl">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="text-sm font-bold text-white">{goal.skill_title}</h3>
                          {goal.completed && (
                            <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 text-xs font-bold">✓ Done</span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 text-xs text-slate-400 mb-2">
                          <Calendar size={12} />
                          Target: {new Date(goal.target_date).toLocaleDateString()}
                          {goal.days_remaining > 0
                            ? ` · ${goal.days_remaining} days left`
                            : ' · Deadline passed'}
                        </div>
                        <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-primary to-accent rounded-full"
                            style={{ width: goal.completed ? '100%' : '0%' }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Create goal */}
              <div className="glass-panel p-6 rounded-3xl">
                <h2 className="text-lg font-black mb-4">Create New Goal</h2>
                <form onSubmit={handleCreateGoal} className="space-y-3">
                  <select
                    value={newGoalSkillId}
                    onChange={(e) => setNewGoalSkillId(e.target.value)}
                    required
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:border-primary/50 transition-all"
                  >
                    <option value="">Select a skill</option>
                    {skills.map((skill) => (
                      <option key={skill.id} value={skill.id}>{skill.title}</option>
                    ))}
                  </select>
                  <input
                    type="date"
                    value={newGoalDate}
                    onChange={(e) => setNewGoalDate(e.target.value)}
                    required
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:border-primary/50 transition-all"
                  />
                  <button
                    type="submit"
                    className="w-full py-3 rounded-xl bg-gradient-to-r from-primary to-accent text-white font-bold text-sm uppercase tracking-wider hover:shadow-[0_0_20px_rgba(99,102,241,0.4)] transition-all"
                  >
                    Create Goal
                  </button>
                </form>
              </div>
            </motion.div>
          )}

          {/* Chat */}
          {activeTab === 'chat' && (
            <motion.div
              key="chat"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="glass-panel rounded-3xl overflow-hidden flex flex-col"
              style={{ height: '60vh' }}
            >
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={cn(
                      'flex gap-3',
                      msg.is_system && 'justify-center'
                    )}
                  >
                    {!msg.is_system && (
                      <img
                        src={msg.sender_avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${msg.sender_username}`}
                        alt={msg.sender_username}
                        className="w-8 h-8 rounded-full border border-white/20 flex-shrink-0"
                      />
                    )}
                    <div className={msg.is_system ? 'text-center' : ''}>
                      {!msg.is_system && (
                        <p className="text-xs font-bold text-primary mb-1">{msg.sender_username}</p>
                      )}
                      <p className={cn(
                        'text-sm',
                        msg.is_system ? 'text-slate-500 italic text-xs' : 'text-slate-200'
                      )}>
                        {msg.text}
                      </p>
                      <p className="text-[10px] text-slate-600 mt-1">
                        {new Date(msg.sent_at).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}
                {typingUsers?.size > 0 && (
                  <div className="flex items-center gap-2 text-xs text-slate-500 italic">
                    <div className="flex gap-1">
                      {[0, 1, 2].map((i) => (
                        <div key={i} className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: `${i * 150}ms` }} />
                      ))}
                    </div>
                    Someone is typing...
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <form onSubmit={handleSendMessage} className="p-4 border-t border-white/10 flex gap-2">
                <input
                  type="text"
                  placeholder={isConnected ? 'Type a message...' : 'Connecting...'}
                  value={messageText}
                  onChange={handleMessageChange}
                  disabled={!isConnected}
                  maxLength={1000}
                  className="flex-1 px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-primary/50 transition-all text-sm disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={!isConnected || !messageText.trim()}
                  className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-primary to-accent text-white font-bold disabled:opacity-50 transition-all hover:shadow-[0_0_16px_rgba(99,102,241,0.4)]"
                >
                  <Send size={16} />
                </button>
              </form>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </MainLayout>
  );
}
