'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useState, useEffect } from 'react';
import { datasetsAPI, organizationsAPI, adminAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import Link from 'next/link';

interface AdminStats {
  totalUsers: number;
  activeUsers: number;
  totalDatasets: number;
  totalOrganizations: number;
  systemHealth: {
    status: 'healthy' | 'warning' | 'critical';
    uptime: string;
    lastCheck: string;
  };
}

export default function AdminPanel() {
  return (
    <ProtectedRoute requireAdmin>
      <DashboardLayout>
        <AdminContent />
      </DashboardLayout>
    </ProtectedRoute>
  );
}

function AdminContent() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [configurations, setConfigurations] = useState<any[]>([]);
  const [googleApiKeyStatus, setGoogleApiKeyStatus] = useState<any>(null);

  useEffect(() => {
    fetchAdminData();
  }, []);

  const fetchAdminData = async () => {
    try {
      setLoading(true);
      
      // Fetch datasets count
      const datasets = await datasetsAPI.getDatasets();
      
      // Fetch configurations
      try {
        const configs = await adminAPI.getConfigurations();
        setConfigurations(configs || []);
      } catch (error) {
        console.error('Failed to fetch configurations:', error);
        setConfigurations([]);
      }

      // Fetch Google API key status
      try {
        const apiKeyStatus = await adminAPI.getGoogleApiKeyStatus();
        setGoogleApiKeyStatus(apiKeyStatus);
      } catch (error) {
        console.error('Failed to fetch Google API key status:', error);
        setGoogleApiKeyStatus({ configured: false });
      }

      // Mock admin stats (these would come from real admin endpoints)
      const mockStats: AdminStats = {
        totalUsers: 0, // Would come from users API
        activeUsers: 0, // Would come from analytics API
        totalDatasets: datasets?.length || 0,
        totalOrganizations: 0, // Would come from organizations API
        systemHealth: {
          status: 'healthy',
          uptime: '99.9%',
          lastCheck: new Date().toISOString()
        }
      };
      
      setStats(mockStats);
      
    } catch (error) {
      console.error('Error fetching admin data:', error);
      // Set fallback data
      setStats({
        totalUsers: 0,
        activeUsers: 0,
        totalDatasets: 0,
        totalOrganizations: 0,
        systemHealth: {
          status: 'critical',
          uptime: 'Unknown',
          lastCheck: new Date().toISOString()
        }
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSetGoogleApiKey = async () => {
    const apiKey = prompt('Enter Google API Key:');
    if (apiKey) {
      try {
        await adminAPI.setGoogleApiKey(apiKey);
        alert('Google API Key set successfully!');
        // Refresh status
        const status = await adminAPI.getGoogleApiKeyStatus();
        setGoogleApiKeyStatus(status);
      } catch (error) {
        console.error('Failed to set Google API key:', error);
        alert('Failed to set Google API key. Please try again.');
      }
    }
  };

  const handleCreateConfiguration = async () => {
    const key = prompt('Enter configuration key:');
    if (key) {
      const value = prompt('Enter configuration value:');
      const description = prompt('Enter description (optional):');
      
      try {
        await adminAPI.createConfiguration({
          key,
          value: value || undefined,
          description: description || undefined
        });
        alert('Configuration created successfully!');
        fetchAdminData(); // Refresh data
      } catch (error) {
        console.error('Failed to create configuration:', error);
        alert('Failed to create configuration. Please try again.');
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center space-y-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"></div>
          <p className="text-gray-600">Loading admin panel...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="py-6 animate-fade-in">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Admin Panel</h1>
          <p className="text-gray-600 mt-2">
            Manage system settings, users, and monitor platform health
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card variant="elevated">
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
                    <span className="text-white text-sm">👥</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Total Users</p>
                  <p className="text-2xl font-semibold text-gray-900">{stats?.totalUsers || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card variant="elevated">
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
                    <span className="text-white text-sm">📊</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Total Datasets</p>
                  <p className="text-2xl font-semibold text-gray-900">{stats?.totalDatasets || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card variant="elevated">
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-purple-500 rounded-lg flex items-center justify-center">
                    <span className="text-white text-sm">🏢</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Organizations</p>
                  <p className="text-2xl font-semibold text-gray-900">{stats?.totalOrganizations || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card variant="elevated">
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    stats?.systemHealth.status === 'healthy' ? 'bg-green-500' :
                    stats?.systemHealth.status === 'warning' ? 'bg-yellow-500' :
                    'bg-red-500'
                  }`}>
                    <span className="text-white text-sm">⚡</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">System Health</p>
                  <p className={`text-2xl font-semibold ${
                    stats?.systemHealth.status === 'healthy' ? 'text-green-600' :
                    stats?.systemHealth.status === 'warning' ? 'text-yellow-600' :
                    'text-red-600'
                  }`}>
                    {stats?.systemHealth.status || 'Unknown'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Quick Actions */}
          <Card variant="elevated">
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
              <CardDescription>
                Common administrative tasks
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Link href="/admin/organizations">
                <Button variant="outline" className="w-full justify-start">
                  <span className="mr-2">🏢</span>
                  Manage Organizations
                </Button>
              </Link>
              
              <Link href="/data-access">
                <Button variant="outline" className="w-full justify-start">
                  <span className="mr-2">🔐</span>
                  Data Access Requests
                </Button>
              </Link>
              
              <Link href="/datasets">
                <Button variant="outline" className="w-full justify-start">
                  <span className="mr-2">📊</span>
                  Manage Datasets
                </Button>
              </Link>
              
              <Link href="/analytics">
                <Button variant="outline" className="w-full justify-start">
                  <span className="mr-2">📈</span>
                  View Analytics
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* System Configuration */}
          <Card variant="elevated">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>System Configuration</CardTitle>
                  <CardDescription>
                    Manage system settings and API keys
                  </CardDescription>
                </div>
                <Button variant="outline" size="sm" onClick={handleCreateConfiguration}>
                  <span className="mr-1">➕</span>
                  Add Config
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Google API Key Status */}
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">Google API Key</p>
                    <p className="text-sm text-gray-600">
                      {googleApiKeyStatus?.configured ? 'Configured' : 'Not configured'}
                    </p>
                  </div>
                  <Button 
                    variant={googleApiKeyStatus?.configured ? "secondary" : "gradient"}
                    size="sm"
                    onClick={handleSetGoogleApiKey}
                  >
                    {googleApiKeyStatus?.configured ? 'Update' : 'Set Key'}
                  </Button>
                </div>

                {/* Configuration List */}
                {configurations.length > 0 ? (
                  <div className="space-y-2">
                    <h4 className="font-medium text-gray-900">Configurations</h4>
                    {configurations.slice(0, 5).map((config, index) => (
                      <div key={index} className="flex items-center justify-between p-2 border border-gray-200 rounded">
                        <div>
                          <p className="text-sm font-medium text-gray-900">{config.key}</p>
                          <p className="text-xs text-gray-600">{config.description || 'No description'}</p>
                        </div>
                        <span className="text-xs text-gray-500">
                          {config.value ? '✓' : '✗'}
                        </span>
                      </div>
                    ))}
                    {configurations.length > 5 && (
                      <p className="text-xs text-gray-500">
                        +{configurations.length - 5} more configurations
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-4">
                    <p className="text-sm text-gray-600">No configurations found</p>
                    <Button variant="outline" size="sm" className="mt-2" onClick={handleCreateConfiguration}>
                      Create First Configuration
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* System Status */}
        <Card variant="elevated" className="mt-8">
          <CardHeader>
            <CardTitle>System Status</CardTitle>
            <CardDescription>
              Current system health and performance metrics
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="w-16 h-16 mx-auto mb-3 bg-green-100 rounded-full flex items-center justify-center">
                  <span className="text-2xl">🚀</span>
                </div>
                <p className="text-sm text-gray-500">Platform Status</p>
                <p className="text-lg font-semibold text-green-600">Online</p>
              </div>
              
              <div className="text-center">
                <div className="w-16 h-16 mx-auto mb-3 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-2xl">⏱️</span>
                </div>
                <p className="text-sm text-gray-500">Uptime</p>
                <p className="text-lg font-semibold text-gray-900">{stats?.systemHealth.uptime}</p>
              </div>
              
              <div className="text-center">
                <div className="w-16 h-16 mx-auto mb-3 bg-purple-100 rounded-full flex items-center justify-center">
                  <span className="text-2xl">🔄</span>
                </div>
                <p className="text-sm text-gray-500">Last Check</p>
                <p className="text-lg font-semibold text-gray-900">
                  {stats?.systemHealth.lastCheck ? new Date(stats.systemHealth.lastCheck).toLocaleTimeString() : 'Unknown'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Information Notice */}
        <Card variant="outlined" className="mt-8 bg-blue-50 border-blue-200">
          <CardContent className="p-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <span className="text-blue-500 text-xl">ℹ️</span>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-blue-800">
                  Admin Panel Information
                </h3>
                <div className="mt-2 text-sm text-blue-700">
                  <p>
                    This admin panel provides basic system management capabilities. 
                    Additional features like user management, detailed analytics, and advanced 
                    system monitoring will be available when the corresponding backend endpoints are implemented.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}