/**
 * SkillTree AI - Share Solution Modal
 * Modal for sharing passed solutions with the community.
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Share2, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { shareSolution } from '../../api/solutionsApi';
import { cn } from '../../utils/cn';

export default function ShareSolutionModal({ submissionId, questTitle, onClose, onSuccess }) {
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);

  const handleShare = async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      const result = await shareSolution(submissionId, isAnonymous);
      setStatus('success');
      setTimeout(() => {
        onSuccess?.(result);
        onClose();
      }, 1500);
    } catch (err) {
      setError(err.message || 'Failed to share solution');
      setStatus('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
        className="bg-slate-900 border border-white/10 rounded-xl max-w-md w-full p-6"
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Share2 size={24} className="text-primary" />
            Share Solution
          </h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-white/10 rounded transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <AnimatePresence mode="wait">
          {status === 'success' ? (
            <motion.div
              key="success"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="text-center py-8"
            >
              <CheckCircle2 size={48} className="mx-auto mb-4 text-emerald-400" />
              <p className="text-white font-semibold mb-2">Solution Shared!</p>
              <p className="text-sm text-slate-400">
                Your solution is now available for the community to learn from.
              </p>
            </motion.div>
          ) : (
            <motion.div
              key="form"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-4"
            >
              <p className="text-sm text-slate-300">
                Share your solution for <span className="font-semibold text-white">{questTitle}</span> with the community.
              </p>

              {/* Anonymous Toggle */}
              <div className="bg-white/5 border border-white/10 rounded-lg p-4">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isAnonymous}
                    onChange={(e) => setIsAnonymous(e.target.checked)}
                    className="w-4 h-4 rounded border-white/20 bg-white/5 text-primary focus:ring-primary"
                  />
                  <div>
                    <p className="text-sm font-semibold text-white">Share Anonymously</p>
                    <p className="text-xs text-slate-400">Your username won't be displayed</p>
                  </div>
                </label>
              </div>

              {/* Error */}
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-3 bg-red-500/10 border border-red-500/30 rounded flex items-center gap-2 text-red-400 text-sm"
                >
                  <AlertCircle size={16} />
                  {error}
                </motion.div>
              )}

              {/* Info */}
              <div className="bg-primary/10 border border-primary/30 rounded-lg p-3 text-xs text-slate-300">
                <p className="font-semibold text-primary mb-1">Community Guidelines</p>
                <ul className="space-y-1 text-slate-400">
                  <li>• Be respectful and constructive</li>
                  <li>• No plagiarism or copied code</li>
                  <li>• Comments should be helpful</li>
                </ul>
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-4">
                <button
                  onClick={onClose}
                  disabled={isSubmitting}
                  className="flex-1 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white font-semibold hover:bg-white/10 disabled:opacity-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleShare}
                  disabled={isSubmitting}
                  className="flex-1 px-4 py-2 bg-primary/20 border border-primary/40 rounded-lg text-primary font-semibold hover:bg-primary/30 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      Sharing...
                    </>
                  ) : (
                    <>
                      <Share2 size={16} />
                      Share Solution
                    </>
                  )}
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </motion.div>
  );
}
