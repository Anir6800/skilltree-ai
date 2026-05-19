import { useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowRight, Eye, EyeOff, KeyRound, Lock, Mail, ShieldCheck, Sparkles, Zap } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import CinemaContainer from '../components/layout/CinemaContainer';
import PulsingCore from '../components/nexus/PulsingCore';
import { resetPassword } from '../api/authApi';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const ResetPasswordPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const emailFromQuery = searchParams.get('email') || '';
  const [formData, setFormData] = useState({
    email: emailFromQuery,
    code: '',
    password: '',
    passwordConfirm: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const passwordStrength = useMemo(() => {
    let strength = 0;
    if (formData.password.length >= 8) strength += 25;
    if (/[A-Z]/.test(formData.password)) strength += 25;
    if (/[0-9]/.test(formData.password)) strength += 25;
    if (/[^A-Za-z0-9]/.test(formData.password)) strength += 25;
    return strength;
  }, [formData.password]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((current) => ({ ...current, [name]: name === 'code' ? value.toUpperCase() : value }));
    setError('');
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setMessage('');

    if (!formData.email.trim()) {
      setError('Email is required.');
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      setError('Enter a valid email address.');
      return;
    }

    if (!/^(?=(?:.*\d){6})(?=.*[A-Z])[A-Z0-9]{7}$/.test(formData.code)) {
      setError('Enter the 7-character reset code from your email.');
      return;
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }

    if (formData.password !== formData.passwordConfirm) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      await resetPassword(formData.email, formData.code, formData.password, formData.passwordConfirm);
      setMessage('Password reset successfully. Redirecting to login...');
      setTimeout(() => navigate('/login', { replace: true }), 1800);
    } catch (err) {
      setError(err.response?.data?.error || err.response?.data?.code?.[0] || err.response?.data?.new_password?.[0] || 'Could not reset password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative w-full min-h-screen bg-background overflow-hidden flex items-center justify-center p-6">
      <div className="absolute inset-0 z-0">
        <CinemaContainer>
          <PulsingCore />
        </CinemaContainer>
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.94, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="relative z-10 w-full max-w-lg"
      >
        <div className="glass-panel p-10 rounded-[2rem] border-white/5 shadow-2xl backdrop-blur-3xl overflow-hidden">
          <div className="text-center mb-9">
            <div className="inline-block mb-4 p-3 rounded-2xl bg-gradient-to-br from-primary to-accent shadow-lg shadow-primary/20">
              <Zap size={32} className="text-white" fill="currentColor" />
            </div>
            <h1 className="text-4xl font-black tracking-tighter mb-2">
              RESET <span className="premium-gradient-text uppercase">PASSWORD</span>
            </h1>
            <p className="text-slate-400 font-medium tracking-wide text-sm uppercase">
              Reset code expires after 4 minutes
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-1">
            <div className="form-input-container">
              <label className="form-label-premium"><Mail size={12} className="inline mr-1 mb-0.5" /> Account Email</label>
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
            </div>

            <div className="form-input-container">
              <label className="form-label-premium"><KeyRound size={12} className="inline mr-1 mb-0.5" /> Reset Code</label>
              <div className="relative">
                <input
                  type="text"
                  name="code"
                  value={formData.code}
                  onChange={handleChange}
                  className="form-input-premium pl-12 pr-4 tracking-[0.35em] uppercase"
                  placeholder="123456A"
                  maxLength={7}
                  required
                />
                <KeyRound size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
              </div>
            </div>

            <div className="form-input-container">
              <label className="form-label-premium"><Lock size={12} className="inline mr-1 mb-0.5" /> New Security Key</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  className="form-input-premium pl-12 pr-12"
                  placeholder="••••••••"
                  required
                />
                <Lock size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                <button
                  type="button"
                  onClick={() => setShowPassword((current) => !current)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>

              {formData.password && (
                <div className="mt-3 px-1">
                  <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${passwordStrength}%` }}
                      className={cn(
                        'h-full transition-colors duration-500',
                        passwordStrength <= 25 ? 'bg-red-500' : passwordStrength <= 50 ? 'bg-orange-500' : 'bg-emerald-500'
                      )}
                    />
                  </div>
                </div>
              )}
            </div>

            <div className="form-input-container">
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
            </div>

            <AnimatePresence>
              {(error || message) && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className={cn(
                    'text-xs font-bold py-3 px-4 rounded-xl mb-6 flex items-center',
                    error ? 'bg-accent/10 border border-accent/20 text-accent' : 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-300'
                  )}
                >
                  <Sparkles size={14} className="mr-2 flex-shrink-0" />
                  {error || message}
                </motion.div>
              )}
            </AnimatePresence>

            <button type="submit" className="auth-btn-primary group flex items-center justify-center space-x-2" disabled={loading}>
              <span>{loading ? 'Resetting...' : 'Reset Password'}</span>
              {!loading && <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />}
            </button>
          </form>

          <div className="mt-8 text-center">
            <Link to="/login" className="text-slate-500 hover:text-white text-xs font-bold uppercase tracking-widest transition-colors">
              Back to login
            </Link>
          </div>
        </div>
      </motion.div>
      <div className="fixed inset-0 pointer-events-none shadow-[inset_0_0_150px_rgba(0,0,0,0.9)] z-0" />
    </div>
  );
};

export default ResetPasswordPage;
