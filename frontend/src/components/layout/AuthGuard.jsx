/**
 * SkillTree AI - AuthGuard Component
 * Protects routes requiring authentication
 * @module components/layout/AuthGuard
 */

import { Navigate, useLocation } from 'react-router-dom';
import useAuthStore from '../../store/authStore';

/**
 * AuthGuard component that protects routes requiring authentication
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Child components to render if authenticated
 * @param {boolean} props.requireAdmin - Whether to require admin role
 * @returns {JSX.Element} Rendered component or redirect
 */
function AuthGuard({ children, requireAdmin = false }) {
  const location = useLocation();
  const { isAuthenticated, user } = useAuthStore();

  // Not authenticated - redirect to login
  if (!isAuthenticated) {
    return <Navigate to="/auth" state={{ from: location }} replace />;
  }

  // Require admin but user is not admin
  if (requireAdmin && user?.role !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}

export default AuthGuard;