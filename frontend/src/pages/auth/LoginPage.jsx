import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { SunMedium, Lock, Mail, ArrowRight, AlertCircle, Eye, EyeOff, CheckCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import GoogleSignInButton from '../../components/common/GoogleSignInButton';

export const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [infoMessage, setInfoMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [unverifiedEmail, setUnverifiedEmail] = useState(null);
  const [resending, setResending] = useState(false);

  const { login, googleLogin, resendVerification } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setInfoMessage('');
    setUnverifiedEmail(null);
    setLoading(true);

    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      const detail = err.response?.data?.detail || 'Invalid email or password.';
      setError(detail);

      // If account is unverified, offer resend option
      if (err.response?.status === 403 && detail.toLowerCase().includes('not verified')) {
        setUnverifiedEmail(email);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (credential) => {
    setError('');
    setInfoMessage('');
    setLoading(true);
    try {
      await googleLogin(credential);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Google authentication failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (!unverifiedEmail) return;
    setResending(true);
    try {
      await resendVerification(unverifiedEmail);
      setInfoMessage(`A fresh verification link has been sent to ${unverifiedEmail}. Please check your inbox.`);
      setUnverifiedEmail(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to resend verification link.');
    } finally {
      setResending(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: '#f6f7f4',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
      }}
    >
      <div
        className="aarka-card"
        style={{
          width: '100%',
          maxWidth: '440px',
          padding: '36px 32px',
          boxShadow: 'var(--shadow-lg)',
          border: '1px solid #e1e4de',
        }}
      >
        {/* Brand */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div
            style={{
              width: '52px',
              height: '52px',
              margin: '0 auto 12px',
              borderRadius: '14px',
              backgroundColor: '#1b4d36',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              boxShadow: '0 4px 12px rgba(27, 77, 54, 0.3)',
            }}
          >
            <SunMedium size={30} color="#fef08a" />
          </div>
          <h1 style={{ fontSize: '24px', fontWeight: '800', fontFamily: 'var(--font-display)', letterSpacing: '-0.02em', color: '#0c2318' }}>
            AARKA
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '2px' }}>
            Solar Operations, Simplified.
          </p>
        </div>

        {error && (
          <div
            style={{
              backgroundColor: 'var(--color-rose-50)',
              border: '1px solid var(--color-rose-100)',
              color: 'var(--color-rose-600)',
              padding: '10px 14px',
              borderRadius: 'var(--radius-md)',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '16px',
            }}
          >
            <AlertCircle size={16} />
            <div style={{ flex: 1 }}>{error}</div>
          </div>
        )}

        {unverifiedEmail && (
          <div
            style={{
              backgroundColor: '#eff6ff',
              border: '1px solid #bfdbfe',
              color: '#1e40af',
              padding: '10px 14px',
              borderRadius: 'var(--radius-md)',
              fontSize: '13px',
              marginBottom: '16px',
            }}
          >
            <p style={{ margin: '0 0 8px 0' }}>Need a new verification link?</p>
            <button
              type="button"
              onClick={handleResend}
              disabled={resending}
              className="btn btn-secondary btn-sm"
              style={{ fontSize: '12px' }}
            >
              {resending ? 'Sending...' : 'Resend Verification Email'}
            </button>
          </div>
        )}

        {infoMessage && (
          <div
            style={{
              backgroundColor: 'var(--color-primary-50)',
              border: '1px solid var(--color-primary-100)',
              color: 'var(--color-primary-800)',
              padding: '10px 14px',
              borderRadius: 'var(--radius-md)',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '16px',
            }}
          >
            <CheckCircle size={16} color="var(--color-primary-600)" />
            <span>{infoMessage}</span>
          </div>
        )}

        {/* Google OAuth Sign-In */}
        <div style={{ marginBottom: '20px' }}>
          <GoogleSignInButton
            onSuccess={handleGoogleSuccess}
            onError={(msg) => setError(msg)}
            text="signin_with"
          />
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            margin: '20px 0',
            color: 'var(--text-light)',
            fontSize: '12px',
          }}
        >
          <div style={{ flex: 1, height: '1px', backgroundColor: '#e2e8f0' }} />
          <span style={{ padding: '0 10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            or sign in with email
          </span>
          <div style={{ flex: 1, height: '1px', backgroundColor: '#e2e8f0' }} />
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group" style={{ marginBottom: '16px' }}>
            <label className="form-label">Email Address</label>
            <div style={{ position: 'relative' }}>
              <Mail size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-light)' }} />
              <input
                type="email"
                required
                className="form-control"
                style={{ paddingLeft: '36px' }}
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <label className="form-label" style={{ marginBottom: 0 }}>Password</label>
              <Link
                to="/forgot-password"
                style={{ fontSize: '12px', color: 'var(--color-primary-700)', textDecoration: 'none', fontWeight: '500' }}
              >
                Forgot password?
              </Link>
            </div>
            <div style={{ position: 'relative' }}>
              <Lock size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-light)' }} />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                className="form-control"
                style={{ paddingLeft: '36px', paddingRight: '36px' }}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: 'var(--text-light)',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '8px' }}
            disabled={loading}
          >
            {loading ? 'Signing in...' : 'Sign In to Operations'}
            <ArrowRight size={16} />
          </button>
        </form>

        {/* Footer: Create Account Link */}
        <div style={{ marginTop: '24px', textAlign: 'center', fontSize: '13px', color: 'var(--text-muted)' }}>
          Don't have an account?{' '}
          <Link
            to="/register"
            style={{ color: 'var(--color-primary-700)', fontWeight: '600', textDecoration: 'none' }}
          >
            Create an Account
          </Link>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
