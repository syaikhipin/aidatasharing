'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useAuth } from '@/components/auth/AuthProvider';
import { useState, useEffect } from 'react';
import { adminAPI } from '@/lib/api';

export default function AdminPage() {
  return (
    <ProtectedRoute requireAdmin={true}>
      <AdminContent />
    </ProtectedRoute>
  );
}

function AdminContent() {
  const { user, logout } = useAuth();
  const [configs, setConfigs] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [newConfig, setNewConfig] = useState({ key: '', value: '' });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const configs = await adminAPI.getConfigurations();
      setConfigs(configs);
      // For now, we'll set users to an empty array since there's no users endpoint
      setUsers([]);
    } catch (error) {
      console.error('Failed to fetch admin data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newConfig.key || !newConfig.value) return;

    try {
      await adminAPI.createConfiguration({ key: newConfig.key, value: newConfig.value });
      setNewConfig({ key: '', value: '' });
      fetchData(); // Refresh data
    } catch (error) {
      console.error('Failed to create config:', error);
    }
  };

  const handleDeleteConfig = async (configKey: string) => {
    if (!confirm('Are you sure you want to delete this configuration?')) return;

    try {
      await adminAPI.deleteConfiguration(configKey);
      fetchData(); // Refresh data
    } catch (error) {
      console.error('Failed to delete config:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-3xl font-bold text-gray-900">Admin Panel</h1>
              <span className="ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                Administrator
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-700">
                {user?.full_name || user?.email}
              </div>
              <button
                onClick={() => window.location.href = '/dashboard'}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Dashboard
              </button>
              <button
                onClick={logout}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Configuration Management */}
            <div className="bg-white shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                  System Configuration
                </h3>
                
                {/* Add New Config Form */}
                <form onSubmit={handleCreateConfig} className="mb-6 space-y-4">
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Configuration Key
                      </label>
                      <input
                        type="text"
                        value={newConfig.key}
                        onChange={(e) => setNewConfig({ ...newConfig, key: e.target.value })}
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500"
                        placeholder="e.g., GOOGLE_API_KEY"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Value
                      </label>
                      <input
                        type="text"
                        value={newConfig.value}
                        onChange={(e) => setNewConfig({ ...newConfig, value: e.target.value })}
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500"
                        placeholder="Configuration value"
                      />
                    </div>
                  </div>
                  <button
                    type="submit"
                    className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                  >
                    Add Configuration
                  </button>
                </form>

                {/* Configurations List */}
                <div className="space-y-3">
                  {configs.length === 0 ? (
                    <p className="text-gray-500 text-sm">No configurations found.</p>
                  ) : (
                    configs.map((config) => (
                      <div
                        key={config.key}
                        className="flex items-center justify-between p-3 border border-gray-200 rounded-md"
                      >
                        <div className="flex-1">
                          <div className="font-medium text-sm text-gray-900">
                            {config.key}
                          </div>
                          <div className="text-sm text-gray-500 truncate max-w-xs">
                            {config.value && config.value.length > 30 
                              ? `${config.value.substring(0, 30)}...` 
                              : config.value || 'No value'
                            }
                          </div>
                        </div>
                        <button
                          onClick={() => handleDeleteConfig(config.key)}
                          className="text-red-600 hover:text-red-900 text-sm font-medium"
                        >
                          Delete
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* User Management */}
            <div className="bg-white shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                  User Management
                </h3>
                
                <div className="space-y-3">
                  {users.length === 0 ? (
                    <p className="text-gray-500 text-sm">No users found.</p>
                  ) : (
                    users.map((user) => (
                      <div
                        key={user.id}
                        className="flex items-center justify-between p-3 border border-gray-200 rounded-md"
                      >
                        <div className="flex-1">
                          <div className="font-medium text-sm text-gray-900">
                            {user.full_name || user.email}
                          </div>
                          <div className="text-sm text-gray-500">
                            {user.email}
                          </div>
                          <div className="flex space-x-2 mt-1">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                              user.is_active 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {user.is_active ? 'Active' : 'Inactive'}
                            </span>
                            {user.is_superuser && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                                Admin
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* MindsDB Status */}
            <div className="bg-white shadow rounded-lg lg:col-span-2">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                  MindsDB Connection Status
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center p-4 border border-gray-200 rounded-md">
                    <div className="text-2xl font-bold text-green-600">●</div>
                    <div className="text-sm font-medium text-gray-900">Connection</div>
                    <div className="text-xs text-gray-500">Active</div>
                  </div>
                  
                  <div className="text-center p-4 border border-gray-200 rounded-md">
                    <div className="text-2xl font-bold text-blue-600">0</div>
                    <div className="text-sm font-medium text-gray-900">Active Models</div>
                    <div className="text-xs text-gray-500">Ready to create</div>
                  </div>
                  
                  <div className="text-center p-4 border border-gray-200 rounded-md">
                    <div className="text-2xl font-bold text-purple-600">0</div>
                    <div className="text-sm font-medium text-gray-900">Data Sources</div>
                    <div className="text-xs text-gray-500">Waiting to connect</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
} 