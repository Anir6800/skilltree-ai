/**
 * SkillTree AI - Result Modal
 * Full-screen overlay showing quest result with animated quote, XP counter, and action buttons.
 * Implements glassmorphism design with dark gradients, floating panels, and motion-led hierarchy.
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Confetti from 'react-confetti';
import './ResultModal.css';

const ResultModal = ({
  isOpen,
  submission,
  quote,
  xpAwarded,
  streakMilestone,
  onTryAgain,
  onNextQuest,
  onViewFeedback,
  onClose,
}) => {
  const [displayedQuote, setDisplayedQuote] = useState('');
  const [quoteIndex, setQuoteIndex] = useState(0);
  const [showConfetti, setShowConfetti] = useState(false);
  const [animatedXP, setAnimatedXP] = useState(0);

  const isPassed = submission?.status === 'passed';
  const isFailed = submission?.status === 'failed';
  const isFlagged = submission?.status === 'flagged';

  // Typewriter effect for quote
  useEffect(() => {
    if (!isOpen || !quote) return;

    setDisplayedQuote('');
    setQuoteIndex(0);

    if (isPassed) {
      setShowConfetti(true);
      const timer = setTimeout(() => setShowConfetti(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [isOpen, quote, isPassed]);

  // Typewriter animation
  useEffect(() => {
    if (!isOpen || !quote || quoteIndex >= quote.length) return;

    const timer = setTimeout(() => {
      setDisplayedQuote((prev) => prev + quote[quoteIndex]);
      setQuoteIndex((prev) => prev + 1);
    }, 30); // 30ms per character

    return () => clearTimeout(timer);
  }, [isOpen, quote, quoteIndex]);

  // Animate XP counter
  useEffect(() => {
    if (!isOpen || !xpAwarded) return;

    let current = 0;
    const increment = Math.ceil(xpAwarded / 30); // Animate over ~30 frames
    const timer = setInterval(() => {
      current += increment;
      if (current >= xpAwarded) {
        setAnimatedXP(xpAwarded);
        clearInterval(timer);
      } else {
        setAnimatedXP(current);
      }
    }, 16); // ~60fps

    return () => clearInterval(timer);
  }, [isOpen, xpAwarded]);

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose?.();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="result-modal-backdrop"
          onClick={handleBackdropClick}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
        >
          {/* Confetti for passed quests */}
          {showConfetti && isPassed && (
            <Confetti
              width={window.innerWidth}
              height={window.innerHeight}
              recycle={false}
              numberOfPieces={100}
            />
          )}

          {/* Main result card */}
          <motion.div
            className={`result-modal-card result-${isPassed ? 'passed' : isFailed ? 'failed' : 'flagged'}`}
            initial={{ scale: 0.8, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.8, opacity: 0, y: 20 }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
          >
            {/* Status header */}
            <motion.div
              className="result-header"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.3 }}
            >
              <div className="status-badge">
                {isPassed && (
                  <>
                    <motion.span
                      className="status-icon passed"
                      initial={{ scale: 0, rotate: -180 }}
                      animate={{ scale: 1, rotate: 0 }}
                      transition={{ delay: 0.3, type: 'spring', stiffness: 200 }}
                    >
                      ✓
                    </motion.span>
                    <span className="status-text">Quest Passed!</span>
                  </>
                )}
                {isFailed && (
                  <>
                    <motion.span
                      className="status-icon failed"
                      animate={{ x: [-5, 5, -5, 0] }}
                      transition={{ delay: 0.3, duration: 0.4 }}
                    >
                      ✕
                    </motion.span>
                    <span className="status-text">Quest Failed</span>
                  </>
                )}
                {isFlagged && (
                  <>
                    <motion.span
                      className="status-icon flagged"
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: 0.3, type: 'spring' }}
                    >
                      ⚠
                    </motion.span>
                    <span className="status-text">AI Flagged</span>
                  </>
                )}
              </div>

              {/* Quest info */}
              <div className="quest-info">
                <h2 className="quest-title">{submission?.quest?.title}</h2>
                <p className="skill-name">{submission?.quest?.skill?.title}</p>
              </div>
            </motion.div>

            {/* Motivational quote */}
            <motion.div
              className="quote-section"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4, duration: 0.3 }}
            >
              <blockquote className="motivational-quote">
                <span className="quote-mark">"</span>
                {displayedQuote}
                {quoteIndex < quote?.length && <span className="cursor">|</span>}
                <span className="quote-mark">"</span>
              </blockquote>
            </motion.div>

            {/* Stats grid */}
            <motion.div
              className="stats-grid"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.3 }}
            >
              {/* Tests passed */}
              <div className="stat-item">
                <span className="stat-label">Tests Passed</span>
                <span className="stat-value">
                  {submission?.execution_result?.tests_passed || 0}
                  <span className="stat-total">/{submission?.quest?.test_cases?.length || 1}</span>
                </span>
              </div>

              {/* Solve time */}
              <div className="stat-item">
                <span className="stat-label">Solve Time</span>
                <span className="stat-value">
                  {((submission?.execution_result?.time_ms || 0) / 1000).toFixed(1)}
                  <span className="stat-unit">s</span>
                </span>
              </div>

              {/* Attempt number */}
              <div className="stat-item">
                <span className="stat-label">Attempt</span>
                <span className="stat-value">#{submission?.attempt_number || 1}</span>
              </div>

              {/* AI score if available */}
              {submission?.ai_feedback?.score !== undefined && (
                <div className="stat-item">
                  <span className="stat-label">AI Score</span>
                  <span className="stat-value">
                    {(submission.ai_feedback.score * 100).toFixed(0)}
                    <span className="stat-unit">%</span>
                  </span>
                </div>
              )}
            </motion.div>

            {/* XP awarded */}
            {xpAwarded > 0 && (
              <motion.div
                className="xp-section"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.6, duration: 0.3 }}
              >
                <div className="xp-counter">
                  <span className="xp-icon">⭐</span>
                  <span className="xp-amount">+{animatedXP}</span>
                  <span className="xp-label">XP</span>
                </div>
              </motion.div>
            )}

            {/* Streak milestone badge */}
            {streakMilestone && (
              <motion.div
                className="streak-badge"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7, duration: 0.3 }}
              >
                <span className="streak-icon">🔥</span>
                <span className="streak-text">{streakMilestone}-Day Streak!</span>
              </motion.div>
            )}

            {/* Action buttons */}
            <motion.div
              className="action-buttons"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8, duration: 0.3 }}
            >
              {isPassed ? (
                <>
                  <motion.button
                    className="btn btn-secondary"
                    onClick={onTryAgain}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    Try Again
                  </motion.button>
                  <motion.button
                    className="btn btn-primary"
                    onClick={onNextQuest}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    Next Quest →
                  </motion.button>
                </>
              ) : (
                <>
                  <motion.button
                    className="btn btn-primary"
                    onClick={onTryAgain}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    Try Again
                  </motion.button>
                  {onViewFeedback && (
                    <motion.button
                      className="btn btn-secondary"
                      onClick={onViewFeedback}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      View AI Feedback
                    </motion.button>
                  )}
                </>
              )}
            </motion.div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ResultModal;
