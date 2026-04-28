/**
 * SkillTree AI - Hint Panel Hook
 * Manages hint panel visibility based on time and failed submissions
 */

import { useState, useEffect } from 'react';

/**
 * Hook to manage hint panel visibility
 * Shows panel after 5 minutes on quest OR after 2 failed submissions
 */
export const useHintPanel = (questStartTime, failedSubmissionCount) => {
  const [showHintPanel, setShowHintPanel] = useState(false);

  useEffect(() => {
    // Check if 5 minutes have passed
    if (questStartTime) {
      const timer = setInterval(() => {
        const elapsedMinutes = (Date.now() - questStartTime) / (1000 * 60);
        if (elapsedMinutes >= 5) {
          setShowHintPanel(true);
          clearInterval(timer);
        }
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [questStartTime]);

  // Show panel if 2+ failed submissions
  useEffect(() => {
    if (failedSubmissionCount >= 2) {
      setShowHintPanel(true);
    }
  }, [failedSubmissionCount]);

  return showHintPanel;
};

export default useHintPanel;
