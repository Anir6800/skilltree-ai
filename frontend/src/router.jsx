import React from 'react';
import { createBrowserRouter, Navigate, useLocation } from 'react-router-dom';
import useAuthStore from './store/authStore';

// Page component imports
import AuthPage from './pages/AuthPage';
import DashboardPage from './pages/DashboardPage';
import SkillTreePage from './pages/SkillTreePage';
import SkillDetailPage from './pages/SkillDetailPage';
import QuestPage from './pages/QuestPage';
import EditorPage from './pages/EditorPage';
import ArenaPage from './pages/ArenaPage';
import MatchPage from './pages/MatchPage';
import LeaderboardPage from './pages/LeaderboardPage';
import ProfilePage from './pages/ProfilePage';
import MentorPage from './pages/MentorPage';
import AdminPage from './pages/AdminPage';

/**
 * AuthGuard Component
 * Prevents access to protected routes if the user is not authenticated.
 * @param {Object} props
 * @param {React.ReactNode} props.children
 * @param {boolean} [props.requireAdmin=false]
 */
const AuthGuard = ({ children, requireAdmin = false }) => {
  const { isAuthenticated, user } = useAuthStore();
  const location = useLocation();

  if (!isAuthenticated) {
    // Redirect to login but save the current location to redirect back after login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requireAdmin && user?.role !== 'admin') {
    // User is not an admin, redirect to safe dashboard
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

/**
 * PublicGuard Component
 * Redirects authenticated users away from public-only routes (like login/register).
 * @param {Object} props
 * @param {React.ReactNode} props.children
 */
const PublicGuard = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

/**
 * SkillTree AI Router Configuration
 * React Router v7 with role-based protected routes
 */
const router = createBrowserRouter([
  // Public Entry / Fallback
  {
    path: '/',
    element: (
      <AuthGuard>
        <Navigate to="/dashboard" replace />
      </AuthGuard>
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
    path: '/auth', // Combined auth page if needed
    element: (
      <PublicGuard>
        <AuthPage />
      </PublicGuard>
    ),
  },

  // Protected Main Routes
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
    path: '/skills/:id',
    element: (
      <AuthGuard>
        <SkillDetailPage />
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

  // User & Support
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

  // Management
  {
    path: '/admin',
    element: (
      <AuthGuard requireAdmin>
        <AdminPage />
      </AuthGuard>
    ),
  },

  // Catch-all
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
]);

export default router;