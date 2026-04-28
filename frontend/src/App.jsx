import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Cpu, Zap, Activity, Users, Settings, Award, Shield, Terminal, Database } from 'lucide-react';
import useAuthStore from './store/authStore';
import useUIStore from './store/uiStore';

// Components
import CinemaContainer from './components/layout/CinemaContainer';
import SkillNexus from './components/nexus/SkillNexus';
import ExplodingCard from './components/ui/ExplodingCard';
import SpatialCarousel from './components/ui/SpatialCarousel';
import FocusModeToggle from './components/FocusModeToggle';
import PomodoroTimer from './components/PomodoroTimer';
import BadgeNotificationQueue from './components/BadgeNotificationQueue';

// Styles
import './styles/focusMode.css';

const SidebarItem = ({ icon: Icon, label, active }) => (
  <motion.div
    whileHover={{ x: 10, backgroundColor: 'rgba(255,255,255,0.05)' }}
    className={`flex items-center space-x-4 p-4 cursor-pointer transition-colors ${active ? 'text-primary' : 'text-slate-400'}`}
  >
    <Icon size={20} />
    <span className="text-sm font-medium tracking-wide uppercase">{label}</span>
  </motion.div>
);

/**
 * SkillTree AI Root Component
 * Handles core session rehydration and main layout Shell
 */
const App = () => {
  const { user, rehydrate, isAuthenticated } = useAuthStore();
  const { focusMode } = useUIStore();
  const [activeTab, setActiveTab] = useState('nexus');
  const [selectedNode, setSelectedNode] = useState(null);

  // Call rehydrate on mount as requested
  useEffect(() => {
    rehydrate();
  }, [rehydrate]);

  // Apply focus mode fade transition
  useEffect(() => {
    const main = document.querySelector('main');
    if (main) {
      main.classList.add('focus-mode-transition');
      const timer = setTimeout(() => {
        main.classList.remove('focus-mode-transition');
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [focusMode]);

  const handleNodeClick = (node) => {
    setSelectedNode(node);
  };

  return (
    <div className="relative w-full h-screen bg-background text-foreground font-['Outfit']">
      {/* 3D Background Layer */}
      <CinemaContainer>
        <SkillNexus />
      </CinemaContainer>

      {/* Futuristic Navigation Overlay */}
      <nav className="fixed top-0 left-0 h-full w-20 hover:w-64 glass-panel border-r border-white/5 transition-all duration-500 z-50 group flex flex-col items-center py-8">
        <div className="mb-12">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-[0_0_20px_rgba(99,102,241,0.5)]">
            <Zap className="text-white" fill="white" size={24} />
          </div>
        </div>

        <div className="flex-1 w-full overflow-hidden">
          <SidebarItem icon={Activity} label="Nexus" active={activeTab === 'nexus'} />
          <SidebarItem icon={Cpu} label="Quests" active={activeTab === 'quests'} />
          <SidebarItem icon={Award} label="Achievements" active={activeTab === 'achievements'} />
          <SidebarItem icon={Users} label="Multiplayer" active={activeTab === 'multiplayer'} />
        </div>

        <div className="w-full mt-auto">
          <SidebarItem icon={Settings} label="Settings" />
        </div>
      </nav>

      {/* Top Status Bar */}
      <header className="fixed top-0 left-20 right-0 h-20 px-12 flex items-center justify-between z-40 bg-gradient-to-b from-black/50 to-transparent pointer-events-none">
        <div className="flex items-center space-x-8 pointer-events-auto">
          <div className="glass-card px-6 py-2 rounded-full flex items-center space-x-3">
            <div className={`w-2 h-2 rounded-full ${isAuthenticated ? 'bg-primary animate-pulse' : 'bg-slate-500'}`} />
            <span className="text-xs font-bold tracking-widest text-slate-400 uppercase">
              System: {isAuthenticated ? 'Online' : 'Restricted'}
            </span>
          </div>
          {isAuthenticated && (
            <div className="flex flex-col">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-tighter">Current Level</span>
              <span className="text-2xl font-black tracking-tighter glow-text">LEVEL {user?.level || 1}</span>
            </div>
          )}
        </div>

        <div className="flex items-center space-x-6 pointer-events-auto">
          {isAuthenticated && (
            <>
              <div className="text-right">
                <span className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest">XP Progress</span>
                <div className="w-48 h-1 bg-white/5 rounded-full mt-1 overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min((user?.xp || 0) % 1000 / 10, 100)}%` }}
                    transition={{ duration: 2, ease: "easeOut" }}
                    className="h-full bg-gradient-to-r from-primary to-accent shadow-[0_0_10px_#6366f1]" 
                  />
                </div>
              </div>
              <div className="w-12 h-12 rounded-full border-2 border-primary/30 p-1">
                <img 
                  src={user?.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${user?.username || 'Guest'}`} 
                  alt="Avatar" 
                  className="w-full h-full rounded-full" 
                />
              </div>
            </>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="relative z-30 pt-32 pl-32 pr-12 pb-12 overflow-visible">
        {/* Section 1: Hero */}
        <section className="min-h-screen flex flex-col justify-center max-w-xl">
          {!selectedNode && (
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -50 }}
              transition={{ duration: 0.8, delay: 0.5 }}
            >
              <h1 className="text-7xl font-black tracking-tighter leading-none mb-4">
                WELCOME TO<br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-accent to-primary bg-[length:200%_auto] animate-gradient-flow">THE NEXUS</span>
              </h1>
              <p className="text-slate-400 text-lg max-w-md mb-8 font-light leading-relaxed">
                Your cognitive skill tree has evolved. Explore the nodes, solve challenges, and ascend to the next architectural tier.
              </p>
              <button 
                onClick={() => handleNodeClick({ 
                  title: 'Algorithms', 
                  description: 'Master the fundamental logic that drives the digital world. From sorting to complex graph traversals.' 
                })}
                className="pointer-events-auto px-8 py-4 bg-white text-black font-bold uppercase tracking-widest text-xs hover:bg-primary hover:text-white transition-all duration-500 shadow-[0_10px_30px_rgba(255,255,255,0.1)]"
              >
                Initialize Sequence
              </button>
            </motion.div>
          )}
        </section>

        {/* Section 2: Match History */}
        <section className="min-h-screen flex flex-col justify-center items-center pointer-events-none">
          <motion.div
            initial={{ opacity: 0, y: 100 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false, amount: 0.5 }}
            className="w-full"
          >
            <div className="text-center mb-12">
              <h2 className="text-4xl font-black tracking-tighter uppercase mb-2">Recent Encounters</h2>
              <p className="text-slate-500 text-sm tracking-widest uppercase font-bold">Neural Combat Logs</p>
            </div>
            
            <SpatialCarousel items={[
              { icon: <Terminal className="text-primary" />, title: "The Kernel War", description: "Optimization battle in a virtualized memory space. Won by clock-cycle margin.", footer: "VICTORY +250 XP" },
              { icon: <Shield className="text-accent" />, title: "Vault Breach", description: "Security challenge to decrypt a nested JSON payload while under AI surveillance.", footer: "VICTORY +400 XP" },
              { icon: <Database className="text-emerald-400" />, title: "Query Storm", description: "SQL injection mitigation drill across distributed shards.", footer: "DEFEAT -50 XP" },
              { icon: <Activity className="text-primary" />, title: "Binary Duel", description: "Real-time assembly debugging against a Tier 4 moderator.", footer: "VICTORY +150 XP" },
            ]} />
          </motion.div>
        </section>

        {/* Section 3: System Stats */}
        <section className="min-h-screen flex flex-col justify-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            whileInView={{ opacity: 1, scale: 1 }}
            className="glass-panel p-12 rounded-3xl max-w-4xl mx-auto grid grid-cols-3 gap-12"
          >
            <div className="text-center">
              <div className="text-5xl font-black text-white mb-2">{user?.streak || 0}</div>
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Day Streak</div>
            </div>
            <div className="text-center">
              <div className="text-5xl font-black text-primary mb-2">{user?.xp || 0}</div>
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Total XP</div>
            </div>
            <div className="text-center">
              <div className="text-5xl font-black text-accent mb-2">{user?.level || 1}</div>
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Current Tier</div>
            </div>
          </motion.div>
        </section>
      </main>

      <ExplodingCard 
        isOpen={!!selectedNode} 
        onClose={() => setSelectedNode(null)} 
        data={selectedNode} 
      />

      {/* Focus Mode Components */}
      <FocusModeToggle />
      <PomodoroTimer />
      <BadgeNotificationQueue />

      {/* Depth Vignette */}
      <div className="fixed inset-0 pointer-events-none shadow-[inset_0_0_200px_rgba(0,0,0,0.8)] z-20" />
    </div>
  );
};

export default App;
