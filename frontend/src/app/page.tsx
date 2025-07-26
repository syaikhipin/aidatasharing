'use client';

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from "@/components/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function Home() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !isLoading && isAuthenticated) {
      router.push('/dashboard');
    }
  }, [mounted, isAuthenticated, isLoading, router]);

  // Show loading during SSR and initial client render
  if (!mounted || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50">
        <div className="flex flex-col items-center space-y-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"></div>
          <p className="text-gray-600 animate-pulse">Loading AI Share Platform...</p>
        </div>
      </div>
    );
  }

  // Don't render content if authenticated (will redirect)
  if (isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50">
        <div className="flex flex-col items-center space-y-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"></div>
          <p className="text-gray-600">Redirecting to dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
        
        <div className="relative container mx-auto px-4 py-16 sm:py-24">
          <div className="text-center animate-fade-in">
            {/* Hero Badge */}
            <div className="inline-flex items-center rounded-full bg-blue-100 px-4 py-2 text-sm font-medium text-blue-700 mb-8">
              <span className="mr-2">🚀</span>
              Powered by MindsDB & AI
            </div>

            {/* Main Heading */}
            <h1 className="text-4xl sm:text-6xl font-bold text-gray-900 mb-6 leading-tight">
              <span className="text-gradient">AI Share Platform</span>
              <br />
              <span className="text-gray-700">Made Simple</span>
            </h1>

            {/* Subtitle */}
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed">
              The most intuitive AI-driven data sharing platform. Create, manage, and deploy 
              machine learning models with unprecedented ease and speed.
            </p>
            
            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
              <Link href="/login">
                <Button variant="gradient" size="lg" className="w-full sm:w-auto">
                  <span className="mr-2">✨</span>
                  Get Started Free
                </Button>
              </Link>
              <Link href="/register">
                <Button variant="outline" size="lg" className="w-full sm:w-auto">
                  <span className="mr-2">👤</span>
                  Create Account
                </Button>
              </Link>
            </div>

            {/* Trust Indicators */}
            <div className="flex flex-wrap justify-center items-center gap-8 text-sm text-gray-500">
              <div className="flex items-center">
                <span className="mr-2">⚡</span>
                Lightning Fast
              </div>
              <div className="flex items-center">
                <span className="mr-2">🔒</span>
                Enterprise Secure
              </div>
              <div className="flex items-center">
                <span className="mr-2">🌐</span>
                Cloud Ready
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Why Choose AI Share Platform?
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Built for modern teams who need powerful AI capabilities without the complexity.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <Card variant="elevated" interactive className="animate-fade-in hover-lift">
              <CardHeader>
                <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <CardTitle>Lightning Fast AI Models</CardTitle>
                <CardDescription>
                  Create and deploy machine learning models in minutes, not hours. 
                  MindsDB's powerful engine handles the complexity.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card variant="elevated" interactive className="animate-fade-in hover-lift" style={{ animationDelay: '0.1s' }}>
              <CardHeader>
                <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-green-600 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <CardTitle>Intuitive Management</CardTitle>
                <CardDescription>
                  Beautiful, modern interface that makes complex data operations feel simple. 
                  No technical expertise required.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card variant="elevated" interactive className="animate-fade-in hover-lift" style={{ animationDelay: '0.2s' }}>
              <CardHeader>
                <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <CardTitle>Enterprise Security</CardTitle>
                <CardDescription>
                  Bank-level security with JWT authentication, role-based access control, 
                  and comprehensive audit logging.
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="py-16 bg-gradient-to-r from-blue-600 to-purple-600">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center text-white">
            <div className="animate-fade-in">
              <div className="text-3xl font-bold mb-2">10x</div>
              <div className="text-blue-100">Faster Deployment</div>
            </div>
            <div className="animate-fade-in" style={{ animationDelay: '0.1s' }}>
              <div className="text-3xl font-bold mb-2">99.9%</div>
              <div className="text-blue-100">Uptime SLA</div>
            </div>
            <div className="animate-fade-in" style={{ animationDelay: '0.2s' }}>
              <div className="text-3xl font-bold mb-2">500+</div>
              <div className="text-blue-100">Data Connectors</div>
            </div>
            <div className="animate-fade-in" style={{ animationDelay: '0.3s' }}>
              <div className="text-3xl font-bold mb-2">24/7</div>
              <div className="text-blue-100">Expert Support</div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-16 bg-gray-50">
        <div className="container mx-auto px-4 text-center">
          <Card variant="elevated" className="max-w-4xl mx-auto">
            <CardContent className="p-12">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Ready to Transform Your Data Workflow?
              </h2>
              <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
                Join thousands of teams who have already revolutionized their AI and data operations 
                with our platform.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link href="/register">
                  <Button variant="gradient" size="lg" className="w-full sm:w-auto">
                    <span className="mr-2">🚀</span>
                    Start Free Trial
                  </Button>
                </Link>
                <Link href="/login">
                  <Button variant="outline" size="lg" className="w-full sm:w-auto">
                    <span className="mr-2">👋</span>
                    Sign In
                  </Button>
                </Link>
              </div>
              <p className="text-sm text-gray-500 mt-4">
                No credit card required • 14-day free trial • Cancel anytime
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-8">
        <div className="container mx-auto px-4 text-center">
          <div className="flex justify-center items-center mb-4">
            <h3 className="text-xl font-bold">AI Share Platform</h3>
          </div>
          <p className="text-gray-400 mb-4">
            Empowering organizations with intelligent data sharing and AI-driven insights.
          </p>
          <div className="text-sm text-gray-500">
            Built with ❤️ using FastAPI, Next.js, and modern AI technologies.
          </div>
        </div>
      </footer>
    </div>
  )
}