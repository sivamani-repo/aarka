import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('aarka_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('aarka_token') || null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const verifyAuth = async () => {
      const savedToken = localStorage.getItem('aarka_token');
      if (savedToken) {
        try {
          const res = await authAPI.getProfile();
          setUser(res.data);
          localStorage.setItem('aarka_user', JSON.stringify(res.data));
        } catch (err) {
          console.error("Token verification failed:", err);
          logout();
        }
      }
      setLoading(false);
    };
    verifyAuth();
  }, []);

  const login = async (email, password) => {
    const res = await authAPI.login(email, password);
    const { access_token, user: userData } = res.data;
    localStorage.setItem('aarka_token', access_token);
    localStorage.setItem('aarka_user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const logout = () => {
    localStorage.removeItem('aarka_token');
    localStorage.removeItem('aarka_user');
    setToken(null);
    setUser(null);
  };

  const hasRole = (allowedRoles) => {
    if (!user) return false;
    if (user.role === 'Director / Admin' || user.role === 'Admin' || user.role === 'Director') {
      return true;
    }
    return allowedRoles.includes(user.role);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        loading,
        login,
        logout,
        hasRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

