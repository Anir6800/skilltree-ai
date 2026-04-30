/**
 * SkillTree AI - Result Modal
 * Full-screen overlay showing quest result with animated quote, XP counter, and action buttons.
 * Implements glassmorphism design with dark gradients, floating panels, and motion-led hierarchy.
 * Enhanced with celebration animations, XP spinning counter, and skill tree unlock effects.
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
  unlockedStages,
}) => {
  const [displayedQuote, setDisplayedQuote] = useState('');
  const [quoteIndex, setQuoteIndex] = useState(0);
  const [showConfetti, setShowConfetti] = useState(false);
  const [animatedXP, setAnimatedXP] = useState(0);
  const [showCelebration, setShowCelebration] = useState(false);
  const [xpParticles, setXpParticles] = useState([]);
  const [showUnlockAnimation, setShowUnlockAnimation] = useState(false);
  const confettiPieces = Array.from({ length: 80 }, (_, index) => ({
    id: index,
    left: `${(index * 37) % 100}%`,
    delay: (index % 12) * 0.05,
    duration: 1.8 + (index % 7) * 0.12,
    color: ['#6366f1', '#a855f7', '#22c55e', '#f59e0b'][index % 4],
  }));

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
      setShowCelebration(true);  // Trigger celebration immediately
      
      // Show unlock animation after celebration
      const unlockTimer = setTimeout(() => {
        if (unlockedStages && unlockedStages.length > 0) {
          setShowUnlockAnimation(true);
        }
      }, 2000);

      const confettiTimer = setTimeout(() => setShowConfetti(false), 3000);
      return () => {
        clearTimeout(unlockTimer);
        clearTimeout(confettiTimer);
      };
    } else {
      // Reset animations for failed/flagged
      setShowCelebration(false);
      setShowUnlockAnimation(false);
    }
  }, [isOpen, quote, isPassed, unlockedStages]);

  // Typewriter animation
  useEffect(() => {
    if (!isOpen || !quote || quoteIndex >= quote.length) return;

    const timer = setTimeout(() => {
      setDisplayedQuote((prev) => prev + quote[quoteIndex]);
      setQuoteIndex((prev) => prev + 1);
    }, 30); // 30ms per character

    return () => clearTimeout(timer);
  }, [isOpen, quote, quoteIndex]);

  // Animate XP counter with particles
  useEffect(() => {
    if (!isOpen || !xpAwarded) return;

    let current = 0;
    const increment = Math.ceil(xpAwarded / 30); // Animate over ~30 frames
    
    // Generate XP particles
    const particles = Array.from({ length: 8 }, (_, i) => ({
      id: i,
      delay: i * 0.05,
      angle: (i / 8) * Math.PI * 2,
    }));
    setXpParticles(particles);

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
            <div className="result-confetti-layer">
              {confettiPieces.map((piece) => (
                <motion.span
                  key={piece.id}
                  className="result-confetti-piece"
                  style={{ left: piece.left, backgroundColor: piece.color }}
                  initial={{ y: -40, opacity: 1, rotate: 0 }}
                  animate={{ y: '105vh', opacity: 0, rotate: 540 }}
                  transition={{ duration: piece.duration, delay: piece.delay, ease: 'easeOut' }}
                />
              ))}
            </div>
          )}

          {/* Main result card */}
          <motion.div
            className={`result-modal-card result-${isPassed ? 'passed' : isFailed ? 'failed' : 'flagged'}`}
            initial={{ scale: 0.8, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.8, opacity: 0, y: 20 }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
          >
            {/* Status header with celebration animation */}
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
                    <motion.span
                      className="status-text"
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.5, duration: 0.3 }}
                    >
                      Quest Passed!
                    </motion.span>
                    
                    {/* Celebration burst animation */}
                    {showCelebration && (
                      <motion.div
                        className="celebration-burst"
                        initial={{ scale: 0, opacity: 1 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0, opacity: 0 }}
                        transition={{ type: 'spring', stiffness: 100, damping: 15 }}
                      >
                        {Array.from({ length: 12 }).map((_, i) => (
                          <motion.div
                            key={i}
                            className="celebration-particle"
                            initial={{ x: 0, y: 0, opacity: 1, scale: 1 }}
                            animate={{
                              x: Math.cos((i / 12) * Math.PI * 2) * 100,
                              y: Math.sin((i / 12) * Math.PI * 2) * 100,
                              opacity: 0,
                              scale: 0,
                            }}
                            transition={{ 
                              duration: 1.2, 
                              delay: i * 0.05,
                              ease: 'easeOut'
                            }}
                          >
                            ✨
                          </motion.div>
                        ))}
                      </motion.div>
                    )}
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
                    {Number(submission.ai_feedback.score).toFixed(0)}
                    <span className="stat-unit">%</span>
                  </span>
                </div>
              )}
            </motion.div>

            {/* XP awarded with spinning counter and particles */}
            {xpAwarded > 0 && (
              <motion.div
                className="xp-section"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.6, duration: 0.3 }}
              >
                {/* XP Particles */}
                <div className="xp-particles-container">
                  {xpParticles.map((particle) => (
                    <motion.div
                      key={particle.id}
                      className="xp-particle"
                      initial={{
                        x: 0,
                        y: 0,
                        opacity: 1,
                        scale: 1,
                      }}
                      animate={{
                        x: Math.cos(particle.angle) * 100,
                        y: Math.sin(particle.angle) * 100,
                        opacity: 0,
                        scale: 0,
                      }}
                      transition={{
                        duration: 1.2,
                        delay: particle.delay,
                        ease: 'easeOut',
                      }}
                    >
                      ⭐
                    </motion.div>
                  ))}
                </div>

                {/* Spinning XP Counter */}
                <motion.div
                  className="xp-counter"
                  animate={{ scale: 1 }}
                  transition={{
                    type: 'spring',
                    stiffness: 200,
                    damping: 15,
                    // Removed repeatDelay
                  }}
                >
                  <motion.span
                    className="xp-icon"
                    animate={{ scale: [1, 1.2, 1], rotate: [0, 180, 360] }}
                    transition={{
                      duration: 3,
                      repeat: Infinity,
                      ease: 'linear',
                    }}
                  >
                    ⭐
                  </motion.span>
                  <motion.span
                    className="xp-amount"
                    key={animatedXP}
                    initial={{ scale: 0, y: -20 }}
                    animate={{ scale: 1, y: 0 }}
                    transition={{ type: 'spring', stiffness: 200 }}
                  >
                    +{animatedXP}
                  </motion.span>
                  <span className="xp-label">XP</span>
                </motion.div>
              </motion.div>
            )}

            {/* Skill tree unlock animation */}
            {showUnlockAnimation && unlockedStages && unlockedStages.length > 0 && (
              <motion.div
                className="unlock-animation-container"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2, duration: 0.5 }}
              >
                <motion.div
                  className="unlock-header"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', stiffness: 150 }}
                >
                  <span className="unlock-icon">🔓</span>
                  <span className="unlock-text">New Stages Unlocked!</span>
                </motion.div>

                <div className="unlocked-stages">
                  {unlockedStages.map((stage, index) => (
                    <motion.div
                      key={stage.id}
                      className="unlocked-stage-item"
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.3 + index * 0.1, duration: 0.3 }}
                    >
                      <motion.div
                        className="stage-badge"
                        animate={{ rotate: 360 }}
                        transition={{
                          duration: 2,
                          repeat: Infinity,
                          ease: 'linear',
                        }}
                      >
                        ✨
                      </motion.div>
                      <div className="stage-info">
                        <span className="stage-name">{stage.title}</span>
                        <span className="stage-description">{stage.description}</span>
                      </div>
                    </motion.div>
                  ))}
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

            {/* Action buttons with smooth transitions */}
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
                    onClick={() => {
                      // Smooth transition animation
                      const card = document.querySelector('.result-modal-card');
                      if (card) {
                        card.style.animation = 'slideOutRight 0.4s ease-in forwards';
                      }
                      setTimeout(onNextQuest, 300);
                    }}
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
