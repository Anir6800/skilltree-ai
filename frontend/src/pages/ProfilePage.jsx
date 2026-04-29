/**
 * SkillTree AI - Profile Page
 * User profile with stats, achievements, and settings
 * @module pages/ProfilePage
 */

import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { User, Settings, Trophy, Zap, Target, Clock, LogOut, Edit2, Check, X } from 'lucide-react';
import useAuthStore from '../store/authStore';
import useSkillStore from '../store/skillStore';
import useQuestStore from '../store/questStore';
import * as authApi from '../api/authApi';
import api from '../api/api';
import { formatXP, formatDate } from '../utils/formatters';
import { calculateXPProgress } from '../utils/xp';
import { getLevelFromXP, getRankFromLevel } from '../constants';
import { cn } from '../utils/cn';
import SkillRadarChart from '../components/profile/SkillRadarChart';
import MainLayout from '../components/layout/MainLayout';

/**
 * Profile page component
 * @returns {JSX.Element} Profile page
 */
function ProfilePage() {
  const navigate = useNavigate();
  const { user, fetchUser, updateUser, logout } = useAuthStore();
  const { skills, fetchSkills, progressStats } = useSkillStore();
  const { completedQuests, fetchCompletedQuests } = useQuestStore();
  
  const [activeTab, setActiveTab] = useState('overview');
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [badges, setBadges] = useState([]);

  useEffect(() => {
    fetchUser();
    fetchSkills();
    fetchCompletedQuests();
    api.get('/api/users/badges/')
      .then((res) => setBadges(res.data.results || []))
      .catch((err) => console.error('Failed to fetch badges:', err));
  }, [fetchUser, fetchSkills, fetchCompletedQuests]);

  useEffect(() => {
    const refreshBadges = () => {
      api.get('/api/users/badges/')
        .then((res) => setBadges(res.data.results || []))
        .catch(() => {});
    };
    window.addEventListener('badgeEarned', refreshBadges);
    return () => window.removeEventListener('badgeEarned', refreshBadges);
  }, []);

  useEffect(() => {
    if (user) {
      setEditForm({
        username: user.username || '',
        email: user.email || '',
        avatar: user.avatar || '',
      });
    }
  }, [user]);

  /**
   * Handle form change
   * @param {React.ChangeEvent<HTMLInputElement>} e - Change event
   */
  const handleChange = (e) => {
    const { name, value } = e.target;
    setEditForm((prev) => ({ ...prev, [name]: value }));
  };

  /**
   * Handle profile update
   */
  const handleUpdate = async () => {
    setIsLoading(true);
    try {
      const updated = await authApi.updateProfile(editForm);
      updateUser(updated);
      setIsEditing(false);
    } catch (e) {
      console.error('Failed to update profile:', e);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle logout
   */
  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const level = user?.level || getLevelFromXP(user?.xp || 0);
  const rank = user?.rank || getRankFromLevel(level);
  const xpProgress = calculateXPProgress(user?.xp || 0, level);

  return (
    <MainLayout>
    <div className="min-h-screen bg-[#0a0c10] text-white overflow-hidden">
      {/* Ambient background */}
      <div className="fixed inset-0 pointer-events-none -z-10">
        <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-purple-600/10 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-600/10 blur-[120px] rounded-full" />
      </div>

      <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
        {/* Profile Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel rounded-3xl p-8 border border-primary/20 shadow-[0_0_60px_rgba(99,102,241,0.15)]"
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Avatar Section */}
            <div className="flex flex-col items-center gap-4">
              <motion.div
                whileHover={{ scale: 1.05 }}
                className="relative w-32 h-32 rounded-2xl bg-gradient-to-br from-primary/30 to-accent/30 border-2 border-primary/40 flex items-center justify-center text-6xl overflow-hidden shadow-[0_0_40px_rgba(99,102,241,0.3)]"
              >
                {user?.avatar ? (
                  <img src={user.avatar} alt={user.username} className="w-full h-full object-cover" />
                ) : (
                  <User size={64} className="text-primary" />
                )}
              </motion.div>
              {isEditing ? (
                <input
                  type="text"
                  name="avatar"
                  value={editForm.avatar}
                  onChange={handleChange}
                  placeholder="Avatar URL"
                  className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-primary/50"
                />
              ) : (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setIsEditing(true)}
                  className="px-4 py-2 rounded-lg bg-primary/20 border border-primary/40 text-primary text-sm font-bold hover:bg-primary/30 transition-all"
                >
                  <Edit2 size={14} className="inline mr-2" />
                  Edit
                </motion.button>
              )}
            </div>

            {/* User Info Section */}
            <div className="md:col-span-2 space-y-4">
              {isEditing ? (
                <div className="space-y-3">
                  <input
                    type="text"
                    name="username"
                    value={editForm.username}
                    onChange={handleChange}
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-primary/50 font-bold text-xl"
                    placeholder="Username"
                  />
                  <input
                    type="email"
                    name="email"
                    value={editForm.email}
                    onChange={handleChange}
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-primary/50"
                    placeholder="Email"
                  />
                  <div className="flex gap-3">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={handleUpdate}
                      disabled={isLoading}
                      className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-gradient-to-r from-primary to-accent text-white font-bold hover:shadow-[0_0_20px_rgba(99,102,241,0.4)] transition-all disabled:opacity-50"
                    >
                      <Check size={16} />
                      {isLoading ? 'Saving...' : 'Save'}
                    </motion.button>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => setIsEditing(false)}
                      className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-slate-300 font-bold hover:bg-white/10 transition-all"
                    >
                      <X size={16} />
                      Cancel
                    </motion.button>
                  </div>
                </div>
              ) : (
                <>
                  <div>
                    <h1 className="text-4xl font-black text-white mb-1">{user?.username}</h1>
                    <p className="text-slate-400 text-sm">{user?.email}</p>
                  </div>
                  <div className="flex flex-wrap gap-3">
                    <motion.div
                      whileHover={{ scale: 1.05 }}
                      className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500/20 to-yellow-500/20 border border-amber-500/40 text-amber-400 font-bold text-sm"
                    >
                      Level {level}
                    </motion.div>
                    <motion.div
                      whileHover={{ scale: 1.05 }}
                      className="px-4 py-2 rounded-xl bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/40 text-purple-400 font-bold text-sm"
                    >
                      {rank}
                    </motion.div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Stats Summary */}
          <div className="grid grid-cols-3 gap-4 mt-8 pt-8 border-t border-white/10">
            {[
              { label: 'Total XP', value: formatXP(user?.xp || 0), icon: Zap },
              { label: 'Skills', value: progressStats?.completed || 0, icon: Target },
              { label: 'Quests', value: completedQuests?.length || 0, icon: Trophy },
            ].map((stat, i) => {
              const Icon = stat.icon;
              return (
                <motion.div
                  key={i}
                  whileHover={{ scale: 1.05 }}
                  className="text-center"
                >
                  <Icon size={20} className="text-primary mx-auto mb-2" />
                  <div className="text-2xl font-black text-white">{stat.value}</div>
                  <div className="text-xs text-slate-400 uppercase tracking-wider">{stat.label}</div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>

        {/* XP Progress */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-panel rounded-2xl p-6 border border-primary/20"
        >
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm font-bold uppercase tracking-wider text-slate-400">Level Progress</span>
            <span className="text-sm font-bold text-primary">{xpProgress}%</span>
          </div>
          <div className="h-3 bg-white/5 rounded-full overflow-hidden border border-white/10">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${xpProgress}%` }}
              transition={{ duration: 1, ease: 'easeOut' }}
              className="h-full bg-gradient-to-r from-primary to-accent rounded-full shadow-[0_0_20px_rgba(99,102,241,0.6)]"
            />
          </div>
          <div className="flex justify-between mt-3 text-xs text-slate-400">
            <span>{user?.xp || 0} XP</span>
            <span>{formatXP(user?.xpToNextLevel || 100)} to next level</span>
          </div>
        </motion.div>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-white/10 overflow-x-auto">
          {[
            { id: 'overview', label: 'Overview', icon: User },
            { id: 'skills', label: 'Skills', icon: Target },
            { id: 'achievements', label: 'Achievements', icon: Trophy },
            { id: 'settings', label: 'Settings', icon: Settings },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <motion.button
                key={tab.id}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  'flex items-center gap-2 px-4 py-3 text-sm font-bold uppercase tracking-wider transition-all relative',
                  activeTab === tab.id
                    ? 'text-primary'
                    : 'text-slate-400 hover:text-slate-300'
                )}
              >
                <Icon size={16} />
                {tab.label}
                {activeTab === tab.id && (
                  <motion.div
                    layoutId="activeTab"
                    className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-primary to-accent"
                  />
                )}
              </motion.button>
            );
          })}
        </div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Skill Radar Chart */}
                <SkillRadarChart />

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {[
                    { icon: '🎯', label: 'Skills Completed', value: progressStats?.completed || 0 },
                    { icon: '📜', label: 'Quests Completed', value: completedQuests?.length || 0 },
                    { icon: '🔥', label: 'Day Streak', value: user?.streak || 0 },
                    { icon: '⏱️', label: 'Total Time', value: `${user?.totalTime || 0}h` },
                  ].map((stat, i) => (
                    <motion.div
                      key={i}
                      whileHover={{ scale: 1.05, y: -5 }}
                      className="glass-panel rounded-2xl p-6 border border-primary/20 text-center hover:shadow-[0_0_30px_rgba(99,102,241,0.2)] transition-all"
                    >
                      <div className="text-4xl mb-3">{stat.icon}</div>
                      <div className="text-3xl font-black text-white mb-1">{stat.value}</div>
                      <div className="text-xs text-slate-400 uppercase tracking-wider">{stat.label}</div>
                    </motion.div>
                  ))}
                </div>

                {/* Recent Activity */}
                <motion.div
                  whileHover={{ scale: 1.02 }}
                  className="glass-panel rounded-2xl p-6 border border-primary/20"
                >
                  <h3 className="text-lg font-black text-white mb-4 flex items-center gap-2">
                    <Clock size={20} className="text-primary" />
                    Recent Activity
                  </h3>
                  <div className="space-y-3">
                    {user?.recentActivity?.length > 0 ? (
                      user.recentActivity.map((activity, i) => (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.05 }}
                          className="flex items-center gap-4 p-3 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all"
                        >
                          <span className="text-2xl">{activity.icon}</span>
                          <div className="flex-1">
                            <div className="text-sm font-bold text-white">{activity.title}</div>
                            <div className="text-xs text-slate-500">{formatDate(activity.timestamp)}</div>
                          </div>
                          <span className="text-sm font-bold text-primary">+{activity.xp} XP</span>
                        </motion.div>
                      ))
                    ) : (
                      <p className="text-center text-slate-400 py-8">No recent activity</p>
                    )}
                  </div>
                </motion.div>
              </div>
            )}

            {activeTab === 'skills' && (
              <div className="space-y-6">
                <motion.div
                  whileHover={{ scale: 1.02 }}
                  className="glass-panel rounded-2xl p-6 border border-primary/20"
                >
                  <h3 className="text-lg font-black text-white mb-2">Skill Progress</h3>
                  <div className="text-sm text-slate-400">
                    {progressStats?.completed || 0} / {progressStats?.total || 0} completed
                  </div>
                </motion.div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {skills.slice(0, 10).map((skill, i) => (
                    <motion.div
                      key={skill.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                      whileHover={{ scale: 1.05, y: -5 }}
                    >
                      <Link
                        to={`/skills/${skill.id}`}
                        className="glass-panel rounded-2xl p-4 border border-primary/20 flex items-center gap-4 hover:shadow-[0_0_30px_rgba(99,102,241,0.2)] transition-all block"
                      >
                        <span className="text-3xl">{skill.icon || '📚'}</span>
                        <div className="flex-1">
                          <div className="font-bold text-white">{skill.name}</div>
                          <div className={cn(
                            'text-xs font-bold uppercase tracking-wider',
                            skill.status === 'completed' ? 'text-emerald-400' : 'text-slate-400'
                          )}>
                            {skill.status}
                          </div>
                        </div>
                      </Link>
                    </motion.div>
                  ))}
                </div>
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Link
                    to="/skills"
                    className="w-full py-3 rounded-xl bg-gradient-to-r from-primary/80 to-accent/80 text-white font-bold text-center hover:from-primary hover:to-accent transition-all"
                  >
                    View All Skills
                  </Link>
                </motion.div>
              </div>
            )}

            {activeTab === 'achievements' && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {badges.length > 0 ? (
                  badges.map((badge, i) => (
                    <motion.div
                      key={badge.id}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: i * 0.05 }}
                      whileHover={{ scale: 1.05, y: -5 }}
                      title={badge.description}
                      className={cn(
                        'glass-panel rounded-2xl p-6 border text-center transition-all relative overflow-hidden',
                        badge.unlocked
                          ? 'border-primary/25 hover:shadow-[0_0_30px_rgba(99,102,241,0.25)]'
                          : 'border-white/10 opacity-55 grayscale'
                      )}
                    >
                      {badge.unlocked && (
                        <div className="absolute inset-0 pointer-events-none bg-gradient-to-br from-white/5 to-transparent" />
                      )}
                      <div className="text-5xl mb-3">{badge.icon_emoji || '🏆'}</div>
                      <h4 className="font-bold text-white mb-1">{badge.name}</h4>
                      <p className="text-xs text-slate-400 mb-3 line-clamp-2">{badge.description}</p>
                      <span className={cn(
                        'inline-flex px-2.5 py-1 rounded-full border text-[10px] font-black uppercase tracking-wider',
                        badge.rarity === 'legendary' && 'border-amber-400/40 text-amber-300 bg-amber-500/10',
                        badge.rarity === 'epic' && 'border-purple-400/40 text-purple-300 bg-purple-500/10',
                        badge.rarity === 'rare' && 'border-blue-400/40 text-blue-300 bg-blue-500/10',
                        badge.rarity === 'common' && 'border-slate-400/30 text-slate-300 bg-slate-500/10'
                      )}>
                        {badge.unlocked ? badge.rarity : 'Locked'}
                      </span>
                      {badge.unlocked && badge.earned_at && (
                        <div className="mt-3 text-[10px] text-slate-500 uppercase tracking-wider">
                          {formatDate(badge.earned_at)}
                        </div>
                      )}
                    </motion.div>
                  ))
                ) : (
                  <div className="col-span-full text-center py-12">
                    <Trophy size={48} className="text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-400">No achievements yet. Keep learning!</p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'settings' && (
              <motion.div
                whileHover={{ scale: 1.02 }}
                className="glass-panel rounded-2xl p-8 border border-primary/20 space-y-8"
              >
                <div>
                  <h3 className="text-lg font-black text-white mb-4 flex items-center gap-2">
                    <Settings size={20} className="text-primary" />
                    Account Settings
                  </h3>
                </div>

                <div className="space-y-4">
                  <h4 className="text-sm font-bold uppercase tracking-wider text-slate-400">Security</h4>
                  <div className="space-y-2">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white font-bold hover:bg-white/10 transition-all text-left"
                    >
                      Change Password
                    </motion.button>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white font-bold hover:bg-white/10 transition-all text-left"
                    >
                      Enable 2FA
                    </motion.button>
                  </div>
                </div>

                <div className="space-y-4">
                  <h4 className="text-sm font-bold uppercase tracking-wider text-slate-400">Notifications</h4>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input type="checkbox" defaultChecked className="w-4 h-4 rounded" />
                    <span className="text-sm text-white">Email notifications</span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input type="checkbox" defaultChecked className="w-4 h-4 rounded" />
                    <span className="text-sm text-white">Push notifications</span>
                  </label>
                </div>

                <div className="pt-4 border-t border-white/10">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleLogout}
                    className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-red-500/20 to-red-600/20 border border-red-500/40 text-red-400 font-bold hover:from-red-500/30 hover:to-red-600/30 hover:shadow-[0_0_20px_rgba(239,68,68,0.4)] transition-all"
                  >
                    <LogOut size={18} />
                    Log Out
                  </motion.button>
                </div>
              </motion.div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
    </MainLayout>
  );
}

export default ProfilePage;
