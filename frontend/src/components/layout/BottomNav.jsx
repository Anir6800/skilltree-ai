/**
 * SkillTree AI - Bottom Navigation Bar
 * Glassmorphic bottom nav with navigation to key pages
 * @module components/layout/BottomNav
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Home, 
  Network, 
  Target, 
  Swords, 
  Trophy, 
  Bot,
  User,
  MoreHorizontal,
  Users,
  Code2,
  BarChart2,
  X,
} from 'lucide-react';
import { cn } from '../../utils/cn';
import useAuthStore from '../../store/authStore';

/**
 * Nav Item Component
 */
const NavItem = ({ item, isActive, onClick }) => {
  const Icon = item.icon;

  return (
    <motion.button
      onClick={onClick}
      whileHover={{ y: -4 }}
      whileTap={{ scale: 0.95 }}
      className={cn(
        'relative flex flex-col items-center justify-center gap-1 px-4 py-2 rounded-xl transition-all duration-300',
        isActive
          ? 'text-primary'
          : 'text-slate-400 hover:text-white'
      )}
    >
      {/* Active indicator */}
      {isActive && (
        <motion.div
          layoutId="activeTab"
          className="absolute inset-0 bg-primary/10 border border-primary/30 rounded-xl"
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        />
      )}

      {/* Icon with glow effect */}
      <div className="relative z-10">
        <Icon 
          size={22} 
          className={cn(
            'transition-all duration-300',
            isActive && 'drop-shadow-[0_0_8px_rgba(99,102,241,0.8)]'
          )}
        />
      </div>

      {/* Label */}
      <span
        className={cn(
          'relative z-10 text-[10px] font-bold uppercase tracking-wider transition-all duration-300',
          isActive && 'text-primary'
        )}
      >
        {item.label}
      </span>

      {/* Glow effect on hover */}
      {isActive && (
        <motion.div
          className="absolute inset-0 bg-primary/5 rounded-xl blur-xl"
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
    </motion.button>
  );
};

/** More menu items — secondary pages accessible via overflow menu */
const moreItems = [
  { id: 'groups',    label: 'Groups',    icon: Users,    path: '/groups' },
  { id: 'solutions', label: 'Solutions', icon: Code2,    path: '/solutions' },
  { id: 'reports',   label: 'Reports',   icon: BarChart2, path: '/reports' },
];

/**
 * Bottom Navigation Bar Component
 */
const BottomNav = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuthStore();
  const [showMore, setShowMore] = useState(false);

  const handleNavigation = (path) => {
    setShowMore(false);
    navigate(path);
  };

  // Primary nav items
  const navItems = [
    { id: 'dashboard',   label: 'Home',    icon: Home,   path: '/dashboard' },
    { id: 'skills',      label: 'Skills',  icon: Network, path: '/skills' },
    { id: 'quests',      label: 'Quests',  icon: Target,  path: '/quests' },
    { id: 'mentor',      label: 'Mentor',  icon: Bot,     path: '/mentor' },
    { id: 'arena',       label: 'Arena',   icon: Swords,  path: '/arena' },
    { id: 'leaderboard', label: 'Ranks',   icon: Trophy,  path: '/leaderboard' },
    { id: 'profile',     label: 'Profile', icon: User,    path: `/profile/${user?.id || ''}` },
  ];

  // Check if any "more" item is currently active
  const isMoreActive = moreItems.some(
    (item) => location.pathname === item.path || location.pathname.startsWith(item.path)
  );

  return (
    <>
      {/* More menu overlay */}
      <AnimatePresence>
        {showMore && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="fixed bottom-28 left-1/2 -translate-x-1/2 z-50"
          >
            <div className="glass-panel px-4 py-3 rounded-2xl border-white/10 shadow-2xl backdrop-blur-3xl flex items-center gap-2">
              {moreItems.map((item) => {
                const isActive = location.pathname === item.path || location.pathname.startsWith(item.path);
                return (
                  <NavItem
                    key={item.id}
                    item={item}
                    isActive={isActive}
                    onClick={() => handleNavigation(item.path)}
                  />
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.nav
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50"
      >
        {/* Glass container */}
        <div className="glass-panel px-4 py-3 rounded-2xl border-white/10 shadow-2xl backdrop-blur-3xl">
          <div className="absolute -top-12 -left-12 w-32 h-32 bg-primary/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-12 -right-12 w-32 h-32 bg-accent/10 rounded-full blur-3xl pointer-events-none" />

          <div className="relative flex items-center gap-2">
            {navItems.map((item) => {
              const isActive =
                location.pathname === item.path ||
                (item.path !== '/dashboard' && location.pathname.startsWith(item.path));
              return (
                <NavItem
                  key={item.id}
                  item={item}
                  isActive={isActive}
                  onClick={() => handleNavigation(item.path)}
                />
              );
            })}

            {/* More button */}
            <NavItem
              item={{ id: 'more', label: 'More', icon: showMore ? X : MoreHorizontal, path: '' }}
              isActive={isMoreActive || showMore}
              onClick={() => setShowMore((v) => !v)}
            />
          </div>
        </div>

        <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent rounded-2xl blur-xl -z-10" />
      </motion.nav>
    </>
  );
};

export default BottomNav;
