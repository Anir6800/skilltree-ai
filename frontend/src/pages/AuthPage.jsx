/**
 * SkillTree AI - Authentication Page
 * Login and registration page with glassmorphism design
 * @module pages/AuthPage
 */

import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import useAuthStore from '../store/authStore';

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

  // Get redirect path from location state
  const from = location.state?.from?.pathname || '/dashboard';

  /**
   * Handle input change
   * @param {React.ChangeEvent<HTMLInputElement>} e - Change event
   */
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    clearError();
    setValidationError('');
  };

  /**
   * Validate form data
   * @returns {boolean} Whether form is valid
   */
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

  /**
   * Handle form submission
   * @param {React.FormEvent<HTMLFormElement>} e - Form event
   */
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
      // Error is handled by store
    }
  };

  /**
   * Toggle between login and register
   */
  const toggleMode = () => {
    setIsLogin(!isLogin);
    clearError();
    setValidationError('');
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-card glass-panel">
          <div className="auth-header">
            <h1 className="auth-title">
              SkillTree <span className="premium-gradient-text">AI</span>
            </h1>
            <p className="auth-subtitle">
              {isLogin ? 'Welcome back, adventurer!' : 'Begin your journey!'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="auth-form">
            <div className="form-group">
              <label htmlFor="username" className="form-label">Username</label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleChange}
                className="form-input"
                placeholder="Enter your username"
                autoComplete="username"
                required
              />
            </div>

            {!isLogin && (
              <div className="form-group">
                <label htmlFor="email" className="form-label">Email</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="form-input"
                  placeholder="Enter your email"
                  autoComplete="email"
                  required
                />
              </div>
            )}

            <div className="form-group">
              <label htmlFor="password" className="form-label">Password</label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className="form-input"
                placeholder="Enter your password"
                autoComplete={isLogin ? 'current-password' : 'new-password'}
                required
              />
            </div>

            {!isLogin && (
              <div className="form-group">
                <label htmlFor="passwordConfirm" className="form-label">Confirm Password</label>
                <input
                  type="password"
                  id="passwordConfirm"
                  name="passwordConfirm"
                  value={formData.passwordConfirm}
                  onChange={handleChange}
                  className="form-input"
                  placeholder="Confirm your password"
                  autoComplete="new-password"
                  required
                />
              </div>
            )}

            {(error || validationError) && (
              <div className="form-error">
                {validationError || error}
              </div>
            )}

            <button
              type="submit"
              className="auth-button primary-cta"
              disabled={isLoading}
            >
              {isLoading ? 'Please wait...' : isLogin ? 'Sign In' : 'Create Account'}
            </button>
          </form>

          <div className="auth-footer">
            <p>
              {isLogin ? "Don't have an account?" : 'Already have an account?'}
              <button
                type="button"
                onClick={toggleMode}
                className="auth-link"
              >
                {isLogin ? 'Sign Up' : 'Sign In'}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AuthPage;