/**
 * SkillTree AI - Focus Mode Result Modal Hook
 * Manages ResultModal behavior when focus mode is active
 * Hides gamification elements and shows only pass/fail + quote
 */

import { useEffect } from 'react';
import useUIStore from '../store/uiStore';

/**
 * Hook to manage ResultModal in focus mode
 * Applies CSS classes to hide gamification elements
 */
export const useFocusResultModal = (isOpen) => {
  const { focusMode } = useUIStore();

  useEffect(() => {
    if (!isOpen || !focusMode) return;

    // Add focus mode class to result modal
    const resultModal = document.querySelector('.result-modal-backdrop');
    if (resultModal) {
      resultModal.classList.add('focus-mode-active');
    }

    return () => {
      const resultModal = document.querySelector('.result-modal-backdrop');
      if (resultModal) {
        resultModal.classList.remove('focus-mode-active');
      }
    };
  }, [isOpen, focusMode]);

  return { focusMode, isOpen };
};

export default useFocusResultModal;
