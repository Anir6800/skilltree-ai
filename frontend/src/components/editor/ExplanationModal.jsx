import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, AlertTriangle } from 'lucide-react';
import { API_BASE_URL } from '../../constants';

const ExplanationModal = ({ isOpen, submissionId, onClose, onSuccess, token }) => {
  const [explanation, setExplanation] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const minChars = 200;
  const maxChars = 5000;
  const charCount = explanation.length;
  const isValid = charCount >= minChars;

  const handleSubmit = async () => {
    if (!isValid) {
      setError(`Explanation must be at least ${minChars} characters`);
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(
        `${API_BASE_URL}/ai-detection/submissions/${submissionId}/explain/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ explanation }),
        }
      );

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to submit explanation');
      }

      onSuccess?.();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Prevent closing by clicking outside or pressing Escape
  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      // Do nothing - modal is required
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      // Do nothing - modal is required
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop - non-dismissible */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleBackdropClick}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0, 0, 0, 0.7)',
              backdropFilter: 'blur(4px)',
              zIndex: 40,
            }}
          />

          {/* Modal - cannot be dismissed */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2 }}
            onKeyDown={handleKeyDown}
            style={{
              position: 'fixed',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              background: 'linear-gradient(135deg, rgba(15, 18, 25, 0.95) 0%, rgba(26, 29, 41, 0.95) 100%)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(124, 106, 245, 0.2)',
              borderRadius: '16px',
              padding: '32px',
              maxWidth: '600px',
              width: '90%',
              maxHeight: '90vh',
              overflowY: 'auto',
              zIndex: 50,
              boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)',
            }}
          >
            {/* No close button - modal is required */}

            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
              <AlertTriangle size={28} color='#ef4444' />
              <h2 style={{ fontSize: '24px', fontWeight: '700', color: '#fff', margin: 0 }}>
                ⚠️ AI Assistance Detected
              </h2>
            </div>

            {/* Description */}
            <p
              style={{
                fontSize: '14px',
                color: '#d1d5db',
                lineHeight: '1.6',
                marginBottom: '24px',
              }}
            >
              Our system flagged your submission as possibly AI-generated. If you wrote this code yourself, please explain your approach. This helps us understand your learning process and improve our detection system.
            </p>

            {/* Required notice */}
            <div
              style={{
                background: 'rgba(245, 158, 11, 0.1)',
                border: '1px solid rgba(245, 158, 11, 0.3)',
                borderRadius: '8px',
                padding: '12px',
                marginBottom: '16px',
                fontSize: '12px',
                color: '#fbbf24',
              }}
            >
              ⚠️ This explanation is required to proceed. You cannot dismiss this modal without responding.
            </div>

            {/* Textarea */}
            <div style={{ marginBottom: '16px' }}>
              <label
                style={{
                  display: 'block',
                  fontSize: '12px',
                  fontWeight: '600',
                  color: '#9ca3af',
                  marginBottom: '8px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                }}
              >
                Your Explanation (Required)
              </label>
              <textarea
                value={explanation}
                onChange={(e) => setExplanation(e.target.value)}
                placeholder='Explain how you approached this problem, what techniques you used, and why you chose this solution...'
                style={{
                  width: '100%',
                  minHeight: '200px',
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: `1px solid ${charCount >= minChars ? 'rgba(124, 106, 245, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                  borderRadius: '8px',
                  padding: '12px',
                  color: '#fff',
                  fontSize: '14px',
                  fontFamily: 'inherit',
                  resize: 'vertical',
                  transition: 'all 0.2s',
                  boxSizing: 'border-box',
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = 'rgba(124, 106, 245, 0.5)';
                  e.target.style.background = 'rgba(255, 255, 255, 0.08)';
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = charCount >= minChars ? 'rgba(124, 106, 245, 0.3)' : 'rgba(239, 68, 68, 0.3)';
                  e.target.style.background = 'rgba(255, 255, 255, 0.05)';
                }}
              />
            </div>

            {/* Character Counter */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '24px',
              }}
            >
              <div
                style={{
                  fontSize: '12px',
                  color: charCount >= minChars ? '#10b981' : '#ef4444',
                  fontWeight: '500',
                }}
              >
                {charCount < minChars ? (
                  <>
                    {minChars - charCount} more characters needed
                  </>
                ) : (
                  <>
                    ✓ Ready to submit
                  </>
                )}
              </div>
              <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                {charCount} / {maxChars}
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: '8px',
                  padding: '12px',
                  marginBottom: '16px',
                  fontSize: '13px',
                  color: '#fca5a5',
                }}
              >
                {error}
              </motion.div>
            )}

            {/* Submit Button Only */}
            <motion.button
              onClick={handleSubmit}
              disabled={!isValid || loading}
              whileHover={isValid && !loading ? { scale: 1.02 } : {}}
              whileTap={isValid && !loading ? { scale: 0.98 } : {}}
              style={{
                width: '100%',
                background: isValid
                  ? 'linear-gradient(135deg, #7c6af5 0%, #a78bfa 100%)'
                  : 'rgba(124, 106, 245, 0.3)',
                border: 'none',
                color: '#fff',
                borderRadius: '8px',
                padding: '12px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: isValid && !loading ? 'pointer' : 'not-allowed',
                transition: 'all 0.2s',
                opacity: loading ? 0.7 : 1,
              }}
            >
              {loading ? 'Submitting...' : 'Submit Explanation'}
            </motion.button>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default ExplanationModal;
