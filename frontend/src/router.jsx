/**
 * SkillTree AI - Router Configuration
 * React Router v7 configuration with AuthGuard
 * @module router
 */

import { createBrowserRouter, Navigate } from 'react-router-dom';
import AuthGuard from './components/layout/AuthGuard';

// Page imports
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
 * Create router with all routes
 * @type {import('react-router-dom').Router}
 */
const router = createBrowserRouter([
  {
    path: '/auth',
    element: <AuthPage />,
  },
  {
    path: '/',
    element: (
      <AuthGuard>
        <DashboardPage />
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
    path: '/quests/:id',
    element: (
      <AuthGuard>
        <QuestPage />
      </AuthGuard>
    ),
  },
  {
    path: '/editor',
    element: (
      <AuthGuard>
        <EditorPage />
      </AuthGuard>
    ),
  },
  {
    path: '/arena',
    element: (
      <AuthGuard>
        <ArenaPage />
      </AuthGuard>
    ),
  },
  {
    path: '/match/:id',
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
  {
    path: '/profile',
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
    path: '/admin',
    element: (
      <AuthGuard requireAdmin>
        <AdminPage />
      </AuthGuard>
    ),
  },
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
]);

export default router;