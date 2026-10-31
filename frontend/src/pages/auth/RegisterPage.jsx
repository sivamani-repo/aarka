import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { SunMedium, Lock, Mail, User, Phone, ArrowRight, AlertCircle, Eye, EyeOff, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import GoogleSignInButton from '../../components/common/GoogleSignInButton';

export const RegisterPage = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    confirm_password: '',
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState(null);

  const { register, googleLogin } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Client-side pre-validations
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }
    if (!/[A-Za-z]/.test(formData.password) || !/\d/.test(formData.password)) {
      setError('Password must contain at least one letter and one number.');
      return;
    }
    if (formData.password !== formData.confirm_password) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      await register({
        name: formData.name,
        email: formData.email,
        phone: formData.phone || null,
        password: formData.password,
        confirm_password: formData.confirm_password,
      });
      setRegisteredEmail(formData.email);
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please check your inputs.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (credential) => {
    setError('');
    setLoading(true);
    try {
      await googleLogin(credential);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Google registration failed.');
    } finally {
      setLoading(false);
    }
  };

  // State: Verification Email Sent Screen
  if (registeredEmail) {
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
            maxWidth: '480px',
            padding: '40px 32px',
            textAlign: 'center',
            boxShadow: 'var(--shadow-lg)',
            border: '1px solid #e1e4de',
          }}
        >
          <div
            style={{
              width: '64px',
              height: '64px',
              margin: '0 auto 16px',
              borderRadius: '50%',
              backgroundColor: 'var(--color-primary-50)',
              color: 'var(--color-primary-700)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <CheckCircle2 size={36} />
          </div>

          <h2 style={{ fontSize: '22px', fontWeight: '800', fontFamily: 'var(--font-display)', marginBottom: '8px' }}>
            Check Your Email
          </h2>

          <p style={{ fontSize: '14px', color: 'var(--text-muted)', lineHeight: '1.6', marginBottom: '20px' }}>
            We've sent a verification link to <strong>{registeredEmail}</strong>.<br />
            Please click the link in your email to activate your AARKA account before logging in.
          </p>

          <div
            style={{
              backgroundColor: '#f9f9f6',
              padding: '12px 16px',
              borderRadius: 'var(--radius-md)',
              fontSize: '12px',
              color: 'var(--text-muted)',
              marginBottom: '24px',
              textAlign: 'left',
              border: '1px solid #e7e5e4',
            }}
          >
            💡 <strong>Next Steps:</strong> Check your inbox (and spam folder). The link is valid for 24 hours. Once verified, you can sign in directly.
          </div>

          <Link to="/login" className="btn btn-primary" style={{ width: '100%', textDecoration: 'none' }}>
            Return to Sign In
          </Link>
        </div>
      </div>
    );
  }

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
          maxWidth: '480px',
          padding: '36px 32px',
          boxShadow: 'var(--shadow-lg)',
          border: '1px solid #e1e4de',
        }}
      >
        {/* Brand */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              margin: '0 auto 10px',
              borderRadius: '12px',
              backgroundColor: '#1b4d36',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              boxShadow: '0 4px 12px rgba(27, 77, 54, 0.3)',
            }}
          >
            <SunMedium size={26} color="#fef08a" />
          </div>
          <h1 style={{ fontSize: '22px', fontWeight: '800', fontFamily: 'var(--font-display)', letterSpacing: '-0.02em', color: '#0c2318' }}>
            Create an Account
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '2px' }}>
            Join AARKA Solar Operations Platform
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

        {/* Google OAuth Registration */}
        <div style={{ marginBottom: '16px' }}>
          <GoogleSignInButton
            onSuccess={handleGoogleSuccess}
            onError={(msg) => setError(msg)}
            text="signup_with"
          />
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            margin: '18px 0',
            color: 'var(--text-light)',
            fontSize: '12px',
          }}
        >
          <div style={{ flex: 1, height: '1px', backgroundColor: '#e2e8f0' }} />
          <span style={{ padding: '0 10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            or register with email
          </span>
          <div style={{ flex: 1, height: '1px', backgroundColor: '#e2e8f0' }} />
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group" style={{ marginBottom: '14px' }}>
            <label className="form-label">Full Name *</label>
            <div style={{ position: 'relative' }}>
              <User size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-light)' }} />
              <input
                type="text"
                name="name"
                required
                className="form-control"
                style={{ paddingLeft: '36px' }}
                placeholder="Rajesh Kumar"
                value={formData.name}
                onChange={handleChange}
                autoComplete="name"
              />
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: '14px' }}>
            <label className="form-label">Email Address *</label>
            <div style={{ position: 'relative' }}>
              <Mail size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-light)' }} />
              <input
                type="email"
                name="email"
                required
                className="form-control"
                style={{ paddingLeft: '36px' }}
                placeholder="rajesh@example.com"
                value={formData.email}
                onChange={handleChange}
                autoComplete="email"
              />
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: '14px' }}>
            <label className="form-label">Phone Number (Optional)</label>
            <div style={{ position: 'relative' }}>
              <Phone size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-light)' }} />
              <input
                type="tel"
                name="phone"
                className="form-control"
                style={{ paddingLeft: '36px' }}
                placeholder="+91 98480 12345"
                value={formData.phone}
                onChange={handleChange}
                autoComplete="tel"
              />
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: '14px' }}>
            <label className="form-label">Password *</label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-light)' }} />
              <input
                type={showPassword ? 'text' : 'password'}
                name="password"
                required
                className="form-control"
                style={{ paddingLeft: '36px', paddingRight: '36px' }}
                placeholder="Minimum 8 characters"
                value={formData.password}
                onChange={handleChange}
                autoComplete="new-password"
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

          <div className="form-group" style={{ marginBottom: '18px' }}>
            <label className="form-label">Confirm Password *</label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-light)' }} />
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                name="confirm_password"
                required
                className="form-control"
                style={{ paddingLeft: '36px', paddingRight: '36px' }}
                placeholder="Re-enter password"
                value={formData.confirm_password}
                onChange={handleChange}
                autoComplete="new-password"
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
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
                {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '4px' }}
            disabled={loading}
          >
            {loading ? 'Creating Account...' : 'Create Account'}
            <ArrowRight size={16} />
          </button>
        </form>

        <div style={{ marginTop: '22px', textAlign: 'center', fontSize: '13px', color: 'var(--text-muted)' }}>
          Already have an account?{' '}
          <Link
            to="/login"
            style={{ color: 'var(--color-primary-700)', fontWeight: '600', textDecoration: 'none' }}
          >
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;

