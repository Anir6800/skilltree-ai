/**
 * SkillTree AI - 404 Not Found Page
 * Theme-consistent glassmorphism 404 with navigation back to safety.
 */

import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { AlertTriangle, Home, ArrowLeft, Zap } from 'lucide-react';
import useAuthStore from '../store/authStore';

const NotFoundPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated } = useAuthStore();

  const handleGoHome = () => {
    navigate(isAuthenticated ? '/dashboard' : '/');
  };

  const handleGoBack = () => {
    navigate(-1);
  };

  return (
    <div className="fixed inset-0 bg-[#0a0c10] text-white flex items-center justify-center overflow-hidden">
      {/* Ambient glows */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-purple-600/10 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-600/10 blur-[120px] rounded-full" />
        <div className="absolute top-[40%] left-[40%] w-[300px] h-[300px] bg-red-600/5 blur-[100px] rounded-full" />
      </div>

      {/* Vignette */}
      <div className="fixed inset-0 pointer-events-none shadow-[inset_0_0_200px_rgba(0,0,0,0.8)]" />

      <div className="relative z-10 text-center px-6 max-w-lg">
        {/* Icon */}
        <motion.div
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, type: 'spring', damping: 15 }}
          className="inline-flex items-center justify-center w-24 h-24 rounded-3xl bg-gradient-to-br from-red-500/20 to-orange-500/20 border border-red-500/30 mb-8 shadow-[0_0_40px_rgba(239,68,68,0.2)]"
        >
          <AlertTriangle size={44} className="text-red-400" />
        </motion.div>

        {/* 404 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.5 }}
        >
          <div className="text-[120px] font-black leading-none tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-primary via-accent to-primary bg-[length:200%_auto] animate-gradient-flow mb-2">
            404
          </div>
          <h1 className="text-2xl font-black text-white mb-3">
            Route Not Found
          </h1>
          <p className="text-slate-400 text-sm mb-2 font-medium">
            The path{' '}
            <code className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-primary font-mono text-xs">
              {location.pathname}
            </code>{' '}
            doesn't exist in this system.
          </p>
          <p className="text-slate-500 text-sm mb-10">
            It may have been moved, deleted, or you may have mistyped the URL.
          </p>
        </motion.div>

        {/* Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25, duration: 0.5 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-3"
        >
          <button
            onClick={handleGoHome}
            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-primary to-accent text-white font-bold text-sm uppercase tracking-wider hover:shadow-[0_0_24px_rgba(99,102,241,0.5)] hover:scale-[1.03] transition-all duration-200"
          >
            <Home size={16} />
            {isAuthenticated ? 'Go to Dashboard' : 'Go Home'}
          </button>
          <button
            onClick={handleGoBack}
            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-white/5 border border-white/10 text-slate-300 font-bold text-sm uppercase tracking-wider hover:bg-white/10 hover:text-white transition-all duration-200"
          >
            <ArrowLeft size={16} />
            Go Back
          </button>
        </motion.div>

        {/* Branding */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mt-12 flex items-center justify-center gap-2 text-slate-600"
        >
          <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
            <Zap size={12} className="text-white" fill="white" />
          </div>
          <span className="text-xs font-bold tracking-widest uppercase">SkillTree AI</span>
        </motion.div>
      </div>
    </div>
  );
};

export default NotFoundPage;
