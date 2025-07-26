'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/components/auth/AuthProvider';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { organizationsAPI } from '@/lib/api';

export default function OrganizationDashboard() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <OrganizationDashboardContent />
      </DashboardLayout>
    </ProtectedRoute>
  );
}

function OrganizationDashboardContent() {
  const { user } = useAuth();
  const [organization, setOrganization] = useState<any>(null);
  const [members, setMembers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    
    const fetchData = async () => {
      if (!user?.organization_id) {
        if (isMounted) {
          setLoading(false);
        }
        return;
      }
      
      try {
        if (isMounted) {
          setLoading(true);
        }
        
        const [orgData, membersData] = await Promise.all([
          organizationsAPI.getMy(),
          organizationsAPI.getMembers(user.organization_id),
        ]);
        
        if (isMounted) {
          setOrganization(orgData);
          setMembers(membersData);
          setError(null);
        }
      } catch (err) {
        console.error('Failed to fetch organization data:', err);
        if (isMounted) {
          setError('Failed to load organization data');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchData();
    
    return () => {
      isMounted = false;
    };
  }, [user?.organization_id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center space-y-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"></div>
          <p className="text-gray-600">Loading organization data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h1 className="text-xl font-bold text-red-900 mb-2">Error</h1>
          <p className="text-red-700">{error}</p>
        </div>
      </div>
    );
  }

  if (!organization) {
    return (
      <div className="p-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <h1 className="text-xl font-bold text-yellow-900 mb-2">No Organization</h1>
          <p className="text-yellow-700">You are not part of any organization</p>
        </div>
      </div>
    );
  }

  return (
    <div className="py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">{organization.name}</h1>
          <p className="text-gray-600 mt-2">{organization.description}</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <div className="text-2xl font-bold text-blue-600">{members.length}</div>
                <div className="text-xs text-gray-600">Members</div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div className="ml-4">
                <div className="text-2xl font-bold text-green-600">0</div>
                <div className="text-xs text-gray-600">Datasets</div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div className="ml-4">
                <div className="text-2xl font-bold text-purple-600">Active</div>
                <div className="text-xs text-gray-600">Status</div>
              </div>
            </div>
          </div>
        </div>

        {/* Organization Details */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Organization Info */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Organization Details</h2>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-500">Type</label>
                <p className="text-gray-900 capitalize">{organization.type.replace('_', ' ')}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Sharing Level</label>
                <p className="text-gray-900 capitalize">{organization.default_sharing_level}</p>
              </div>
              {organization.website && (
                <div>
                  <label className="text-sm font-medium text-gray-500">Website</label>
                  <p className="text-blue-600">
                    <a href={organization.website} target="_blank" rel="noopener noreferrer">
                      {organization.website}
                    </a>
                  </p>
                </div>
              )}
              {organization.contact_email && (
                <div>
                  <label className="text-sm font-medium text-gray-500">Contact Email</label>
                  <p className="text-gray-900">{organization.contact_email}</p>
                </div>
              )}
            </div>
          </div>

          {/* Members List */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Members ({members.length})</h2>
            <div className="space-y-3">
              {members.map((member) => (
                <div key={member.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <div className="font-medium text-gray-900">{member.full_name || member.email}</div>
                    <div className="text-sm text-gray-500">{member.email}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900 capitalize">{member.role}</div>
                    <div className={`text-xs ${member.is_active ? 'text-green-600' : 'text-red-600'}`}>
                      {member.is_active ? 'Active' : 'Inactive'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}