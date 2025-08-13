'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { authAPI } from '@/lib/api';
import { useAuth } from '@/components/auth/AuthProvider';
import DemoUsersDisplay from '@/components/auth/DemoUsersDisplay';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface DemoUser {
  email: string;
  password: string;
  role: string;
  description: string;
  organization: string | null;
  full_name: string;
  is_superuser: boolean;
}

export default function LoginPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [selectedDemoUser, setSelectedDemoUser] = useState<string>('');
  const [demoUsers, setDemoUsers] = useState<DemoUser[]>([]);
  const [loadingDemoUsers, setLoadingDemoUsers] = useState(true);
  const router = useRouter();
  const { login } = useAuth();

  // Fetch all demo users from backend
  useEffect(() => {
    const fetchDemoUsers = async () => {
      try {
        const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${API_BASE_URL}/api/auth/demo-users`);
        if (response.ok) {
          const data = await response.json();
          setDemoUsers(data.demo_users || []);
        } else {
          console.warn('Could not fetch demo users from API');
          // Fallback to hardcoded demo users if API fails
          setDemoUsers([
            {
              email: "superadmin@platform.com",
              password: "SuperAdmin123!",
              description: "Platform Superadmin (full platform access)",
              full_name: "Platform Superadmin"
            },
            {
              email: "alice.manager@techcorp.com",
              password: "TechManager123!",
              description: "TechCorp Solutions - Organization Admin",
              full_name: "Alice Johnson"
            },
            {
              email: "bob.analyst@techcorp.com",
              password: "TechAnalyst123!",
              description: "TechCorp Solutions - Organization Member",
              full_name: "Bob Smith"
            },
            {
              email: "carol.researcher@datasciencehub.com",
              password: "DataResearch123!",
              description: "DataScience Hub - Organization Admin",
              full_name: "Carol Davis"
            },
            {
              email: "david.scientist@datasciencehub.com",
              password: "DataScience123!",
              description: "DataScience Hub - Organization Member",
              full_name: "David Wilson"
            }
          ]);
        }
      } catch (error) {
        console.warn('Error fetching demo users:', error);
        // Fallback to hardcoded demo users
        setDemoUsers([
          {
            email: "superadmin@platform.com",
            password: "SuperAdmin123!",
            description: "Platform Superadmin (full platform access)",
            full_name: "Platform Superadmin"
          },
          {
            email: "alice.manager@techcorp.com",
            password: "TechManager123!",
            description: "TechCorp Solutions - Organization Admin",
            full_name: "Alice Johnson"
          },
          {
            email: "bob.analyst@techcorp.com",
            password: "TechAnalyst123!",
            description: "TechCorp Solutions - Organization Member",
            full_name: "Bob Smith"
          },
          {
            email: "carol.researcher@datasciencehub.com",
            password: "DataResearch123!",
            description: "DataScience Hub - Organization Admin",
            full_name: "Carol Davis"
          },
          {
            email: "david.scientist@datasciencehub.com",
            password: "DataScience123!",
            description: "DataScience Hub - Organization Member",
            full_name: "David Wilson"
          }
        ]);
      } finally {
        setLoadingDemoUsers(false);
      }
    };

    fetchDemoUsers();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setIsLoading(true);
    try {
      const response = await authAPI.login(formData.email, formData.password);

      if (response.access_token) {
        await login(response.access_token);
        router.push('/dashboard');
      }
    } catch (error: any) {
      console.error('Login error:', error);
      setErrors({
        submit: error.response?.data?.detail || 'Login failed. Please try again.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoUserSelect = (value: string) => {
    setSelectedDemoUser(value);
    const user = demoUsers.find(u => u.email === value);
    if (user) {
      setFormData({
        email: user.email,
        password: user.password
      });
      setErrors({});
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md animate-fade-in">
        <Card variant="elevated" className="shadow-xl">
          <CardHeader className="text-center pb-6">
            <div className="w-16 h-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">🚀</span>
            </div>
            <CardTitle className="text-2xl font-bold text-gray-900">
              Welcome Back
            </CardTitle>
            <CardDescription className="text-gray-600">
              Sign in to your AI Share Platform account
            </CardDescription>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Simple Demo User Selector */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Quick Login (Demo Accounts)
                </label>
                {loadingDemoUsers ? (
                  <div className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-gray-50 flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                    <span className="text-sm text-gray-500">Loading accounts...</span>
                  </div>
                ) : (
                  <Select value={selectedDemoUser} onValueChange={handleDemoUserSelect}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder={`Choose from ${demoUsers.length} demo accounts...`} />
                    </SelectTrigger>
                    <SelectContent className="max-h-80 bg-white border border-gray-200 shadow-lg z-50">
                      {demoUsers.map((user) => (
                        <SelectItem key={user.email} value={user.email} className="py-2">
                          <div className="flex items-center space-x-2">
                            <span className="font-medium">{user.full_name}</span>
                            <span className="text-sm text-gray-500">({user.email})</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
                <p className="text-xs text-gray-500 mt-1">
                  {loadingDemoUsers ? 'Loading demo accounts...' : `${demoUsers.length} demo accounts available - select one to auto-fill credentials`}
                </p>
              </div>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white text-gray-500">or enter manually</span>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                    Email address
                  </label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={formData.email}
                    onChange={handleChange}
                    className={`w-full px-4 py-3 border rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${
                      errors.email ? 'border-red-300 bg-red-50' : 'border-gray-300 hover:border-gray-400'
                    }`}
                    placeholder="Enter your email"
                  />
                  {errors.email && (
                    <p className="mt-2 text-sm text-red-600 flex items-center">
                      <span className="mr-1">⚠️</span>
                      {errors.email}
                    </p>
                  )}
                </div>

                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                    Password
                  </label>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    autoComplete="current-password"
                    required
                    value={formData.password}
                    onChange={handleChange}
                    className={`w-full px-4 py-3 border rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${
                      errors.password ? 'border-red-300 bg-red-50' : 'border-gray-300 hover:border-gray-400'
                    }`}
                    placeholder="Enter your password"
                  />
                  {errors.password && (
                    <p className="mt-2 text-sm text-red-600 flex items-center">
                      <span className="mr-1">⚠️</span>
                      {errors.password}
                    </p>
                  )}
                </div>
              </div>

              {errors.submit && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <span className="text-red-400">❌</span>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-red-800">{errors.submit}</p>
                    </div>
                  </div>
                </div>
              )}

              <Button
                type="submit"
                variant="gradient"
                size="lg"
                isLoading={isLoading}
                className="w-full"
              >
                {isLoading ? 'Signing in...' : 'Sign In'}
              </Button>
            </form>

            <div className="mt-8 text-center">
              <p className="text-sm text-gray-600">
                Don't have an account?{' '}
                <Link
                  href="/register"
                  className="font-medium text-blue-600 hover:text-blue-500 transition-colors"
                >
                  Create one here
                </Link>
              </p>
            </div>

            {/* Simple demo info */}
            {!loadingDemoUsers && demoUsers.length > 0 && (
              <Card variant="outlined" className="mt-6 bg-blue-50 border-blue-200">
                <CardContent className="p-4">
                  <div className="text-center">
                    <h4 className="text-sm font-medium text-blue-900 mb-2">
                      🧪 {demoUsers.length} Demo Accounts Available
                    </h4>
                    <p className="text-xs text-blue-700">
                      Select from the dropdown above to auto-fill credentials.
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}
          </CardContent>
        </Card>

        {/* Enhanced Demo Users Display */}
        <DemoUsersDisplay 
          demoUsers={demoUsers}
          onUserSelect={(email, password) => {
            setFormData({ email, password });
            setErrors({});
          }}
        />

        {/* Footer */}
        <div className="text-center mt-8">
          <p className="text-sm text-gray-500">
            Powered by AI Share Platform
          </p>
        </div>
      </div>
    </div>
  );
}