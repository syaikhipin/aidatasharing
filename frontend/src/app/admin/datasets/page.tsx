'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { SharingLevelBadge } from '@/components/datasets/SharingLevelSelector';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { adminAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

interface AdminDataset {
  id: number;
  name: string;
  description?: string;
  type: string;
  sharing_level: string;
  organization_id: number;
  owner_id: number;
  is_active: boolean;
  is_deleted: boolean;
  created_at?: string;
  updated_at?: string;
  deleted_at?: string;
  deleted_by?: number;
  size_bytes?: number;
  allow_download: boolean;
  allow_api_access: boolean;
}

interface AdminDatasetStats {
  total_datasets: number;
  active_datasets: number;
  deleted_datasets: number;
  inactive_datasets: number;
  recent_deletions: number;
  sharing_level_stats: {
    private: number;
    organization: number;
    public: number;
  };
  health_status: {
    deletion_rate: number;
    active_rate: number;
  };
}

export default function AdminDatasetsPage() {
  return (
    <ProtectedRoute requireAdmin>
      <DashboardLayout>
        <AdminDatasetsContent />
      </DashboardLayout>
    </ProtectedRoute>
  );
}

function AdminDatasetsContent() {
  const [datasets, setDatasets] = useState<AdminDataset[]>([]);
  const [stats, setStats] = useState<AdminDatasetStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [showDeleted, setShowDeleted] = useState(false);
  const [showInactive, setShowInactive] = useState(false);

  useEffect(() => {
    fetchData();
  }, [showDeleted, showInactive]);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      console.log('🔍 Fetching admin datasets with params:', {
        include_deleted: showDeleted,
        include_inactive: showInactive,
        limit: 1000
      });
      
      // Fetch datasets with admin controls
      const datasetsResponse = await adminAPI.getAdminDatasets({
        include_deleted: showDeleted,
        include_inactive: showInactive,
        limit: 1000 // Get all datasets for admin view
      });
      
      console.log('📊 Admin datasets response:', datasetsResponse);
      console.log('📄 Datasets array:', datasetsResponse.datasets);
      console.log('📋 Dataset count:', datasetsResponse.datasets?.length || 0);
      
      setDatasets(datasetsResponse.datasets || datasetsResponse || []);
      
      // Fetch admin stats
      const statsResponse = await adminAPI.getAdminDatasetStats();
      console.log('📈 Admin stats response:', statsResponse);
      setStats(statsResponse);
      
    } catch (error: any) {
      console.error('❌ Failed to fetch admin data:', error);
      console.error('❌ Error details:', error.response?.data);
      setError(error.response?.data?.detail || 'Failed to fetch admin data');
      setDatasets([]);
      setStats(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteDataset = async (datasetId: number, datasetName: string, forceDelete: boolean = false) => {
    let title, message, confirmText;
    
    if (forceDelete) {
      title = 'Permanently Delete Dataset';
      message = `⚠️ WARNING: This will PERMANENTLY DELETE the dataset "${datasetName}" and ALL associated data including:\n\n• All access logs and analytics\n• All download records\n• All chat sessions and messages\n• All AI models and predictions\n• All sharing links and accesses\n\nThis action CANNOT be undone and the data will be lost forever!`;
      confirmText = 'Type "DELETE" to confirm permanent deletion:';
    } else {
      title = 'Disable Dataset';
      message = `This will disable the dataset "${datasetName}" and hide it from users.\n\n✅ The dataset can be restored later\n✅ All data and history will be preserved\n✅ No data will be permanently lost\n\nThe dataset will be marked as deleted but can be restored from the admin panel.`;
      confirmText = 'Are you sure you want to disable this dataset?';
    }
    
    if (forceDelete) {
      // For permanent delete, require typing "DELETE"
      const userInput = prompt(`${title}\n\n${message}\n\n${confirmText}`);
      if (userInput !== 'DELETE') {
        if (userInput !== null) {
          alert('Deletion cancelled. You must type "DELETE" exactly to confirm permanent deletion.');
        }
        return;
      }
    } else {
      // For soft delete, just confirm
      if (!confirm(`${title}\n\n${message}\n\n${confirmText}`)) {
        return;
      }
    }

    try {
      await adminAPI.deleteAdminDataset(datasetId, forceDelete);
      await fetchData(); // Refresh data
      
      if (forceDelete) {
        alert(`Dataset "${datasetName}" has been permanently deleted.`);
      } else {
        alert(`Dataset "${datasetName}" has been disabled and can be restored later.`);
      }
    } catch (error: any) {
      console.error('Failed to delete dataset:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to delete dataset';
      alert(`Error: ${errorMessage}`);
    }
  };

  const handleRestoreDataset = async (datasetId: number, datasetName: string) => {
    if (!confirm(`Are you sure you want to restore the dataset "${datasetName}"?`)) {
      return;
    }

    try {
      await adminAPI.restoreDataset(datasetId);
      await fetchData(); // Refresh data
    } catch (error: any) {
      console.error('Failed to restore dataset:', error);
      alert(error.response?.data?.detail || 'Failed to restore dataset');
    }
  };

  // Filter datasets based on search and type
  const filteredDatasets = datasets.filter(dataset => {
    const matchesSearch = dataset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (dataset.description && dataset.description.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesType = filterType === 'all' || dataset.type === filterType;
    return matchesSearch && matchesType;
  });

  const datasetTypes = ['all', ...Array.from(new Set(datasets.map(d => d.type).filter(Boolean)))];

  if (isLoading && datasets.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center space-y-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"></div>
          <p className="text-gray-600">Loading admin datasets...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="py-6 animate-fade-in">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
        {/* Header Section */}
        <div className="mb-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
            <div className="mb-6 lg:mb-0">
              <h1 className="text-3xl font-bold text-gray-900">Admin Dataset Management</h1>
              <p className="text-gray-600 mt-2">
                Manage all datasets across the platform with advanced controls
              </p>
            </div>
            <div className="flex flex-col sm:flex-row gap-3">
              <Link href="/admin">
                <Button variant="outline" size="lg" className="w-full sm:w-auto">
                  <span className="mr-2">←</span>
                  Back to Admin Panel
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Stats Overview */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
            <Card variant="elevated">
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
                      <span className="text-white text-sm">📊</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Total Datasets</p>
                    <p className="text-2xl font-semibold text-gray-900">{stats.total_datasets}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card variant="elevated">
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
                      <span className="text-white text-sm">✅</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Active</p>
                    <p className="text-2xl font-semibold text-gray-900">{stats.active_datasets}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card variant="elevated">
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-red-500 rounded-lg flex items-center justify-center">
                      <span className="text-white text-sm">🗑️</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Deleted</p>
                    <p className="text-2xl font-semibold text-gray-900">{stats.deleted_datasets}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card variant="elevated">
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-yellow-500 rounded-lg flex items-center justify-center">
                      <span className="text-white text-sm">⏸️</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Inactive</p>
                    <p className="text-2xl font-semibold text-gray-900">{stats.inactive_datasets}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card variant="elevated">
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-purple-500 rounded-lg flex items-center justify-center">
                      <span className="text-white text-sm">📈</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Health Score</p>
                    <p className="text-2xl font-semibold text-gray-900">{Math.round(stats.health_status.active_rate)}%</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Datasets Section */}
        <Card variant="elevated">
          <CardHeader>
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
              <div>
                <CardTitle className="text-xl">Dataset Management</CardTitle>
                <CardDescription>
                  View and manage all datasets with advanced filtering options
                </CardDescription>
              </div>
              <div className="flex flex-col sm:flex-row gap-3 mt-4 lg:mt-0">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={showDeleted}
                    onChange={(e) => setShowDeleted(e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">Show Deleted</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={showInactive}
                    onChange={(e) => setShowInactive(e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">Show Inactive</span>
                </label>
              </div>
            </div>
          </CardHeader>
          
          <CardContent>
            {/* Search and Filter */}
            <div className="flex flex-col sm:flex-row gap-4 mb-6">
              <div className="flex-1">
                <input
                  type="text"
                  placeholder="Search datasets by name, description, or owner..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                />
              </div>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="px-4 py-2.5 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 transition-colors hover:border-gray-400"
              >
                {datasetTypes.map(type => (
                  <option key={type} value={type}>
                    {type === 'all' ? '📁 All Types' : `📁 ${type.toUpperCase()}`}
                  </option>
                ))}
              </select>
            </div>

            {error && (
              <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 18.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">Error loading datasets</h3>
                    <div className="mt-2 text-sm text-red-700">
                      <p>{error}</p>
                    </div>
                    <div className="mt-3">
                      <Button
                        onClick={fetchData}
                        variant="outline"
                        size="sm"
                      >
                        Try again
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {filteredDatasets.length === 0 && !error && !isLoading ? (
              <div className="text-center py-12">
                <div className="w-24 h-24 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                  <span className="text-4xl">📊</span>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {searchTerm || filterType !== 'all' ? 'No matching datasets' : 'No datasets found'}
                </h3>
                <p className="text-gray-600 mb-6">
                  {searchTerm || filterType !== 'all' 
                    ? 'Try adjusting your search or filter criteria.'
                    : 'No datasets match the current filter settings.'
                  }
                </p>
              </div>
            ) : filteredDatasets.length > 0 ? (
              <div className="grid gap-4">
                {filteredDatasets.map((dataset) => (
                  <Card key={dataset.id} variant="outlined" interactive className={`hover-lift ${
                    dataset.is_deleted ? 'bg-red-50 border-red-200' : 
                    !dataset.is_active ? 'bg-yellow-50 border-yellow-200' : ''
                  }`}>
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center mb-2">
                            <h3 className="text-lg font-semibold text-gray-900 mr-3">
                              {dataset.name}
                            </h3>
                            <SharingLevelBadge level={(dataset.sharing_level || 'private') as ('private' | 'organization' | 'public')} />
                            {dataset.is_deleted && (
                              <span className="ml-2 px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">
                                Deleted
                              </span>
                            )}
                            {!dataset.is_active && !dataset.is_deleted && (
                              <span className="ml-2 px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">
                                Inactive
                              </span>
                            )}
                          </div>
                          <p className="text-gray-600 mb-3">
                            {dataset.description || 'No description provided'}
                          </p>
                          <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
                            <span className="flex items-center">
                              <span className="mr-1">📁</span>
                              {dataset.type?.toUpperCase() || 'Unknown'}
                            </span>
                            {dataset.size_bytes && (
                              <span className="flex items-center">
                                <span className="mr-1">💾</span>
                                {formatFileSize(dataset.size_bytes)}
                              </span>
                            )}
                            <span className="flex items-center">
                              <span className="mr-1">📅</span>
                              {dataset.created_at ? new Date(dataset.created_at).toLocaleDateString() : 'Unknown'}
                            </span>
                            <span className="flex items-center">
                              <span className="mr-1">🏢</span>
                              Org: {dataset.organization_id}
                            </span>
                            {dataset.deleted_at && (
                              <span className="flex items-center text-red-600">
                                <span className="mr-1">🗑️</span>
                                Deleted: {new Date(dataset.deleted_at).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex flex-col items-end space-y-3 ml-4">
                          <div className="flex items-center space-x-2">
                            {!dataset.is_deleted && (
                              <>
                                <Link href={`/datasets/${dataset.id}`}>
                                  <Button variant="outline" size="sm">
                                    <span className="mr-1">👁️</span>
                                    View
                                  </Button>
                                </Link>
                                <Button 
                                  onClick={() => handleDeleteDataset(dataset.id, dataset.name, false)}
                                  variant="destructive"
                                  size="sm"
                                >
                                  <span className="mr-1">⏸️</span>
                                  Disable
                                </Button>
                              </>
                            )}
                            {dataset.is_deleted && (
                              <>
                                <Button 
                                  onClick={() => handleRestoreDataset(dataset.id, dataset.name)}
                                  variant="secondary"
                                  size="sm"
                                >
                                  <span className="mr-1">↩️</span>
                                  Restore
                                </Button>
                                <Button 
                                  onClick={() => handleDeleteDataset(dataset.id, dataset.name, true)}
                                  variant="destructive"
                                  size="sm"
                                >
                                  <span className="mr-1">💥</span>
                                  Permanent Delete
                                </Button>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : null}

            {isLoading && datasets.length > 0 && (
              <div className="text-center py-4">
                <div className="inline-flex items-center">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-200 border-t-blue-600 mr-2"></div>
                  <span className="text-gray-600">Updating datasets...</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}