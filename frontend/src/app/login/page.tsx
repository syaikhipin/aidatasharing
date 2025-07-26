'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { authAPI } from '@/lib/api';
import { useAuth } from '@/components/auth/AuthProvider';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function LoginPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const { login } = useAuth();

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

  const fillDemoCredentials = (userType: 'admin' | 'user' | 'test') => {
    if (userType === 'admin') {
      setFormData({
        email: 'admin@example.com',
        password: 'admin123'
      });
    } else if (userType === 'user') {
      setFormData({
        email: 'testuser@demo.com',
        password: 'testpassword123'
      });
    } else {
      setFormData({
        email: 'test@mailinator.com',
        password: 'test123'
      });
    }
    setErrors({});
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

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white text-gray-500">or</span>
                </div>
              </div>

              <div className="space-y-3">
                <Button
                  type="button"
                  variant="outline"
                  size="lg"
                  onClick={() => fillDemoCredentials('admin')}
                  className="w-full"
                >
                  <span className="mr-2">👑</span>
                  Login as Admin
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  size="lg"
                  onClick={() => fillDemoCredentials('user')}
                  className="w-full"
                >
                  <span className="mr-2">👤</span>
                  Login as Demo User
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  size="lg"
                  onClick={() => fillDemoCredentials('test')}
                  className="w-full"
                >
                  <span className="mr-2">🧪</span>
                  Login as Test User
                </Button>
              </div>
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

            {/* Demo info card */}
            <Card variant="outlined" className="mt-6 bg-blue-50 border-blue-200">
              <CardContent className="p-4">
                <div className="text-center">
                  <h4 className="text-sm font-medium text-blue-900 mb-3">
                    🚀 Demo Accounts
                  </h4>
                  <div className="grid grid-cols-1 gap-3 text-xs text-blue-700">
                    <div className="bg-white rounded-lg p-3 border border-blue-200">
                      <p className="font-medium text-blue-900 mb-1">👑 Admin Account</p>
                      <p><strong>Email:</strong> admin@example.com</p>
                      <p><strong>Password:</strong> admin123</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-blue-200">
                      <p className="font-medium text-blue-900 mb-1">👤 Demo User</p>
                      <p><strong>Email:</strong> testuser@demo.com</p>
                      <p><strong>Password:</strong> testpassword123</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-blue-200">
                      <p className="font-medium text-blue-900 mb-1">🧪 Test User</p>
                      <p><strong>Email:</strong> test@mailinator.com</p>
                      <p><strong>Password:</strong> test123</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </CardContent>
        </Card>

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