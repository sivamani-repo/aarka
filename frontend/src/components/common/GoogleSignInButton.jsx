import React from 'react';
import { GoogleLogin } from '@react-oauth/google';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

export const GoogleSignInButton = ({ onSuccess, onError, text = "signin_with" }) => {
  // If client ID is not configured or is placeholder, render accessible fallback button
  if (!GOOGLE_CLIENT_ID || GOOGLE_CLIENT_ID === 'your_google_oauth_client_id') {
    return (
      <button
        type="button"
        onClick={() => {
          if (onError) {
            onError("Google Sign-In is disabled: VITE_GOOGLE_CLIENT_ID has not been configured in frontend/.env yet.");
          }
        }}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '10px',
          padding: '10px 16px',
          backgroundColor: '#ffffff',
          color: '#3c4043',
          border: '1px solid #dadce0',
          borderRadius: 'var(--radius-md)',
          fontSize: '14px',
          fontWeight: '500',
          cursor: 'pointer',
          transition: 'background-color 0.2s',
          boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
        }}
        onMouseOver={(e) => (e.currentTarget.style.backgroundColor = '#f8f9fa')}
        onMouseOut={(e) => (e.currentTarget.style.backgroundColor = '#ffffff')}
      >
        <svg width="18" height="18" viewBox="0 0 18 18">
          <path
            fill="#4285F4"
            d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.616z"
          />
          <path
            fill="#34A853"
            d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332C2.438 15.983 5.482 18 9 18z"
          />
          <path
            fill="#FBBC05"
            d="M3.964 10.707c-.18-.54-.282-1.117-.282-1.707s.102-1.167.282-1.707V4.961H.957C.347 6.175 0 7.55 0 9s.347 2.825.957 4.039l3.007-2.332z"
          />
          <path
            fill="#EA4335"
            d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.438 2.017.957 4.961L3.964 7.293C4.672 5.166 6.656 3.58 9 3.58z"
          />
        </svg>
        <span>Continue with Google</span>
      </button>
    );
  }

  return (
    <div style={{ width: '100%', display: 'flex', justifyContent: 'center' }}>
      <GoogleLogin
        onSuccess={(credentialResponse) => {
          if (credentialResponse.credential && onSuccess) {
            onSuccess(credentialResponse.credential);
          }
        }}
        onError={() => {
          if (onError) {
            onError("Google Sign-In failed or popup was closed.");
          }
        }}
        text={text}
        shape="rectangular"
        size="large"
        width="100%"
      />
    </div>
  );
};

export default GoogleSignInButton;

