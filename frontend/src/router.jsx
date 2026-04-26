import React from 'react';
import { createBrowserRouter, Navigate, useLocation } from 'react-router-dom';
import useAuthStore from './store/authStore';
import { useOnboardingCheck } from './hooks/useOnboardingCheck';

// Page component imports
import AuthPage from './pages/AuthPage';
import AdminLoginPage from './pages/AdminLoginPage';
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
import OnboardingPage from './pages/OnboardingPage';
import AdminPage from './pages/AdminPage';

/**
 * AuthGuard Component
 * Prevents access to protected routes if the user is not authenticated.
 * Also checks onboarding status and redirects if needed.
 * @param {Object} props
 * @param {React.ReactNode} props.children
 * @param {boolean} [props.requireAdmin=false]
 * @param {boolean} [props.skipOnboardingCheck=false]
 */
const AuthGuard = ({ children, requireAdmin = false, skipOnboardingCheck = false }) => {
  const { isAuthenticated, user } = useAuthStore();
  const location = useLocation();
  const { isChecking } = useOnboardingCheck();

  if (!isAuthenticated) {
    // Redirect to login but save the current location to redirect back after login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requireAdmin && !user?.is_staff) {
    // User is not an admin, redirect to safe dashboard
    return <Navigate to="/dashboard" replace />;
  }

  // Show loading while checking onboarding (prevents flash)
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
 * @param {Object} props
 * @param {React.ReactNode} props.children
 * @param {string} [props.redirectTo] - Custom redirect path for authenticated users
 */
const PublicGuard = ({ children, redirectTo = '/dashboard' }) => {
  const { isAuthenticated, user } = useAuthStore();
  
  if (isAuthenticated) {
    // If user is staff and trying to access admin login, redirect to admin panel
    if (redirectTo === '/admin' && user?.is_staff) {
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
  {
    path: '/admin/login',
    element: <AdminLoginPage />,
  },

  // Protected Main Routes
  {
    path: '/onboarding',
    element: (
      <AuthGuard skipOnboardingCheck={true}>
        <OnboardingPage />
      </AuthGuard>
    ),
  },
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

  // Admin Management
  {
    path: '/admin',
    element: (
      <AuthGuard requireAdmin={true} skipOnboardingCheck={true}>
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