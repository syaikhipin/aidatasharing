'use client';

import { useAuth } from '@/components/auth/AuthProvider';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

export default function OrganizationsPage() {
  const { user } = useAuth();

  return (
    <ProtectedRoute>
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-6">
              Organization Details
            </h1>
            
            {user?.organization_name ? (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">
                      Organization Information
                    </h2>
                    <div className="space-y-3">
                      <div>
                        <label className="text-sm font-medium text-gray-500">Organization Name</label>
                        <p className="text-gray-900">{user.organization_name}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-500">Your Role</label>
                        <p className="text-gray-900 capitalize">{user.role}</p>
                      </div>
                      {user.department_name && (
                        <div>
                          <label className="text-sm font-medium text-gray-500">Department</label>
                          <p className="text-gray-900">{user.department_name}</p>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">
                      Your Access
                    </h2>
                    <div className="space-y-3">
                      <div>
                        <label className="text-sm font-medium text-gray-500">Status</label>
                        <p className="text-green-600 font-medium">Active Member</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-500">Member Since</label>
                        <p className="text-gray-900">
                          {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="border-t border-gray-200 pt-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">
                    Quick Actions
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <a
                      href="/datasets"
                      className="block p-4 bg-blue-50 rounded-lg border border-blue-200 hover:bg-blue-100 transition-colors"
                    >
                      <h3 className="font-medium text-blue-900">View Datasets</h3>
                      <p className="text-sm text-blue-700">Browse organization datasets</p>
                    </a>
                    <a
                      href="/models"
                      className="block p-4 bg-green-50 rounded-lg border border-green-200 hover:bg-green-100 transition-colors"
                    >
                      <h3 className="font-medium text-green-900">AI Models</h3>
                      <p className="text-sm text-green-700">Manage ML models</p>
                    </a>
                    <a
                      href="/analytics"
                      className="block p-4 bg-purple-50 rounded-lg border border-purple-200 hover:bg-purple-100 transition-colors"
                    >
                      <h3 className="font-medium text-purple-900">Analytics</h3>
                      <p className="text-sm text-purple-700">View usage analytics</p>
                    </a>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                  <h2 className="text-lg font-semibold text-yellow-800 mb-2">
                    No Organization
                  </h2>
                  <p className="text-yellow-700 mb-4">
                    You are not currently a member of any organization. Join or create an organization to access shared data and collaborate with others.
                  </p>
                  <div className="space-x-4">
                    <a
                      href="/register"
                      className="inline-flex items-center px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 transition-colors"
                    >
                      Join Organization
                    </a>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
} 