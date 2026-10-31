import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { SunMedium, CheckCircle, AlertTriangle, ArrowRight, Mail, RefreshCw } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const VerifyEmailPage = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  const [status, setStatus] = useState(token ? 'VERIFYING' : 'NO_TOKEN'); // VERIFYING | SUCCESS | ERROR | NO_TOKEN
  const [message, setMessage] = useState('');
  const [resendEmail, setResendEmail] = useState('');
  const [resending, setResending] = useState(false);
  const [resendMessage, setResendMessage] = useState('');

  const { verifyEmail, resendVerification } = useAuth();

  useEffect(() => {
    if (!token) return;

    const performVerification = async () => {
      try {
        const data = await verifyEmail(token);
        setStatus('SUCCESS');
        setMessage(data.message || 'Email successfully verified! You can now log in.');
      } catch (err) {
        setStatus('ERROR');
        setMessage(err.response?.data?.detail || 'Verification link is invalid or has expired.');
      }
    };

    performVerification();
  }, [token, verifyEmail]);

  const handleResend = async (e) => {
    e.preventDefault();
    if (!resendEmail) return;
    setResending(true);
    setResendMessage('');
    try {
      const data = await resendVerification(resendEmail);
      setResendMessage(data.message || 'Verification link sent! Please check your inbox.');
    } catch (err) {
      setResendMessage(err.response?.data?.detail || 'Failed to resend verification email.');
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
          maxWidth: '460px',
          padding: '40px 32px',
          textAlign: 'center',
          boxShadow: 'var(--shadow-lg)',
          border: '1px solid #e1e4de',
        }}
      >
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
            AARKA Email Verification
          </h1>
        </div>

        {/* State: Verifying */}
        {status === 'VERIFYING' && (
          <div style={{ padding: '20px 0' }}>
            <div
              style={{
                width: '40px',
                height: '40px',
                margin: '0 auto 16px',
                border: '3px solid #1b4d36',
                borderTopColor: 'transparent',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
              }}
            />
            <p style={{ fontSize: '15px', color: 'var(--text-muted)' }}>
              Validating your verification token...
            </p>
          </div>
        )}

        {/* State: Success */}
        {status === 'SUCCESS' && (
          <div style={{ padding: '10px 0' }}>
            <div
              style={{
                width: '60px',
                height: '60px',
                margin: '0 auto 16px',
                borderRadius: '50%',
                backgroundColor: 'var(--color-primary-50)',
                color: 'var(--color-primary-600)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <CheckCircle size={36} />
            </div>
            <h2 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '8px' }}>
              Email Successfully Verified!
            </h2>
            <p style={{ fontSize: '14px', color: 'var(--text-muted)', lineHeight: '1.6', marginBottom: '24px' }}>
              {message}
            </p>
            <Link to="/login" className="btn btn-primary" style={{ width: '100%', textDecoration: 'none' }}>
              Sign In to Your Account <ArrowRight size={16} />
            </Link>
          </div>
        )}

        {/* State: Error / Invalid Token */}
        {(status === 'ERROR' || status === 'NO_TOKEN') && (
          <div style={{ padding: '10px 0' }}>
            <div
              style={{
                width: '60px',
                height: '60px',
                margin: '0 auto 16px',
                borderRadius: '50%',
                backgroundColor: 'var(--color-rose-50)',
                color: 'var(--color-rose-600)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <AlertTriangle size={36} />
            </div>
            <h2 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '8px', color: '#1c1917' }}>
              {status === 'NO_TOKEN' ? 'Missing Verification Token' : 'Verification Link Expired or Invalid'}
            </h2>
            <p style={{ fontSize: '14px', color: 'var(--text-muted)', lineHeight: '1.6', marginBottom: '20px' }}>
              {message || 'No verification token was detected in your link.'}
            </p>

            {/* Resend Form */}
            <div
              style={{
                backgroundColor: '#f9f9f6',
                border: '1px solid #e7e5e4',
                borderRadius: 'var(--radius-md)',
                padding: '18px 16px',
                textAlign: 'left',
                marginBottom: '20px',
              }}
            >
              <h3 style={{ fontSize: '13px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '8px' }}>
                Request a New Verification Link
              </h3>
              {resendMessage && (
                <div style={{ fontSize: '12px', padding: '8px', borderRadius: '4px', backgroundColor: '#e0f2fe', color: '#0369a1', marginBottom: '10px' }}>
                  {resendMessage}
                </div>
              )}
              <form onSubmit={handleResend}>
                <div style={{ position: 'relative', marginBottom: '10px' }}>
                  <Mail size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-light)' }} />
                  <input
                    type="email"
                    required
                    placeholder="Enter your registered email"
                    className="form-control"
                    style={{ paddingLeft: '36px', fontSize: '13px' }}
                    value={resendEmail}
                    onChange={(e) => setResendEmail(e.target.value)}
                  />
                </div>
                <button
                  type="submit"
                  disabled={resending}
                  className="btn btn-secondary btn-sm"
                  style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
                >
                  <RefreshCw size={14} className={resending ? 'animate-spin' : ''} />
                  {resending ? 'Sending...' : 'Send New Verification Link'}
                </button>
              </form>
            </div>

            <Link to="/login" style={{ fontSize: '13px', color: 'var(--color-primary-700)', textDecoration: 'none', fontWeight: '600' }}>
              Return to Login
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default VerifyEmailPage;

