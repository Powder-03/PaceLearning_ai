import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { User } from '../types';
import { authService } from '../services';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => void;
  updateUser: (user: User) => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'));
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!token && !!user;

  // Load user on mount if token exists
  useEffect(() => {
    const loadUser = async () => {
      if (token) {
        try {
          const userData = await authService.verifyToken();
          setUser(userData);
        } catch (error) {
          // Token invalid, clear it
          localStorage.removeItem('token');
          setToken(null);
          setUser(null);
        }
      }
      setIsLoading(false);
    };

    loadUser();
  }, [token]);

  const login = useCallback(async (email: string, password: string) => {
    const response = await authService.login({ email, password });
    localStorage.setItem('token', response.access_token);
    setToken(response.access_token);
    setUser(response.user);
  }, []);

  const register = useCallback(async (email: string, password: string, name?: string) => {
    const response = await authService.register({ email, password, name });
    localStorage.setItem('token', response.access_token);
    setToken(response.access_token);
    setUser(response.user);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  }, []);

  const updateUser = useCallback((updatedUser: User) => {
    setUser(updatedUser);
  }, []);

  const refreshUser = useCallback(async () => {
    if (token) {
      try {
        // Use refreshToken to get a new JWT with updated is_verified status
        const response = await authService.refreshToken();
        localStorage.setItem('token', response.access_token);
        setToken(response.access_token);
        setUser(response.user);
      } catch (error) {
        console.error('Failed to refresh user:', error);
        // If refresh fails, try to at least get user data
        try {
          const userData = await authService.getMe();
          setUser(userData);
        } catch {
          // Token is invalid
          localStorage.removeItem('token');
          setToken(null);
          setUser(null);
        }
      }
    }
  }, [token]);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated,
        login,
        register,
        logout,
        updateUser,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
