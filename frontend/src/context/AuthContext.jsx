import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);
const DIRECTOR_ROLES = new Set([
  'Director / Super Admin',
  'Director / Admin',
  'Director',
  'Admin',
]);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('aarka_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('aarka_token') || null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    localStorage.removeItem('aarka_token');
    localStorage.removeItem('aarka_user');
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    const verifyAuth = async () => {
      const savedToken = localStorage.getItem('aarka_token');
      if (savedToken) {
        try {
          const res = await authAPI.getProfile();
          setUser(res.data);
          localStorage.setItem('aarka_user', JSON.stringify(res.data));
        } catch (err) {
          console.error("Session verification failed or token expired:", err);
          logout();
        }
      }
      setLoading(false);
    };
    verifyAuth();
  }, [logout]);

  const login = async (email, password) => {
    const res = await authAPI.login(email, password);
    const { access_token, user: userData } = res.data;
    localStorage.setItem('aarka_token', access_token);
    localStorage.setItem('aarka_user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const register = async (data) => {
    const res = await authAPI.register(data);
    return res.data;
  };

  const googleLogin = async (credential) => {
    const res = await authAPI.googleAuth(credential);
    const { access_token, user: userData } = res.data;
    localStorage.setItem('aarka_token', access_token);
    localStorage.setItem('aarka_user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const verifyEmail = async (tokenParam) => {
    const res = await authAPI.verifyEmail(tokenParam);
    return res.data;
  };

  const resendVerification = async (email) => {
    const res = await authAPI.resendVerification(email);
    return res.data;
  };

  const forgotPassword = async (email) => {
    const res = await authAPI.forgotPassword(email);
    return res.data;
  };

  const resetPassword = async (data) => {
    const res = await authAPI.resetPassword(data);
    return res.data;
  };

  const hasRole = (allowedRoles) => {
    if (!user) return false;
    return DIRECTOR_ROLES.has(user.role) || allowedRoles.includes(user.role);
  };

  const hasPermission = (resource, action = 'VIEW') => {
    if (!user) return false;
    if (DIRECTOR_ROLES.has(user.role)) return true;
    return !!user.permissions?.some(
      (permission) =>
        permission.resource === resource && permission.action === action
    );
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        loading,
        login,
        register,
        googleLogin,
        verifyEmail,
        resendVerification,
        forgotPassword,
        resetPassword,
        logout,
        hasRole,
        hasPermission,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
