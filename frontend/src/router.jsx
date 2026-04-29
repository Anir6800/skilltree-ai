import React from 'react';
import { createBrowserRouter, Navigate, useLocation } from 'react-router-dom';
import useAuthStore from './store/authStore';
import { useOnboardingCheck } from './hooks/useOnboardingCheck';

// Page component imports
import LandingPage from './pages/LandingPage';
import AuthPage from './pages/AuthPage';
import AdminLoginPage from './pages/AdminLoginPage';
import DashboardPage from './pages/DashboardPage';
import SkillTreePage from './pages/SkillTreePage';
import SkillTreeMakerPage from './pages/SkillTreeMakerPage';
import SkillDetailPage from './pages/SkillDetailPage';
import QuestPage from './pages/QuestPage';
import MCQQuestPage from './pages/MCQQuestPage';
import EditorPage from './pages/EditorPage';
import ArenaPage from './pages/ArenaPage';
import MatchPage from './pages/MatchPage';
import LeaderboardPage from './pages/LeaderboardPage';
import ProfilePage from './pages/ProfilePage';
import MentorPage from './pages/MentorPage';
import OnboardingPage from './pages/OnboardingPage';
import AdminPage from './pages/AdminPage';
import GroupPage from './pages/GroupPage';
import SolutionsPage from './pages/SolutionsPage';
import ReportsPage from './pages/ReportsPage';
import NotFoundPage from './pages/NotFoundPage';

/**
 * AuthGuard Component
 * Prevents access to protected routes if the user is not authenticated.
 * Also checks onboarding status and redirects if needed.
 */
const AuthGuard = ({ children, requireAdmin = false, skipOnboardingCheck = false }) => {
  const { isAuthenticated, user, _hasHydrated } = useAuthStore();
  const location = useLocation();
  const { isChecking } = useOnboardingCheck();

  // Wait for hydration to complete before deciding anything
  if (!_hasHydrated) {
    return (
      <div className="fixed inset-0 bg-[#0a0c10] flex items-center justify-center z-[9999]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-2 border-primary/20 border-t-primary rounded-full animate-spin" />
          <p className="text-slate-500 font-bold uppercase tracking-widest text-[10px]">Synchronizing Neural Link...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Admin check: support both role-based and is_staff
  if (requireAdmin && user?.role !== 'admin' && !user?.is_staff) {
    return <Navigate to="/dashboard" replace />;
  }

  if (!skipOnboardingCheck && isChecking) {
    return (
      <div style={{
        position: 'fixed',
        inset: 0,
        background: '#0a0c10',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#7c6af5'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '40px',
            height: '40px',
            border: '3px solid rgba(124, 106, 245, 0.3)',
            borderTopColor: '#7c6af5',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px'
          }} />
          <p style={{ fontSize: '14px', fontWeight: '500' }}>Loading...</p>
        </div>
      </div>
    );
  }

  return children;
};

/**
 * PublicGuard Component
 * Redirects authenticated users away from public-only routes (like login/register).
 */
const PublicGuard = ({ children, redirectTo = '/dashboard' }) => {
  const { isAuthenticated, user } = useAuthStore();

  if (isAuthenticated) {
    if (redirectTo === '/admin' && (user?.role === 'admin' || user?.is_staff)) {
      return <Navigate to="/admin" replace />;
    }
    return <Navigate to={redirectTo} replace />;
  }

  return children;
};

/**
 * SkillTree AI Router Configuration
 * React Router v7 with role-based protected routes
 */
const router = createBrowserRouter([
  // Landing page — public, redirect authenticated users to dashboard
  {
    path: '/',
    element: (
      <PublicGuard redirectTo="/dashboard">
        <LandingPage />
      </PublicGuard>
    ),
  },

  // Auth Routes
  {
    path: '/login',
    element: (
      <PublicGuard>
        <AuthPage isLogin={true} />
      </PublicGuard>
    ),
  },
  {
    path: '/register',
    element: (
      <PublicGuard>
        <AuthPage isLogin={false} />
      </PublicGuard>
    ),
  },
  {
    path: '/auth',
    element: (
      <PublicGuard>
        <AuthPage />
      </PublicGuard>
    ),
  },
  {
    path: '/admin/login',
    element: <AdminLoginPage />,
  },

  // Onboarding — protected, skip onboarding check to avoid redirect loop
  {
    path: '/onboarding',
    element: (
      <AuthGuard skipOnboardingCheck={true}>
        <OnboardingPage />
      </AuthGuard>
    ),
  },

  // Core App Routes
  {
    path: '/dashboard',
    element: (
      <AuthGuard>
        <DashboardPage />
      </AuthGuard>
    ),
  },
  {
    path: '/skills',
    element: (
      <AuthGuard>
        <SkillTreePage />
      </AuthGuard>
    ),
  },
  {
    path: '/skill-tree-maker',
    element: (
      <AuthGuard>
        <SkillTreeMakerPage />
      </AuthGuard>
    ),
  },
  {
    path: '/skills/:id',
    element: (
      <AuthGuard>
        <SkillDetailPage />
      </AuthGuard>
    ),
  },
  {
    path: '/quests',
    element: (
      <AuthGuard>
        <QuestPage />
      </AuthGuard>
    ),
  },
  {
    path: '/quests/:questId',
    element: (
      <AuthGuard>
        <QuestPage />
      </AuthGuard>
    ),
  },
  {
    path: '/editor/:questId',
    element: (
      <AuthGuard>
        <EditorPage />
      </AuthGuard>
    ),
  },
  {
    path: '/quests/:questId/mcq',
    element: (
      <AuthGuard>
        <MCQQuestPage />
      </AuthGuard>
    ),
  },

  // Multiplayer & Social
  {
    path: '/arena',
    element: (
      <AuthGuard>
        <ArenaPage />
      </AuthGuard>
    ),
  },
  {
    path: '/match/:matchId',
    element: (
      <AuthGuard>
        <MatchPage />
      </AuthGuard>
    ),
  },
  {
    path: '/leaderboard',
    element: (
      <AuthGuard>
        <LeaderboardPage />
      </AuthGuard>
    ),
  },

  // Community
  {
    path: '/groups',
    element: (
      <AuthGuard>
        <GroupPage />
      </AuthGuard>
    ),
  },
  {
    path: '/solutions',
    element: (
      <AuthGuard>
        <SolutionsPage />
      </AuthGuard>
    ),
  },
  {
    path: '/solutions/:questId',
    element: (
      <AuthGuard>
        <SolutionsPage />
      </AuthGuard>
    ),
  },

  // User & Profile
  {
    path: '/profile/:userId',
    element: (
      <AuthGuard>
        <ProfilePage />
      </AuthGuard>
    ),
  },
  {
    path: '/mentor',
    element: (
      <AuthGuard>
        <MentorPage />
      </AuthGuard>
    ),
  },
  {
    path: '/reports',
    element: (
      <AuthGuard>
        <ReportsPage />
      </AuthGuard>
    ),
  },

  // Admin
  {
    path: '/admin',
    element: (
      <AuthGuard requireAdmin={true} skipOnboardingCheck={true}>
        <AdminPage />
      </AuthGuard>
    ),
  },

  // 404 — themed not-found page
  {
    path: '*',
    element: <NotFoundPage />,
  },
]);

export default router;
