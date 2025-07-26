'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useState, useEffect } from 'react';
import { datasetsAPI, adminAPI } from '@/lib/api';
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
  const [environmentVariables, setEnvironmentVariables] = useState<any>(null);
  const [showEnvironmentModal, setShowEnvironmentModal] = useState(false);

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

      // Fetch environment variables
      try {
        const envVars = await adminAPI.getEnvironmentVariables();
        setEnvironmentVariables(envVars);
      } catch (error) {
        console.error('Failed to fetch environment variables:', error);
        setEnvironmentVariables(null);
      }

      // Fetch admin stats
      try {
        const adminStats = await adminAPI.getAdminStats();
        setStats(adminStats);
      } catch (error) {
        console.error('Failed to fetch admin stats:', error);
        // Fallback to mock stats
        const mockStats: AdminStats = {
          totalUsers: 0,
          activeUsers: 0,
          totalDatasets: datasets?.length || 0,
          totalOrganizations: 0,
          systemHealth: {
            status: 'critical',
            uptime: 'Unknown',
            lastCheck: new Date().toISOString()
          }
        };
        setStats(mockStats);
      }
      
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
              
              <Link href="/admin/datasets">
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

          {/* System Configuration - Unified */}
          <Card variant="elevated">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>System Configuration</CardTitle>
                  <CardDescription>
                    Manage system settings, API keys, and environment variables
                  </CardDescription>
                </div>
                <Button variant="outline" size="sm" onClick={handleCreateConfiguration}>
                  <span className="mr-1">➕</span>
                  Add Config
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
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

                {/* Environment Variables Toggle */}
                <div className="border-t pt-4">
                  <Button
                    variant="outline"
                    className="w-full justify-start"
                    onClick={() => setShowEnvironmentModal(!showEnvironmentModal)}
                  >
                    <span className="mr-2">⚙️</span>
                    {showEnvironmentModal ? 'Hide' : 'Show'} Environment Variables
                  </Button>
                </div>

                {/* Configuration List */}
                {configurations.length > 0 ? (
                  <div className="space-y-2 border-t pt-4">
                    <h4 className="font-medium text-gray-900">System Configurations</h4>
                    {configurations.slice(0, 4).map((config, index) => (
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
                    {configurations.length > 4 && (
                      <p className="text-xs text-gray-500">
                        +{configurations.length - 4} more configurations
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-4 border-t">
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

        {/* Environment Variables Section - Expandable */}
        {showEnvironmentModal && environmentVariables && (
          <Card variant="elevated" className="mt-8">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Environment Variables</CardTitle>
                  <CardDescription>
                    Manage system environment variables by category
                  </CardDescription>
                </div>
                <Button variant="outline" size="sm" onClick={() => setShowEnvironmentModal(false)}>
                  <span className="mr-1">✕</span>
                  Hide
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <EnvironmentVariablesSection 
                environmentVariables={environmentVariables}
                onUpdate={fetchAdminData}
              />
            </CardContent>
          </Card>
        )}

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

      {/* Environment Management Modal */}
      {showEnvironmentModal && (
        <EnvironmentVariablesModal 
          environmentVariables={environmentVariables}
          onClose={() => setShowEnvironmentModal(false)}
          onUpdate={fetchAdminData}
        />
      )}
    </div>
  );
}

// Environment Variables Section Component
function EnvironmentVariablesSection({ 
  environmentVariables, 
  onUpdate 
}: { 
  environmentVariables: any; 
  onUpdate: () => void; 
}) {
  const [activeCategory, setActiveCategory] = useState('api');
  const [editingVar, setEditingVar] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSaveVariable = async (key: string, value: string) => {
    try {
      setSaving(true);
      await adminAPI.updateEnvironmentVariable(key, value);
      setEditingVar(null);
      setEditValue('');
      onUpdate();
      alert('Environment variable updated successfully!');
    } catch (error) {
      console.error('Failed to update environment variable:', error);
      alert('Failed to update environment variable. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const categories = environmentVariables.categories || {};

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      {/* Category Sidebar */}
      <div className="space-y-2">
        <h3 className="font-semibold text-gray-700 mb-3">Categories</h3>
        {Object.entries(categories).map(([key, category]: [string, any]) => (
          <button
            key={key}
            onClick={() => setActiveCategory(key)}
            className={`w-full text-left p-2 rounded-md text-sm transition-colors ${
              activeCategory === key 
                ? 'bg-blue-100 text-blue-700 border border-blue-300' 
                : 'hover:bg-gray-100'
            }`}
          >
            {category.name}
          </button>
        ))}
      </div>

      {/* Variables Content */}
      <div className="md:col-span-3">
        {categories[activeCategory] && (
          <div>
            <h3 className="text-lg font-semibold mb-2">
              {categories[activeCategory].name}
            </h3>
            <p className="text-gray-600 text-sm mb-4">
              {categories[activeCategory].description}
            </p>

            <div className="space-y-3">
              {categories[activeCategory].variables.map((variable: any) => (
                <div key={variable.key} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h4 className="font-medium text-gray-900">{variable.key}</h4>
                      <p className="text-xs text-gray-500">{variable.description}</p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setEditingVar(variable.key);
                        setEditValue(variable.value);
                      }}
                      disabled={editingVar === variable.key}
                    >
                      {editingVar === variable.key ? 'Editing...' : 'Edit'}
                    </Button>
                  </div>

                  {editingVar === variable.key ? (
                    <div className="mt-3 space-y-2">
                      <input
                        type={variable.key.toLowerCase().includes('password') || variable.key.toLowerCase().includes('secret') ? 'password' : 'text'}
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        className="w-full p-2 border border-gray-300 rounded-md text-sm"
                        placeholder="Enter value..."
                      />
                      <div className="flex space-x-2">
                        <Button
                          size="sm"
                          onClick={() => handleSaveVariable(variable.key, editValue)}
                          disabled={saving}
                        >
                          {saving ? 'Saving...' : 'Save'}
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setEditingVar(null);
                            setEditValue('');
                          }}
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="mt-2">
                      <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                        {variable.key.toLowerCase().includes('password') || variable.key.toLowerCase().includes('secret') || variable.key.toLowerCase().includes('key')
                          ? variable.value ? '••••••••' : 'Not set'
                          : variable.value || 'Not set'
                        }
                      </code>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Environment Variables Modal Component
function EnvironmentVariablesModal({ 
  environmentVariables, 
  onClose, 
  onUpdate 
}: { 
  environmentVariables: any; 
  onClose: () => void; 
  onUpdate: () => void; 
}) {
  const [activeCategory, setActiveCategory] = useState<string>('');
  const [editingVar, setEditingVar] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  const [saving, setSaving] = useState(false);

  // Initialize active category when modal opens
  useEffect(() => {
    if (environmentVariables?.variables && environmentVariables.variables.length > 0) {
      const categories = [...new Set(environmentVariables.variables.map((v: any) => v.category || 'GENERAL'))];
      setActiveCategory(categories[0]);
    }
  }, [environmentVariables]);

  const handleSaveVariable = async (name: string, value: string) => {
    try {
      setSaving(true);
      // Call the API to update environment variable
      await adminAPI.updateEnvironmentVariable(name, value);
      setEditingVar(null);
      setEditValue('');
      onUpdate();
      alert('Environment variable updated successfully!');
    } catch (error) {
      console.error('Failed to update environment variable:', error);
      alert('Failed to update environment variable. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  // Group variables by category
  const groupedVariables = environmentVariables?.variables?.reduce((acc: any, variable: any) => {
    const category = variable.category || 'GENERAL';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(variable);
    return acc;
  }, {}) || {};

  const categories = Object.keys(groupedVariables);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl h-5/6 flex flex-col">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Environment Variables</h2>
            <p className="text-gray-600 text-sm mt-1">
              Manage system environment variables by category
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={onClose}>
            <span className="mr-1">✕</span>
            Close
          </Button>
        </div>

        {/* Modal Content */}
        <div className="flex flex-1 overflow-hidden">
          {/* Category Sidebar */}
          <div className="w-64 border-r bg-gray-50 p-4 overflow-y-auto">
            <h3 className="font-semibold text-gray-700 mb-3">Categories</h3>
            <div className="space-y-2">
              {categories.map((category) => (
                <button
                  key={category}
                  onClick={() => setActiveCategory(category)}
                  className={`w-full text-left p-3 rounded-md text-sm transition-colors ${
                    activeCategory === category 
                      ? 'bg-blue-100 text-blue-700 border border-blue-300' 
                      : 'hover:bg-gray-100'
                  }`}
                >
                  <div className="font-medium">{category}</div>
                  <div className="text-xs text-gray-500">
                    {groupedVariables[category]?.length || 0} variables
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Variables Content */}
          <div className="flex-1 p-6 overflow-y-auto">
            {activeCategory && groupedVariables[activeCategory] && (
              <div>
                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-2">{activeCategory}</h3>
                  <p className="text-gray-600 text-sm">
                    Manage environment variables for the {activeCategory.toLowerCase()} category
                  </p>
                </div>

                <div className="space-y-4">
                  {groupedVariables[activeCategory].map((variable: any) => (
                    <div key={variable.name} className="border border-gray-200 rounded-lg p-4 bg-white">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900 mb-1">{variable.name}</h4>
                          <p className="text-xs text-gray-500 mb-2">{variable.description || 'No description available'}</p>
                          <div className="flex items-center space-x-4 text-xs">
                            <span className={`px-2 py-1 rounded-full ${
                              variable.is_set ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                            }`}>
                              {variable.is_set ? 'Set' : 'Not Set'}
                            </span>
                            <span className={`px-2 py-1 rounded-full ${
                              variable.is_managed ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'
                            }`}>
                              {variable.is_managed ? 'Managed' : 'Unmanaged'}
                            </span>
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setEditingVar(variable.name);
                            setEditValue(variable.value || '');
                          }}
                          disabled={editingVar === variable.name}
                        >
                          {editingVar === variable.name ? 'Editing...' : 'Edit'}
                        </Button>
                      </div>

                      {editingVar === variable.name ? (
                        <div className="space-y-3">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Value
                            </label>
                            <input
                              type={variable.name.toLowerCase().includes('password') || 
                                    variable.name.toLowerCase().includes('secret') ||
                                    variable.name.toLowerCase().includes('key') ? 'password' : 'text'}
                              value={editValue}
                              onChange={(e) => setEditValue(e.target.value)}
                              className="w-full p-3 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                              placeholder="Enter value..."
                            />
                          </div>
                          <div className="flex space-x-2">
                            <Button
                              size="sm"
                              onClick={() => handleSaveVariable(variable.name, editValue)}
                              disabled={saving}
                            >
                              {saving ? 'Saving...' : 'Save'}
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setEditingVar(null);
                                setEditValue('');
                              }}
                            >
                              Cancel
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <div className="mt-3">
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Current Value
                          </label>
                          <code className="block text-sm bg-gray-100 px-3 py-2 rounded border">
                            {variable.name.toLowerCase().includes('password') || 
                             variable.name.toLowerCase().includes('secret') || 
                             variable.name.toLowerCase().includes('key')
                              ? (variable.value ? '••••••••' : 'Not set')
                              : (variable.value || 'Not set')
                            }
                          </code>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {!activeCategory && (
              <div className="text-center py-12">
                <p className="text-gray-500">Select a category to view environment variables</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}