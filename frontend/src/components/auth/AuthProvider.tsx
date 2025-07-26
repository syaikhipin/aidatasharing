'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { authAPI } from '@/lib/api';

interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  organization_id?: number;
  role?: string;
  organization_name?: string;
  created_at?: string;
  updated_at?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const initializeAuth = async () => {
      // Check if we're in the browser (client-side)
      if (typeof window !== 'undefined') {
        const storedToken = localStorage.getItem('access_token');
        if (storedToken) {
          setToken(storedToken);
          try {
            const user = await authAPI.getMe();
            setUser(user);
          } catch (error) {
            console.error('Failed to fetch user on initial load:', error);
            localStorage.removeItem('access_token');
            setToken(null);
            setUser(null);
          }
        }
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (authToken: string) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', authToken);
    }
    setToken(authToken);
    try {
      const user = await authAPI.getMe();
      setUser(user);
    } catch (error) {
      console.error('Failed to fetch user after login:', error);
      // Clear auth state if getMe fails
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
      }
      setToken(null);
      setUser(null);
    }
  };

  const logout = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
    }
    setToken(null);
    setUser(null);
    router.push('/');
  };

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    login,
    logout,
    isAuthenticated: !isLoading && !!token && !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
} 