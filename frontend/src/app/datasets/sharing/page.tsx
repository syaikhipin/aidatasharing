'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { 
  Share2, 
  Users, 
  Globe, 
  Lock, 
  Settings, 
  ExternalLink, 
  Copy, 
  Trash2,
  Plus,
  Database,
  Shield,
  ChevronDown
} from 'lucide-react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { SharingLevelSelector, SharingLevelBadge } from '@/components/datasets/SharingLevelSelector';
import { datasetsAPI, dataSharingAPI } from '@/lib/api';

import AccessInstructions from '@/components/shared/AccessInstructions';
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
  share_expires_at?: string;
  view_count?: number;
}


export default function DatasetSharingPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <DatasetSharingContent />
      </DashboardLayout>
    </ProtectedRoute>
  );
}

function DatasetSharingContent() {
  // State for datasets only
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  
  // UI state
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };


  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Fetch datasets only
      const datasetsResponse = await datasetsAPI.getDatasets();
      setDatasets(datasetsResponse);
      
    } catch (error: any) {
      console.error('Failed to fetch datasets:', error);
      setError(error.response?.data?.detail || 'Failed to fetch datasets');
    } finally {
      setIsLoading(false);
    }
  };

  // Dataset sharing handlers
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
      
      // Refresh datasets
      fetchDatasets();
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
      
      // Only refresh proxy connectors for datasets that need them (API, database connectors)
      const dataset = datasets.find(d => d.id === datasetId);
      const needsProxyConnector = dataset && ['api', 'database', 'mysql', 'postgresql', 'mongodb'].includes(dataset.type?.toLowerCase());
      
      if (needsProxyConnector) {
        try {
          const refreshResponse = await fetch('/api/data-sharing/refresh-proxy-connectors', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
              'Content-Type': 'application/json'
            }
          });
          
          if (refreshResponse.ok) {
            const refreshData = await refreshResponse.json();
            console.log('Proxy connectors refreshed:', refreshData);
            
            // Show proxy access information
            const proxyUrl = `http://localhost:10103/api/${encodeURIComponent(dataset.name)}?token=${response.share_token}`;
            console.log('Proxy URL for dataset:', proxyUrl);
            
            showToast("Success", `Share link and proxy connector created! Proxy URL: ${proxyUrl}`);
          } else {
            showToast("Warning", "Share link created but proxy connector refresh failed");
          }
          
        } catch (proxyError) {
          console.warn('Failed to refresh proxy connectors:', proxyError);
          showToast("Warning", "Share link created but proxy connector refresh failed");
        }
      } else {
        // For uploaded files (images, CSVs, etc.), just show success without proxy info
        showToast("Success", "Share link created successfully! Users can download and access the shared file.");
      }
      
      // Refresh datasets to show updated share info
      fetchDatasets();
    } catch (error: any) {
      console.error('Error creating share link:', error);
      showToast("Error", "Failed to create share link", "destructive");
    }
  };

  const handleDisableSharing = async (datasetId: number) => {
    try {
      await dataSharingAPI.disableSharing(datasetId);
      showToast("Success", "Sharing disabled successfully");
      
      // Refresh datasets to show updated share info
      fetchDatasets();
    } catch (error: any) {
      console.error('Error disabling sharing:', error);
      showToast("Error", "Failed to disable sharing", "destructive");
    }
  };


  // Utility functions
  const copyShareLink = (shareUrl: string) => {
    const fullUrl = shareUrl.startsWith('http') ? shareUrl : `${window.location.origin}${shareUrl}`;
    navigator.clipboard.writeText(fullUrl);
    showToast("Success", "Share link copied to clipboard");
  };

  const openShareLink = (shareUrl: string) => {
    const fullUrl = shareUrl.startsWith('http') ? shareUrl : `${window.location.origin}${shareUrl}`;
    window.open(fullUrl, '_blank');
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    showToast("Success", "Copied to clipboard");
  };

  const getDefaultOperationsForType = (datasetType: string): string[] => {
    switch (datasetType.toLowerCase()) {
      case 'mysql':
      case 'postgresql':
      case 'clickhouse':
        return ['SELECT', 'INSERT', 'UPDATE', 'DELETE'];
      case 's3':
        return ['GET', 'PUT', 'DELETE', 'LIST'];
      case 'api':
        return ['GET', 'POST'];
      case 'mongodb':
        return ['find', 'insert', 'update', 'delete'];
      default:
        return ['READ'];
    }
  };

  const generateProxyConnectionString = (dataset: Dataset): string => {
    if (!dataset.share_token) return '';
    
    const encodedDatasetName = encodeURIComponent(dataset.name);
    
    switch (dataset.type.toLowerCase()) {
      case 'mysql':
        return `mysql://proxy_user:${dataset.share_token}@localhost:10101/${encodedDatasetName}`;
      case 'postgresql':
        return `postgresql://proxy_user:${dataset.share_token}@localhost:10102/${encodedDatasetName}`;
      case 'clickhouse':
        return `clickhouse://proxy_user:${dataset.share_token}@localhost:10104/${encodedDatasetName}`;
      case 's3':
        return `s3://localhost:10106/${encodedDatasetName}?access_key=proxy_user&secret_key=${dataset.share_token}`;
      case 'mongodb':
        return `mongodb://proxy_user:${dataset.share_token}@localhost:10105/${encodedDatasetName}`;
      case 'api':
        return `http://localhost:10103/api/${encodedDatasetName}?token=${dataset.share_token}`;
      default:
        return `http://localhost:10103/api/${encodedDatasetName}?token=${dataset.share_token}`;
    }
  };

  const getStatsForLevel = (level: 'private' | 'organization' | 'public') => {
    return datasets.filter(d => {
      const datasetLevel = d.sharing_level?.toLowerCase() || 'private';
      return datasetLevel === level;
    }).length;
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
                <h3 className="text-sm font-medium text-red-800">Error loading data</h3>
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
                Data Sharing & Connection Hub
              </h1>
              <p className="text-gray-600 mt-1 text-sm">
                Unified management for datasets, secure proxies, and data connections
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
                <Database className="h-5 w-5 text-indigo-600 mr-1" />
                <span className="text-sm font-medium text-gray-500">Total</span>
              </div>
              <div className="text-xl font-bold text-gray-900">{datasets.length}</div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            <div className="py-2 px-1 border-b-2 border-blue-500 font-medium text-sm text-blue-600">
              <Share2 className="w-4 h-4 inline mr-1" />
              Dataset Sharing ({datasets.length})
            </div>
            <Link
              href="/connectors"
              className="py-2 px-1 border-b-2 border-transparent font-medium text-sm text-gray-500 hover:text-gray-700 hover:border-gray-300"
            >
              <Database className="w-4 h-4 inline mr-1" />
              Data Connectors
            </Link>
          </nav>
        </div>

        {/* Dataset Sharing Content */}
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <div className="px-4 py-4 sm:px-6 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Dataset Sharing Management</h3>
              <p className="text-sm text-gray-600 mt-1">Manage sharing levels and public share links for your datasets</p>
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
                    <Plus className="h-4 w-4 mr-2" />
                    Add Dataset
                  </Link>
                </div>
              </div>
            ) : (
              <ul className="divide-y divide-gray-200">
                {datasets.map((dataset) => (
                  <li key={dataset.id} className="px-4 py-6 sm:px-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3">
                          <div className="flex-shrink-0">
                            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                              <Database className="w-5 h-5 text-blue-600" />
                            </div>
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2">
                              <h3 className="text-sm font-medium text-gray-900 truncate">
                                {dataset.name}
                              </h3>
                              <SharingLevelBadge level={(dataset.sharing_level?.toLowerCase() || 'private') as 'private' | 'organization' | 'public'} />
                            </div>
                            <p className="text-sm text-gray-500 truncate">
                              {dataset.description || 'No description'}
                            </p>
                            <div className="flex items-center space-x-4 mt-1">
                              <span className="text-xs text-gray-500 capitalize">
                                {dataset.type}
                              </span>
                              {dataset.size_bytes && (
                                <span className="text-xs text-gray-500">
                                  {formatFileSize(dataset.size_bytes)}
                                </span>
                              )}
                              <span className="text-xs text-gray-500">
                                Created {formatDate(dataset.created_at)}
                              </span>
                              {dataset.view_count !== undefined && (
                                <span className="text-xs text-gray-500">
                                  {dataset.view_count} views
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex flex-col items-end space-y-3 ml-4">
                        {/* Sharing Level Selector */}
                        <div className="flex-shrink-0">
                          <SharingLevelSelector
                            currentLevel={(dataset.sharing_level?.toLowerCase() || 'private') as 'private' | 'organization' | 'public'}
                            onLevelChange={(level) => handleSharingLevelChange(dataset.id, level)}
                          />
                        </div>
                        
                        {/* Action Buttons */}
                        <div className="flex items-center space-x-2">
                          {dataset.public_share_enabled && dataset.share_url ? (
                            <>
                              <button
                                onClick={() => copyShareLink(dataset.share_url!)}
                                className="inline-flex items-center px-2 py-1 border border-gray-300 rounded text-xs font-medium text-gray-700 bg-white hover:bg-gray-50"
                                title="Copy Share Link"
                              >
                                <Copy className="h-3 w-3" />
                              </button>
                              <button
                                onClick={() => openShareLink(dataset.share_url!)}
                                className="inline-flex items-center px-2 py-1 border border-gray-300 rounded text-xs font-medium text-gray-700 bg-white hover:bg-gray-50"
                                title="Open Share Link"
                              >
                                <ExternalLink className="h-3 w-3" />
                              </button>
                              <button
                                onClick={() => {
                                  const connectionString = generateProxyConnectionString(dataset);
                                  if (connectionString) {
                                    copyToClipboard(connectionString);
                                    showToast("Success", "Proxy connection string copied to clipboard");
                                  }
                                }}
                                className="inline-flex items-center px-2 py-1 border border-blue-300 rounded text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100"
                                title="Copy DB Connection"
                              >
                                <Database className="h-3 w-3" />
                              </button>
                              <button
                                onClick={() => handleDisableSharing(dataset.id)}
                                className="inline-flex items-center px-2 py-1 border border-red-300 rounded text-xs font-medium text-red-700 bg-red-50 hover:bg-red-100"
                                title="Disable Sharing"
                              >
                                <Trash2 className="h-3 w-3" />
                              </button>
                            </>
                          ) : (
                            <button
                              onClick={() => handleCreateShareLink(dataset.id)}
                              className="inline-flex items-center px-3 py-2 border border-green-300 rounded-md text-sm font-medium text-green-700 bg-green-50 hover:bg-green-100"
                            >
                              <Share2 className="h-4 w-4 mr-1" />
                              Create Share
                            </button>
                          )}
                        </div>
                        
                        {/* Status Indicator */}
                        {dataset.public_share_enabled && (
                          <div className="flex items-center space-x-1">
                            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                            <span className="text-xs text-gray-500">Public</span>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {/* Collapsible Details for Public Datasets */}
                    {dataset.public_share_enabled && dataset.share_token && (
                      <div className="mt-4 border-t border-gray-100 pt-4">
                        <details className="group">
                          <summary className="flex items-center justify-between cursor-pointer text-sm font-medium text-blue-700 hover:text-blue-800">
                            <span className="flex items-center space-x-2">
                              <Shield className="h-4 w-4" />
                              <span>Connection Details & Access Instructions</span>
                            </span>
                            <ChevronDown className="h-4 w-4 group-open:rotate-180 transition-transform" />
                          </summary>
                          <div className="mt-3 space-y-3">
                            {/* Proxy Connection Info */}
                            <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-blue-900">Database Proxy Access</span>
                                <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded">
                                  {dataset.type.toUpperCase()}
                                </span>
                              </div>
                              <p className="text-xs text-blue-700 mb-2">
                                Connect directly using {dataset.type} clients with the proxy connection string.
                              </p>
                              <div className="text-xs text-blue-600">
                                <strong>Supported operations:</strong> {getDefaultOperationsForType(dataset.type).join(', ')}
                              </div>
                            </div>
                            
                            {/* Access Instructions */}
                            {dataset.share_url && (
                              <div className="p-3 bg-gray-50 border border-gray-200 rounded-md">
                                <AccessInstructions
                                  shareLink={dataset.share_url}
                                  shareToken={dataset.share_token || ''}
                                  accessType={dataset.sharing_level === 'public' ? 'public' : 'token'}
                                  expiresAt={dataset.share_expires_at}
                                  instructions={[
                                    'Use the share link to access the dataset directly',
                                    'Include the access token for API requests',
                                    'Proxy connection strings are available for database clients',
                                    'Chat functionality is enabled for this dataset'
                                  ]}
                                />
                              </div>
                            )}
                          </div>
                        </details>
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )}
        </div>

      </div>
    </div>
  );
}