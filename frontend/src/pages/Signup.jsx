import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function getPasswordStrength(password) {
  if (!password) return { score: 0, label: '', color: '' };
  let score = 0;
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;
  if (score <= 1) return { score, label: 'Very weak', color: 'bg-red-500' };
  if (score === 2) return { score, label: 'Weak', color: 'bg-orange-500' };
  if (score === 3) return { score, label: 'Fair', color: 'bg-yellow-500' };
  if (score === 4) return { score, label: 'Strong', color: 'bg-blue-500' };
  return { score, label: 'Very strong', color: 'bg-green-500' };
}

export default function Signup() {
  const { signup, loading, error, setError } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  const [success, setSuccess] = useState(false);

  const strength = useMemo(() => getPasswordStrength(password), [password]);

  const validate = () => {
    const errs = {};
    if (!username.trim()) errs.username = 'Username is required';
    else if (username.trim().length < 3) errs.username = 'At least 3 characters';
    else if (!/^[a-zA-Z0-9_-]+$/.test(username))
      errs.username = 'Only letters, numbers, _ and -';

    if (!email.trim()) errs.email = 'Email is required';
    else if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) errs.email = 'Enter a valid email';

    if (!password) errs.password = 'Password is required';
    else if (password.length < 8) errs.password = 'At least 8 characters';

    if (!confirmPassword) errs.confirmPassword = 'Please confirm your password';
    else if (password !== confirmPassword) errs.confirmPassword = 'Passwords do not match';

    if (!acceptTerms) errs.terms = 'You must accept the terms';

    return errs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    const errs = validate();
    if (Object.keys(errs).length) {
      setFieldErrors(errs);
      return;
    }
    setFieldErrors({});
    try {
      await signup(username.trim(), email.trim(), password);
      setSuccess(true);
      setTimeout(() => navigate('/dashboard', { replace: true }), 1200);
    } catch {
      // error already set by AuthContext
    }
  };

  return (
    <div className="min-h-screen bg-[#0d1117] flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <button onClick={() => navigate('/')} className="inline-block">
            <span className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
              JARVIS
            </span>
          </button>
          <p className="text-gray-500 mt-1 text-sm">AI Assistant</p>
        </div>

        <div className="bg-[#161b22] border border-[#21262d] rounded-2xl p-8">
          <h1 className="text-xl font-bold text-white mb-2">Create your account</h1>
          <p className="text-gray-400 text-sm mb-6">
            Join JARVIS and start chatting with the smartest AI routing system.
          </p>

          {/* Success */}
          {success && (
            <div className="mb-4 px-4 py-3 bg-green-500/10 border border-green-500/30 rounded-lg text-green-400 text-sm">
              🎉 Account created! Redirecting to dashboard…
            </div>
          )}

          {/* Global error */}
          {error && !success && (
            <div className="mb-4 px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate>
            {/* Username */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-300 mb-1.5">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => { setUsername(e.target.value); setFieldErrors((p) => ({ ...p, username: undefined })); }}
                placeholder="john_doe"
                autoComplete="username"
                className={`w-full px-3 py-2.5 bg-[#0d1117] border rounded-lg text-white placeholder-gray-600 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-colors ${
                  fieldErrors.username ? 'border-red-500/70' : 'border-[#30363d] focus:border-blue-500/50'
                }`}
              />
              {fieldErrors.username && (
                <p className="mt-1 text-xs text-red-400">{fieldErrors.username}</p>
              )}
            </div>

            {/* Email */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-300 mb-1.5">
                Email address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => { setEmail(e.target.value); setFieldErrors((p) => ({ ...p, email: undefined })); }}
                placeholder="you@example.com"
                autoComplete="email"
                className={`w-full px-3 py-2.5 bg-[#0d1117] border rounded-lg text-white placeholder-gray-600 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-colors ${
                  fieldErrors.email ? 'border-red-500/70' : 'border-[#30363d] focus:border-blue-500/50'
                }`}
              />
              {fieldErrors.email && (
                <p className="mt-1 text-xs text-red-400">{fieldErrors.email}</p>
              )}
            </div>

            {/* Password */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-300 mb-1.5">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); setFieldErrors((p) => ({ ...p, password: undefined })); }}
                  placeholder="Min. 8 characters"
                  autoComplete="new-password"
                  className={`w-full px-3 py-2.5 bg-[#0d1117] border rounded-lg text-white placeholder-gray-600 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-colors pr-10 ${
                    fieldErrors.password ? 'border-red-500/70' : 'border-[#30363d] focus:border-blue-500/50'
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                  tabIndex={-1}
                >
                  {showPassword ? '🙈' : '👁'}
                </button>
              </div>

              {/* Password strength bar */}
              {password && (
                <div className="mt-2">
                  <div className="flex gap-1 mb-1">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <div
                        key={i}
                        className={`h-1 flex-1 rounded-full transition-all ${
                          i <= strength.score ? strength.color : 'bg-[#21262d]'
                        }`}
                      />
                    ))}
                  </div>
                  <p className="text-xs text-gray-500">{strength.label}</p>
                </div>
              )}

              {fieldErrors.password && (
                <p className="mt-1 text-xs text-red-400">{fieldErrors.password}</p>
              )}
            </div>

            {/* Confirm Password */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-300 mb-1.5">
                Confirm password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => { setConfirmPassword(e.target.value); setFieldErrors((p) => ({ ...p, confirmPassword: undefined })); }}
                placeholder="••••••••"
                autoComplete="new-password"
                className={`w-full px-3 py-2.5 bg-[#0d1117] border rounded-lg text-white placeholder-gray-600 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-colors ${
                  fieldErrors.confirmPassword ? 'border-red-500/70' : 'border-[#30363d] focus:border-blue-500/50'
                }`}
              />
              {fieldErrors.confirmPassword && (
                <p className="mt-1 text-xs text-red-400">{fieldErrors.confirmPassword}</p>
              )}
            </div>

            {/* Terms */}
            <div className="flex items-start gap-2 mb-6">
              <input
                id="terms"
                type="checkbox"
                checked={acceptTerms}
                onChange={(e) => { setAcceptTerms(e.target.checked); setFieldErrors((p) => ({ ...p, terms: undefined })); }}
                className="w-4 h-4 mt-0.5 accent-blue-500 cursor-pointer flex-shrink-0"
              />
              <label htmlFor="terms" className="text-sm text-gray-400 cursor-pointer leading-relaxed">
                I agree to the{' '}
                <span className="text-blue-400 hover:text-blue-300">Terms of Service</span>
                {' '}and{' '}
                <span className="text-blue-400 hover:text-blue-300">Privacy Policy</span>
              </label>
            </div>
            {fieldErrors.terms && (
              <p className="-mt-4 mb-4 text-xs text-red-400">{fieldErrors.terms}</p>
            )}

            <button
              type="submit"
              disabled={loading || success}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed rounded-lg font-semibold text-sm transition-colors flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Creating account…
                </>
              ) : (
                'Create account'
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-500">
            Already have an account?{' '}
            <button
              onClick={() => navigate('/login')}
              className="text-blue-400 hover:text-blue-300 font-medium transition-colors"
            >
              Sign in
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
