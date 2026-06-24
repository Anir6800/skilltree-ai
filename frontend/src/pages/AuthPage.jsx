/**
 * SkillTree AI - Authentication Page
 * Redesigned with immersive 3D background and premium glassmorphism
 * @module pages/AuthPage
 */

import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Mail, Lock, User, ShieldCheck, ArrowRight, Sparkles, Zap, Eye, EyeOff } from 'lucide-react';
import useAuthStore from '../store/authStore';
import CinemaContainer from '../components/layout/CinemaContainer';
import PulsingCore from '../components/nexus/PulsingCore';
import { requestPasswordReset } from '../api/authApi';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Custom Icons for Brand Logos (Removed in Lucide v1.0+)
 */
const Github = ({ size = 24, className = "" }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
    <path d="M9 18c-4.51 2-5-2-7-2" />
  </svg>
);



/**
 * Utility for tailwind classes merging
 */
function cn(...inputs) {
  return twMerge(clsx(inputs));
}

/**
 * Authentication page component
 * @returns {JSX.Element} Auth page
 */
function AuthPage({ isLogin: initialIsLogin = true }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, register, isLoading, error, clearError } = useAuthStore();

  const [isLogin, setIsLogin] = useState(initialIsLogin);
  const [isForgotPassword, setIsForgotPassword] = useState(false);
  const [isResetLoading, setIsResetLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    passwordConfirm: '',
  });
  const [validationError, setValidationError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [showSignupPrompt, setShowSignupPrompt] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);

  const from = location.state?.from?.pathname || '/dashboard';
  const authError = typeof error === 'string' ? error : error?.message || '';

  useEffect(() => {
    clearError();
    setValidationError('');
    setSuccessMessage('');
    setShowSignupPrompt(false);
  }, [isLogin, isForgotPassword]);

  useEffect(() => {
    let strength = 0;
    if (formData.password.length >= 8) strength += 25;
    if (/[A-Z]/.test(formData.password)) strength += 25;
    if (/[0-9]/.test(formData.password)) strength += 25;
    if (/[^A-Za-z0-9]/.test(formData.password)) strength += 25;
    setPasswordStrength(strength);
  }, [formData.password]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setValidationError('');
    setSuccessMessage('');
    setShowSignupPrompt(false);
    if (error) clearError();
  };

  const validateForm = () => {
    if (isForgotPassword) {
      if (!formData.email.trim()) {
        setValidationError('Email is required');
        return false;
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
        setValidationError('Invalid email format');
        return false;
      }
      return true;
    }

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
      if (isForgotPassword) {
        setIsResetLoading(true);
        const result = await requestPasswordReset(formData.email);
        setSuccessMessage(result.detail || 'Password reset code sent. It expires in 4 minutes.');
        setTimeout(() => {
          navigate(`/reset-password?email=${encodeURIComponent(formData.email)}`);
        }, 900);
      } else if (isLogin) {
        await login(formData.username, formData.password);
        navigate(from, { replace: true });
      } else {
        await register(formData);
        navigate(from, { replace: true });
      }
    } catch (err) {
      // Error is already handled by the store, but we can add local UI effects if needed
      console.error('Auth error:', err);
      if (isForgotPassword && err.response?.status === 404) {
        setShowSignupPrompt(true);
        setValidationError(err.response?.data?.detail || 'This email is not in our database. Please sign up first.');
      } else {
        setValidationError(err.response?.data?.error || err.message || 'Request failed. Please try again.');
      }
    } finally {
      setIsResetLoading(false);
    }
  };

  const handleGithubLogin = () => {
    window.location.href = '/api/auth/oauth/github/';
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
              {isForgotPassword ? 'Recover Account Access' : isLogin ? 'Authorization Required' : 'Initialize New Account'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-1 relative">
            <AnimatePresence mode="wait">
              <motion.div
                key={isForgotPassword ? 'forgot-password' : isLogin ? 'login' : 'register'}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                {!isForgotPassword && (
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
                )}

                {(!isLogin || isForgotPassword) && (
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

                {!isForgotPassword && (
                  <div className="form-input-container">
                    <label className="form-label-premium"><Lock size={12} className="inline mr-1 mb-0.5" /> Security Key</label>
                    <div className="relative">
                      <input
                        type={showPassword ? "text" : "password"}
                        name="password"
                        value={formData.password}
                        onChange={handleChange}
                        className={cn("form-input-premium pl-12 pr-12", validationError && validationError.includes('Password') && "border-red-500/50 bg-red-500/5")}
                        placeholder="••••••••"
                        required
                      />
                      <Lock size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                      <button 
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white transition-colors"
                      >
                        {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>

                    {/* Strength Indicator */}
                    {formData.password && (
                      <div className="mt-3 px-1">
                        <div className="flex justify-between items-center mb-1.5">
                          <span className="text-[9px] uppercase tracking-wider font-bold text-slate-500">Integrity Level</span>
                          <span className={cn(
                            "text-[9px] font-bold uppercase",
                            passwordStrength <= 25 ? "text-red-500" : passwordStrength <= 50 ? "text-orange-500" : "text-emerald-500"
                          )}>
                            {passwordStrength <= 25 ? "Vulnerable" : passwordStrength <= 50 ? "Encrypted" : "Quantum Secure"}
                          </span>
                        </div>
                        <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                          <motion.div 
                            initial={{ width: 0 }}
                            animate={{ width: `${passwordStrength}%` }}
                            className={cn(
                              "h-full transition-colors duration-500",
                              passwordStrength <= 25 ? "bg-red-500" : passwordStrength <= 50 ? "bg-orange-500" : "bg-emerald-500"
                            )}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Confirm Password (Register only) */}
                {!isLogin && !isForgotPassword && (
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
                        className={cn("form-input-premium pl-12 pr-4", validationError && validationError.includes('Passwords') && "border-red-500/50 bg-red-500/5")}
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
              {(authError || validationError || successMessage) && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className={cn(
                    "text-xs font-bold py-3 px-4 rounded-xl mb-6 flex items-center",
                    successMessage
                      ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-300"
                      : "bg-accent/10 border border-accent/20 text-accent"
                  )}
                >
                  <Sparkles size={14} className="mr-2 flex-shrink-0" />
                  {successMessage || validationError || authError}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Submit Button */}
            <button
              type="submit"
              className="auth-btn-primary group flex items-center justify-center space-x-2"
              disabled={isLoading || isResetLoading}
            >
              <span>{isLoading || isResetLoading ? 'Processing...' : isForgotPassword ? 'Send Reset Code' : isLogin ? 'Initialize Sequence' : 'Create Identity'}</span>
              {!isLoading && !isResetLoading && <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />}
            </button>

            {isLogin && !isForgotPassword && (
              <button
                type="button"
                onClick={() => setIsForgotPassword(true)}
                className="w-full mt-4 text-slate-500 hover:text-white text-[11px] font-bold uppercase tracking-widest transition-colors"
              >
                Forgot password?
              </button>
            )}

            {showSignupPrompt && (
              <button
                type="button"
                onClick={() => {
                  setIsForgotPassword(false);
                  setIsLogin(false);
                  setShowSignupPrompt(false);
                  setValidationError('');
                }}
                className="w-full mt-4 py-3 bg-white/5 border border-primary/30 rounded-xl text-xs font-bold text-primary hover:bg-primary/10 transition-all duration-300 uppercase tracking-widest"
              >
                Sign up with this email
              </button>
            )}

            {/* GitHub OAuth Button */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-white/5"></div>
              </div>
              <div className="relative flex justify-center text-[10px] uppercase">
                <span className="bg-[#030712] px-4 text-slate-500 font-bold tracking-widest">External Uplink</span>
              </div>
            </div>

            <button 
              type="button"
              onClick={handleGithubLogin}
              className="w-full py-3 bg-white/5 border border-white/10 rounded-xl flex items-center justify-center gap-3 text-xs font-bold text-slate-400 hover:bg-white/10 hover:text-white transition-all duration-300 group"
            >
              <Github size={18} className="group-hover:scale-110 transition-transform" />
              Sync with Github
            </button>
          </form>

          {/* Footer Toggle */}
          <div className="mt-8 text-center">
            <button
              type="button"
              onClick={() => {
                if (isForgotPassword) {
                  setIsForgotPassword(false);
                  setIsLogin(true);
                  return;
                }
                setIsLogin(!isLogin);
              }}
              className="text-slate-500 hover:text-white text-xs font-bold uppercase tracking-widest transition-colors flex items-center justify-center mx-auto space-x-2"
            >
              <span>{isForgotPassword ? "Remembered your key?" : isLogin ? "Need a neural uplink?" : "Already have an uplink?"}</span>
              <span className="text-primary hover:underline underline-offset-4 decoration-2">
                {isForgotPassword ? 'Login' : isLogin ? 'Register' : 'Login'}
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
