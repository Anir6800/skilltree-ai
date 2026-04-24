/**
 * SkillTree AI - Authentication Page
 * Redesigned with immersive 3D background and premium glassmorphism
 * @module pages/AuthPage
 */

import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Mail, Lock, User, ShieldCheck, ArrowRight, Sparkles, Zap } from 'lucide-react';
import useAuthStore from '../store/authStore';
import CinemaContainer from '../components/layout/CinemaContainer';
import PulsingCore from '../components/nexus/PulsingCore';

/**
 * Authentication page component
 * @returns {JSX.Element} Auth page
 */
function AuthPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, register, isLoading, error, clearError } = useAuthStore();
  
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    passwordConfirm: '',
  });
  const [validationError, setValidationError] = useState('');

  const from = location.state?.from?.pathname || '/dashboard';

  useEffect(() => {
    clearError();
  }, [isLogin]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setValidationError('');
    if (error) clearError();
  };

  const validateForm = () => {
    if (!formData.username.trim()) {
      setValidationError('Username is required');
      return false;
    }
    
    if (!isLogin) {
      if (!formData.email.trim()) {
        setValidationError('Email is required');
        return false;
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
        setValidationError('Invalid email format');
        return false;
      }
    }
    
    if (!formData.password) {
      setValidationError('Password is required');
      return false;
    }
    
    if (formData.password.length < 8) {
      setValidationError('Password must be at least 8 characters');
      return false;
    }
    
    if (!isLogin && formData.password !== formData.passwordConfirm) {
      setValidationError('Passwords do not match');
      return false;
    }
    
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;
    
    try {
      if (isLogin) {
        await login(formData.username, formData.password);
      } else {
        await register(formData);
      }
      navigate(from, { replace: true });
    } catch (err) {
      // Handled by store
    }
  };

  return (
    <div className="relative w-full min-h-screen bg-background overflow-hidden flex items-center justify-center p-6">
      {/* Immersive 3D Layer */}
      <div className="absolute inset-0 z-0">
        <CinemaContainer>
          <PulsingCore />
        </CinemaContainer>
      </div>

      {/* Content Overlay */}
      <motion.div 
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="relative z-10 w-full max-w-lg"
      >
        <div className="glass-panel p-10 rounded-[2.5rem] border-white/5 shadow-2xl backdrop-blur-3xl overflow-hidden group">
          {/* Subtle light effect */}
          <div className="absolute -top-24 -right-24 w-48 h-48 bg-primary/20 rounded-full blur-3xl group-hover:bg-primary/30 transition-colors duration-700" />
          <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-accent/10 rounded-full blur-3xl group-hover:bg-accent/20 transition-colors duration-700" />

          <div className="text-center mb-10 relative">
            <motion.div
              initial={{ rotate: -10, scale: 0.8 }}
              animate={{ rotate: 0, scale: 1 }}
              transition={{ type: "spring", damping: 12 }}
              className="inline-block mb-4 p-3 rounded-2xl bg-gradient-to-br from-primary to-accent shadow-lg shadow-primary/20"
            >
              <Zap size={32} className="text-white" fill="currentColor" />
            </motion.div>
            
            <h1 className="text-5xl font-black tracking-tighter mb-2">
              SKILLTREE <span className="premium-gradient-text uppercase">AI</span>
            </h1>
            <p className="text-slate-400 font-medium tracking-wide text-sm uppercase">
              {isLogin ? 'Authorization Required' : 'Initialize New Account'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-1 relative">
            <AnimatePresence mode="wait">
              <motion.div
                key={isLogin ? 'login' : 'register'}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                {/* Username */}
                <div className="form-input-container">
                  <label className="form-label-premium"><User size={12} className="inline mr-1 mb-0.5" /> Username</label>
                  <div className="relative">
                    <input
                      type="text"
                      name="username"
                      value={formData.username}
                      onChange={handleChange}
                      className="form-input-premium pl-12 pr-4"
                      placeholder="adventurer_01"
                      required
                    />
                    <User size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                  </div>
                </div>

                {/* Email (Register only) */}
                {!isLogin && (
                  <motion.div 
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    className="form-input-container"
                  >
                    <label className="form-label-premium"><Mail size={12} className="inline mr-1 mb-0.5" /> Neural Link (Email)</label>
                    <div className="relative">
                      <input
                        type="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        className="form-input-premium pl-12 pr-4"
                        placeholder="connect@nexus.ai"
                        required
                      />
                      <Mail size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                    </div>
                  </motion.div>
                )}

                {/* Password */}
                <div className="form-input-container">
                  <label className="form-label-premium"><Lock size={12} className="inline mr-1 mb-0.5" /> Security Key</label>
                  <div className="relative">
                    <input
                      type="password"
                      name="password"
                      value={formData.password}
                      onChange={handleChange}
                      className="form-input-premium pl-12 pr-4"
                      placeholder="••••••••"
                      required
                    />
                    <Lock size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                  </div>
                </div>

                {/* Confirm Password (Register only) */}
                {!isLogin && (
                  <motion.div 
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    className="form-input-container"
                  >
                    <label className="form-label-premium"><ShieldCheck size={12} className="inline mr-1 mb-0.5" /> Verify Key</label>
                    <div className="relative">
                      <input
                        type="password"
                        name="passwordConfirm"
                        value={formData.passwordConfirm}
                        onChange={handleChange}
                        className="form-input-premium pl-12 pr-4"
                        placeholder="••••••••"
                        required
                      />
                      <ShieldCheck size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                    </div>
                  </motion.div>
                )}
              </motion.div>
            </AnimatePresence>

            {/* Error Messages */}
            <AnimatePresence>
              {(error || validationError) && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="bg-accent/10 border border-accent/20 text-accent text-xs font-bold py-3 px-4 rounded-xl mb-6 flex items-center"
                >
                  <Sparkles size={14} className="mr-2 flex-shrink-0" />
                  {validationError || error}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Submit Button */}
            <button
              type="submit"
              className="auth-btn-primary group flex items-center justify-center space-x-2"
              disabled={isLoading}
            >
              <span>{isLoading ? 'Processing...' : isLogin ? 'Initialize Sequence' : 'Create Identity'}</span>
              {!isLoading && <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />}
            </button>
          </form>

          {/* Footer Toggle */}
          <div className="mt-8 text-center">
            <button
              type="button"
              onClick={() => setIsLogin(!isLogin)}
              className="text-slate-500 hover:text-white text-xs font-bold uppercase tracking-widest transition-colors flex items-center justify-center mx-auto space-x-2"
            >
              <span>{isLogin ? "Need a neural uplink?" : "Already have an uplink?"}</span>
              <span className="text-primary hover:underline underline-offset-4 decoration-2">
                {isLogin ? 'Register' : 'Login'}
              </span>
            </button>
          </div>
        </div>

        {/* Decorative elements */}
        <div className="mt-8 flex items-center justify-center space-x-6 opacity-30 grayscale hover:grayscale-0 hover:opacity-100 transition-all duration-700">
          <div className="flex flex-col items-center">
            <div className="w-1 h-12 bg-gradient-to-b from-primary to-transparent" />
            <span className="text-[8px] font-black uppercase tracking-tighter mt-2">Core</span>
          </div>
          <div className="flex flex-col items-center">
            <div className="w-1 h-8 bg-gradient-to-b from-accent to-transparent" />
            <span className="text-[8px] font-black uppercase tracking-tighter mt-2">Sync</span>
          </div>
          <div className="flex flex-col items-center">
            <div className="w-1 h-16 bg-gradient-to-b from-emerald-400 to-transparent" />
            <span className="text-[8px] font-black uppercase tracking-tighter mt-2">Node</span>
          </div>
        </div>
      </motion.div>

      {/* Background Vignette */}
      <div className="fixed inset-0 pointer-events-none shadow-[inset_0_0_150px_rgba(0,0,0,0.9)] z-0" />
    </div>
  );
}

export default AuthPage;