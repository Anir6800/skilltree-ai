/**
 * SkillTree AI - Onboarding Check Hook
 * Checks if user needs onboarding and redirects
 */

import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import api from '../api/api';
import useAuthStore from '../store/authStore';

/**
 * Hook to check onboarding status and redirect if needed
 * @returns {Object} { needsOnboarding, isChecking }
 */
export function useOnboardingCheck() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, user } = useAuthStore();
  const [needsOnboarding, setNeedsOnboarding] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const checkOnboarding = async () => {
      // Skip check if not authenticated
      if (!isAuthenticated) {
        setIsChecking(false);
        return;
      }

      // Skip check if already on onboarding page
      if (location.pathname === '/onboarding') {
        setIsChecking(false);
        return;
      }

      // Skip check for auth pages
      if (location.pathname === '/login' || location.pathname === '/register') {
        setIsChecking(false);
        return;
      }

      // Skip onboarding check for admin users or admin routes
      if (user?.is_staff || location.pathname.startsWith('/admin')) {
        setIsChecking(false);
        setNeedsOnboarding(false);
        return;
      }

      try {
        const response = await api.get('/api/onboarding/status/');
        const { completed } = response.data;

        if (!completed) {
          setNeedsOnboarding(true);
          // Redirect to onboarding
          navigate('/onboarding', { replace: true });
        } else {
          setNeedsOnboarding(false);
        }
      } catch (error) {
        console.error('Failed to check onboarding status:', error);
        // Don't block user if check fails
        setNeedsOnboarding(false);
      } finally {
        setIsChecking(false);
      }
    };

    checkOnboarding();
  }, [isAuthenticated, location.pathname, navigate, user]);

  return { needsOnboarding, isChecking };
}

export default useOnboardingCheck;
