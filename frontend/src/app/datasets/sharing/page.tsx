'use client';

import { useState, useEffect } from 'react';
import { Share2, Eye, Users, Globe, Lock, Settings, ExternalLink, Copy, Trash2 } from 'lucide-react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { SharingLevelSelector, SharingLevelBadge } from '@/components/datasets/SharingLevelSelector';
import { datasetsAPI, dataSharingAPI } from '@/lib/api';
import Link from 'next/link';

interface Dataset {
  id: number;
  name: string;
  description?: string;
  type: string;
  sharing_level: 'private' | 'organization' | 'public';
  size_bytes?: number;
  created_at: string;
  public_share_enabled?: boolean;
  share_token?: string;
  share_url?: string;
  view_count?: number;
}

export default function SharingManagementPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <SharingManagementContent />
      </DashboardLayout>
    </ProtectedRoute>
  );
}

function SharingManagementContent() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const showToast = (title: string, description: string, variant: 'default' | 'destructive' = 'default') => {
    // Simple alert for now - can be replaced with proper toast implementation
    if (variant === 'destructive') {
      alert(`Error: ${description}`);
    } else {
      alert(`${title}: ${description}`);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await datasetsAPI.getDatasets();
      setDatasets(response);
    } catch (error: any) {
      console.error('Failed to fetch datasets:', error);
      setError(error.response?.data?.detail || 'Failed to fetch datasets');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSharingLevelChange = async (datasetId: number, newLevel: 'private' | 'organization' | 'public') => {
    try {
      await datasetsAPI.updateDataset(datasetId, { sharing_level: newLevel });
      
      let updatedDataset: any = { sharing_level: newLevel };
      
      // If setting to public, automatically create a share link
      if (newLevel === 'public') {
        try {
          const shareResponse = await dataSharingAPI.createShareLink({
            dataset_id: datasetId,
            enable_chat: true
          });
          
          updatedDataset = {
            ...updatedDataset,
            public_share_enabled: true,
            share_token: shareResponse.share_token,
            share_url: shareResponse.share_url
          };
        } catch (shareError) {
          console.warn('Failed to create share link for public dataset:', shareError);
        }
      } else if (newLevel === 'private') {
        // If setting to private, disable sharing
        try {
          await dataSharingAPI.disableSharing(datasetId);
          updatedDataset = {
            ...updatedDataset,
            public_share_enabled: false,
            share_token: undefined,
            share_url: undefined
          };
        } catch (disableError) {
          console.warn('Failed to disable sharing for private dataset:', disableError);
        }
      }
      
      showToast("Success", `Sharing level updated to ${newLevel}`);
      
      // Update local state
      setDatasets(datasets.map(dataset => 
        dataset.id === datasetId 
          ? { ...dataset, ...updatedDataset }
          : dataset
      ));
    } catch (error: any) {
      console.error('Error updating sharing level:', error);
      showToast("Error", "Failed to update sharing level", "destructive");
    }
  };

  const handleCreateShareLink = async (datasetId: number) => {
    try {
      const response = await dataSharingAPI.createShareLink({
        dataset_id: datasetId,
        enable_chat: true
      });
      
      showToast("Success", "Share link created successfully");
      
      // Update local state
      setDatasets(datasets.map(dataset => 
        dataset.id === datasetId 
          ? { 
              ...dataset, 
              public_share_enabled: true,
              share_token: response.share_token,
              share_url: response.share_url
            }
          : dataset
      ));
    } catch (error: any) {
      console.error('Error creating share link:', error);
      showToast("Error", "Failed to create share link", "destructive");
    }
  };

  const handleDisableSharing = async (datasetId: number) => {
    try {
      await dataSharingAPI.disableSharing(datasetId);
      showToast("Success", "Sharing disabled successfully");
      
      // Update local state
      setDatasets(datasets.map(dataset => 
        dataset.id === datasetId 
          ? { 
              ...dataset, 
              public_share_enabled: false,
              share_token: undefined,
              share_url: undefined
            }
          : dataset
      ));
    } catch (error: any) {
      console.error('Error disabling sharing:', error);
      showToast("Error", "Failed to disable sharing", "destructive");
    }
  };

  const copyShareLink = (shareUrl: string) => {
    const fullUrl = shareUrl.startsWith('http') ? shareUrl : `${window.location.origin}${shareUrl}`;
    navigator.clipboard.writeText(fullUrl);
    showToast("Success", "Share link copied to clipboard");
  };

  const openShareLink = (shareUrl: string) => {
    const fullUrl = shareUrl.startsWith('http') ? shareUrl : `${window.location.origin}${shareUrl}`;
    window.open(fullUrl, '_blank');
  };

  const getStatsForLevel = (level: 'private' | 'organization' | 'public') => {
    return datasets.filter(d => d.sharing_level === level).length;
  };

  const getSharedDatasets = () => {
    return datasets.filter(d => d.public_share_enabled);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
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
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                <Settings className="h-6 w-6 mr-2 text-blue-600" />
                Sharing Management
              </h1>
              <p className="text-gray-600 mt-1 text-sm">
                Manage sharing levels and public share links for your datasets
              </p>
            </div>
            <Link
              href="/datasets"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
            >
              ← Back to Datasets
            </Link>
          </div>
        </div>

        {/* Stats Overview */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="flex items-center justify-center mb-1">
                <Lock className="h-5 w-5 text-gray-600 mr-1" />
                <span className="text-sm font-medium text-gray-500">Private</span>
              </div>
              <div className="text-xl font-bold text-gray-900">{getStatsForLevel('private')}</div>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center mb-1">
                <Users className="h-5 w-5 text-blue-600 mr-1" />
                <span className="text-sm font-medium text-gray-500">Organization</span>
              </div>
              <div className="text-xl font-bold text-gray-900">{getStatsForLevel('organization')}</div>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center mb-1">
                <Globe className="h-5 w-5 text-green-600 mr-1" />
                <span className="text-sm font-medium text-gray-500">Public</span>
              </div>
              <div className="text-xl font-bold text-gray-900">{getStatsForLevel('public')}</div>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center mb-1">
                <Share2 className="h-5 w-5 text-purple-600 mr-1" />
                <span className="text-sm font-medium text-gray-500">Active Shares</span>
              </div>
              <div className="text-xl font-bold text-gray-900">{getSharedDatasets().length}</div>
            </div>
          </div>
        </div>

        {/* Datasets List */}
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="px-4 py-4 sm:px-6 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Datasets ({datasets.length})</h3>
          </div>
          
          {datasets.length === 0 ? (
            <div className="text-center py-12">
              <Share2 className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No datasets found</h3>
              <p className="mt-1 text-sm text-gray-500">
                Upload or connect to a data source to get started.
              </p>
              <div className="mt-6">
                <Link
                  href="/datasets"
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  Go to Datasets
                </Link>
              </div>
            </div>
          ) : (
            <ul className="divide-y divide-gray-200">
              {datasets.map((dataset) => (
                <li key={dataset.id} className="px-4 py-4 sm:px-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-3">
                        <h4 className="text-base font-medium text-gray-900 truncate">{dataset.name}</h4>
                        <SharingLevelBadge level={dataset.sharing_level} />
                      </div>
                      {dataset.description && (
                        <p className="text-gray-600 text-sm mt-1 truncate">
                          {dataset.description}
                        </p>
                      )}
                      <div className="flex items-center space-x-3 text-xs text-gray-500 mt-1">
                        <span>{dataset.type?.toUpperCase()}</span>
                        {dataset.size_bytes && (
                          <span>{formatFileSize(dataset.size_bytes)}</span>
                        )}
                        <span>{new Date(dataset.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-3 ml-4">
                      <SharingLevelSelector
                        currentLevel={dataset.sharing_level}
                        onLevelChange={(level) => handleSharingLevelChange(dataset.id, level)}
                        size="sm"
                      />
                      
                      {dataset.public_share_enabled && dataset.share_url ? (
                        <div className="flex items-center space-x-1">
                          <button
                            onClick={() => copyShareLink(dataset.share_url!)}
                            className="p-1.5 text-gray-400 hover:text-gray-600 transition-colors"
                            title="Copy share link"
                          >
                            <Copy className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => openShareLink(dataset.share_url!)}
                            className="p-1.5 text-gray-400 hover:text-gray-600 transition-colors"
                            title="Open share link"
                          >
                            <ExternalLink className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDisableSharing(dataset.id)}
                            className="p-1.5 text-red-400 hover:text-red-600 transition-colors"
                            title="Disable sharing"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => handleCreateShareLink(dataset.id)}
                          className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors"
                        >
                          Create Link
                        </button>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}