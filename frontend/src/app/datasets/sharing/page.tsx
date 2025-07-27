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
  Link as LinkIcon,
  TestTube,
  Zap,
  RefreshCw
} from 'lucide-react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { SharingLevelSelector, SharingLevelBadge } from '@/components/datasets/SharingLevelSelector';
import { datasetsAPI, dataSharingAPI, dataConnectorsAPI } from '@/lib/api';
import ProxyConnectorForm from '@/components/proxy/ProxyConnectorForm';
import SharedLinkForm from '@/components/proxy/SharedLinkForm';
import SimplifiedConnectorForm from '@/components/connectors/SimplifiedConnectorForm';
import { parseConnectionUrl } from '@/utils/connectionParser';
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

interface ProxyConnector {
  id: number;
  proxy_id: string;
  name: string;
  description?: string;
  connector_type: string;
  proxy_url: string;
  is_public: boolean;
  allowed_operations: string[];
  total_requests: number;
  created_at: string;
  last_accessed_at?: string;
}

interface SharedLink {
  id: number;
  share_id: string;
  name: string;
  description?: string;
  public_url: string;
  is_public: boolean;
  requires_authentication: boolean;
  expires_at?: string;
  max_uses?: number;
  current_uses: number;
  created_at: string;
}

interface DatabaseConnector {
  id: number;
  name: string;
  connector_type: string;
  description?: string;
  is_active: boolean;
  test_status: string;
  last_tested_at?: string;
  created_at: string;
  mindsdb_database_name?: string;
  organization_id: number;
  datasets?: any[];
}

interface SimplifiedConnectorData {
  name: string;
  description: string;
  connector_type: string;
  connection_url: string;
}

export default function UnifiedSharingPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <UnifiedSharingContent />
      </DashboardLayout>
    </ProtectedRoute>
  );
}

function UnifiedSharingContent() {
  // State for datasets
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  
  // State for proxy connectors
  const [proxyConnectors, setProxyConnectors] = useState<ProxyConnector[]>([]);
  const [sharedLinks, setSharedLinks] = useState<SharedLink[]>([]);
  
  // State for simplified connectors
  const [simplifiedConnectors, setSimplifiedConnectors] = useState<DatabaseConnector[]>([]);
  
  // UI state
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'datasets' | 'proxies' | 'links' | 'connectors'>('datasets');
  
  // Check URL params for initial tab
  const searchParams = useSearchParams();
  const router = useRouter();
  const tabParam = searchParams.get('tab') as 'datasets' | 'proxies' | 'links' | 'connectors' | null;
  
  // Modal states
  const [showCreateProxy, setShowCreateProxy] = useState(false);
  const [showCreateLink, setShowCreateLink] = useState(false);
  const [showCreateConnector, setShowCreateConnector] = useState(false);
  const [selectedProxyForLink, setSelectedProxyForLink] = useState<ProxyConnector | null>(null);
  const [creating, setCreating] = useState(false);
  
  // Action states
  const [testing, setTesting] = useState<Record<number, boolean>>({});
  const [syncing, setSyncing] = useState<Record<number, boolean>>({});

  const handleTabChange = (tab: 'datasets' | 'proxies' | 'links' | 'connectors') => {
    setActiveTab(tab);
    const url = new URL(window.location.href);
    url.searchParams.set('tab', tab);
    router.replace(url.toString(), { scroll: false });
  };

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

  const isExpired = (expiresAt?: string) => {
    if (!expiresAt) return false;
    return new Date(expiresAt) < new Date();
  };

  useEffect(() => {
    fetchAllData();
    
    // Set initial tab from URL parameter
    if (tabParam && ['datasets', 'proxies', 'links', 'connectors'].includes(tabParam)) {
      setActiveTab(tabParam);
    }
  }, [tabParam]);

  const fetchAllData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Fetch datasets
      const datasetsResponse = await datasetsAPI.getDatasets();
      setDatasets(datasetsResponse);
      
      // Fetch simplified connectors
      const connectorsResponse = await dataConnectorsAPI.getConnectors({ include_datasets: true });
      setSimplifiedConnectors(connectorsResponse);
      
      // Mock data for proxy connectors and shared links (replace with actual API calls)
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setProxyConnectors([
        {
          id: 1,
          proxy_id: 'px_abc123',
          name: 'Customer API Proxy',
          description: 'Secure access to customer management API',
          connector_type: 'api',
          proxy_url: '/proxy/px_abc123',
          is_public: false,
          allowed_operations: ['GET', 'POST'],
          total_requests: 245,
          created_at: '2024-01-15T10:30:00Z',
          last_accessed_at: '2024-01-20T14:22:00Z'
        },
        {
          id: 2,
          proxy_id: 'px_def456',
          name: 'Analytics Database',
          description: 'Read-only access to analytics database',
          connector_type: 'database',
          proxy_url: '/proxy/px_def456',
          is_public: true,
          allowed_operations: ['SELECT'],
          total_requests: 89,
          created_at: '2024-01-10T09:15:00Z',
          last_accessed_at: '2024-01-19T16:45:00Z'
        }
      ]);

      setSharedLinks([
        {
          id: 1,
          share_id: 'sh_xyz789',
          name: 'Customer Dashboard Access',
          description: 'Shared access for external partners',
          public_url: '/share/sh_xyz789',
          is_public: false,
          requires_authentication: true,
          expires_at: '2024-02-15T23:59:59Z',
          max_uses: 100,
          current_uses: 23,
          created_at: '2024-01-15T11:00:00Z'
        }
      ]);
      
    } catch (error: any) {
      console.error('Failed to fetch data:', error);
      setError(error.response?.data?.detail || 'Failed to fetch data');
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
      
      // Automatically create a proxy connector for the shared dataset
      const dataset = datasets.find(d => d.id === datasetId);
      if (dataset) {
        try {
          const proxyData = {
            name: `${dataset.name} Proxy`,
            description: `Secure proxy access for shared dataset: ${dataset.name}`,
            connector_type: dataset.type.toLowerCase(), // mysql, postgresql, s3, etc.
            dataset_id: datasetId,
            share_token: response.share_token,
            is_public: dataset.sharing_level === 'public',
            allowed_operations: getDefaultOperationsForType(dataset.type),
            generate_credentials: true
          };
          
          // Create proxy connector (this would be a real API call)
          console.log('Creating proxy connector for shared dataset:', proxyData);
          
          showToast("Success", "Share link and proxy connector created successfully");
        } catch (proxyError) {
          console.warn('Failed to create proxy connector:', proxyError);
          showToast("Warning", "Share link created but proxy connector failed");
        }
      } else {
        showToast("Success", "Share link created successfully");
      }
      
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
      
      // Refresh all data to show new proxy connector
      fetchAllData();
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

  // Proxy connector handlers
  const handleCreateProxy = async (data: any) => {
    setCreating(true);
    try {
      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      console.log('Creating proxy:', data);
      setShowCreateProxy(false);
      fetchAllData();
    } catch (error) {
      console.error('Failed to create proxy:', error);
      throw error;
    } finally {
      setCreating(false);
    }
  };

  const handleCreateSharedLink = async (data: any) => {
    setCreating(true);
    try {
      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      console.log('Creating shared link:', data);
      setShowCreateLink(false);
      setSelectedProxyForLink(null);
      fetchAllData();
    } catch (error) {
      console.error('Failed to create shared link:', error);
      throw error;
    } finally {
      setCreating(false);
    }
  };

  // Simplified connector handlers
  const handleCreateConnector = async (data: SimplifiedConnectorData) => {
    setCreating(true);
    setError(null);

    try {
      // Validate the URL before sending to backend
      const parseResult = parseConnectionUrl(data.connection_url, data.connector_type);
      if (!parseResult.success) {
        throw new Error(parseResult.error);
      }

      await dataConnectorsAPI.createSimplifiedConnector(data);
      setShowCreateConnector(false);
      fetchAllData();
    } catch (error: any) {
      console.error('Failed to create connector:', error);
      setError(error.response?.data?.detail || error.message || 'Failed to create connector');
      throw error;
    } finally {
      setCreating(false);
    }
  };

  const handleTestConnection = async (connectorId: number) => {
    setTesting(prev => ({ ...prev, [connectorId]: true }));
    
    try {
      await dataConnectorsAPI.testConnector(connectorId);
      fetchAllData(); // Refresh to get updated status
    } catch (error) {
      console.error('Test failed:', error);
    } finally {
      setTesting(prev => ({ ...prev, [connectorId]: false }));
    }
  };

  const handleCreateDatasetFromConnector = async (connectorId: number) => {
    const connector = simplifiedConnectors.find(c => c.id === connectorId);
    if (!connector) return;

    const datasetName = prompt(`Create dataset from ${connector.name}:`, `${connector.name} Dataset`);
    if (!datasetName) return;

    let tableName = "default_table";
    if (connector.connector_type === 'mysql' || connector.connector_type === 'postgresql') {
      tableName = prompt(`Enter table name for ${connector.connector_type} database:`, "");
      if (!tableName) {
        showToast("Error", "Table name is required for database connections");
        return;
      }
    }

    try {
      setCreating(true);
      const result = await dataConnectorsAPI.createDatasetFromConnector(connectorId, {
        dataset_name: datasetName,
        description: `Dataset created from ${connector.name} connector`,
        table_or_endpoint: tableName,
        sharing_level: 'private'
      });
      
      showToast("Success", `Dataset "${datasetName}" created successfully! You can now chat with this data.`);
      fetchAllData(); // Refresh to show new dataset
    } catch (error: any) {
      console.error('Dataset creation failed:', error);
      showToast("Error", `Failed to create dataset: ${error.response?.data?.detail || error.message}`);
    } finally {
      setCreating(false);
    }
  };

  const handleSyncWithMindsDB = async (connectorId: number) => {
    setSyncing(prev => ({ ...prev, [connectorId]: true }));
    
    try {
      await dataConnectorsAPI.syncWithMindsDB(connectorId);
      fetchAllData(); // Refresh to get updated status
    } catch (error) {
      console.error('Sync failed:', error);
    } finally {
      setSyncing(prev => ({ ...prev, [connectorId]: false }));
    }
  };

  const handleDeleteConnector = async (connectorId: number) => {
    if (!confirm('Are you sure you want to delete this connection?')) {
      return;
    }

    try {
      await dataConnectorsAPI.deleteConnector(connectorId);
      fetchAllData();
    } catch (error) {
      console.error('Delete failed:', error);
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

  const generateProxyConnectionString = (dataset: Dataset, proxyConnector?: ProxyConnector): string => {
    if (!proxyConnector) return '';
    
    const baseUrl = window.location.origin;
    const proxyHost = baseUrl.replace(/:\d+$/, ':8000'); // Use backend port 8000
    const proxyEndpoint = `${proxyHost}/proxy/${proxyConnector.proxy_id}`;
    const encodedDatasetName = encodeURIComponent(dataset.name);
    
    switch (dataset.type.toLowerCase()) {
      case 'mysql':
        return `mysql://proxy_user:${dataset.share_token}@${proxyHost.replace(/^https?:\/\//, '')}:8000/${encodedDatasetName}`;
      case 'postgresql':
        return `postgresql://proxy_user:${dataset.share_token}@${proxyHost.replace(/^https?:\/\//, '')}:8000/${encodedDatasetName}`;
      case 'clickhouse':
        return `clickhouse://proxy_user:${dataset.share_token}@${proxyHost.replace(/^https?:\/\//, '')}:8000/${encodedDatasetName}`;
      case 's3':
        return `s3://${proxyEndpoint}/${encodedDatasetName}?access_key=proxy_user&secret_key=${dataset.share_token}`;
      case 'mongodb':
        return `mongodb://proxy_user:${dataset.share_token}@${proxyHost.replace(/^https?:\/\//, '')}:8000/${encodedDatasetName}`;
      default:
        return `${proxyEndpoint}?token=${dataset.share_token}`;
    }
  };

  const getStatsForLevel = (level: 'private' | 'organization' | 'public') => {
    return datasets.filter(d => d.sharing_level === level).length;
  };

  const getSharedDatasets = () => {
    return datasets.filter(d => d.public_share_enabled);
  };

  const getConnectorIcon = (type: string) => {
    switch (type) {
      case 'api':
        return <Globe className="w-5 h-5" />;
      case 'database':
        return <Database className="w-5 h-5" />;
      case 'shared_link':
        return <LinkIcon className="w-5 h-5" />;
      case 'mysql':
      case 'postgresql':
      case 'mongodb':
      case 'clickhouse':
        return <Database className="w-5 h-5" />;
      case 's3':
        return <Database className="w-5 h-5" />;
      default:
        return <Shield className="w-5 h-5" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'text-green-600 bg-green-100';
      case 'failed': return 'text-red-600 bg-red-100';
      case 'pending': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
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
                <span className="text-sm font-medium text-gray-500">Connections</span>
              </div>
              <div className="text-xl font-bold text-gray-900">{simplifiedConnectors.length}</div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => handleTabChange('datasets')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'datasets'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Share2 className="w-4 h-4 inline mr-1" />
              Dataset Sharing ({datasets.length})
            </button>
            <button
              onClick={() => handleTabChange('connectors')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'connectors'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Database className="w-4 h-4 inline mr-1" />
              Data Connections ({simplifiedConnectors.length})
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'datasets' && (
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
                    <div className="flex items-center justify-between">
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
                              <SharingLevelBadge level={dataset.sharing_level} />
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
                            
                            {/* Proxy Connection Details */}
                            {dataset.public_share_enabled && dataset.share_token && (
                              <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-md">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center space-x-2">
                                    <Shield className="h-4 w-4 text-blue-600" />
                                    <span className="text-sm font-medium text-blue-900">Third-Party Access</span>
                                  </div>
                                  <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded">
                                    {dataset.type.toUpperCase()} Proxy
                                  </span>
                                </div>
                                <p className="text-xs text-blue-700 mt-1">
                                  Use the "Copy DB Connection" button above to get connection string for {dataset.type} clients
                                </p>
                                <div className="mt-2 text-xs text-blue-600">
                                  <strong>Supported operations:</strong> {getDefaultOperationsForType(dataset.type).join(', ')}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-4">
                        <div className="flex-shrink-0">
                          <SharingLevelSelector
                            currentLevel={dataset.sharing_level}
                            onLevelChange={(level) => handleSharingLevelChange(dataset.id, level)}
                          />
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          {dataset.public_share_enabled && dataset.share_url ? (
                            <>
                              <button
                                onClick={() => copyShareLink(dataset.share_url!)}
                                className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                              >
                                <Copy className="h-4 w-4 mr-1" />
                                Copy Link
                              </button>
                              <button
                                onClick={() => openShareLink(dataset.share_url!)}
                                className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                              >
                                <ExternalLink className="h-4 w-4 mr-1" />
                                Open
                              </button>
                              <button
                                onClick={() => {
                                  const proxyConnector = proxyConnectors.find(p => p.name === `${dataset.name} Proxy`);
                                  const connectionString = generateProxyConnectionString(dataset, proxyConnector);
                                  if (connectionString) {
                                    copyToClipboard(connectionString);
                                    showToast("Success", "Proxy connection string copied to clipboard");
                                  }
                                }}
                                className="inline-flex items-center px-3 py-2 border border-blue-300 rounded-md text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100"
                              >
                                <Database className="h-4 w-4 mr-1" />
                                Copy DB Connection
                              </button>
                              <button
                                onClick={() => handleDisableSharing(dataset.id)}
                                className="inline-flex items-center px-3 py-2 border border-red-300 rounded-md text-sm font-medium text-red-700 bg-red-50 hover:bg-red-100"
                              >
                                <Trash2 className="h-4 w-4 mr-1" />
                                Disable
                              </button>
                            </>
                          ) : (
                            <button
                              onClick={() => handleCreateShareLink(dataset.id)}
                              className="inline-flex items-center px-3 py-2 border border-green-300 rounded-md text-sm font-medium text-green-700 bg-green-50 hover:bg-green-100"
                            >
                              <Share2 className="h-4 w-4 mr-1" />
                              Create Share + Proxy
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {activeTab === 'connectors' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-medium text-gray-900">Data Connections</h3>
                <p className="text-sm text-gray-600 mt-1">Connect to your databases and APIs with simple URLs</p>
              </div>
              <button
                onClick={() => setShowCreateConnector(true)}
                className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Connection
              </button>
            </div>

            {simplifiedConnectors.length === 0 ? (
              <div className="bg-white rounded-lg p-12 text-center">
                <Database className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No connections yet</h3>
                <p className="text-gray-600 mb-6">
                  Get started by creating your first data connection
                </p>
                <button
                  onClick={() => setShowCreateConnector(true)}
                  className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add Your First Connection
                </button>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow divide-y divide-gray-200">
                {simplifiedConnectors.map((connector) => (
                  <div key={connector.id} className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="flex-shrink-0 text-indigo-600">
                          {getConnectorIcon(connector.connector_type)}
                        </div>
                        <div>
                          <h3 className="text-lg font-medium text-gray-900">
                            {connector.name}
                          </h3>
                          <p className="text-sm text-gray-600 capitalize">
                            {connector.connector_type} • {connector.description || 'No description'}
                          </p>
                          <div className="flex items-center space-x-4 mt-2">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(connector.test_status)}`}>
                              {connector.test_status}
                            </span>
                            {connector.datasets && connector.datasets.length > 0 && (
                              <span className="text-xs text-gray-500">
                                {connector.datasets.length} dataset{connector.datasets.length !== 1 ? 's' : ''}
                              </span>
                            )}
                            <span className="text-xs text-gray-500">
                              Created {formatDate(connector.created_at)}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        {connector.test_status === 'success' && (
                          <button
                            onClick={() => handleCreateDatasetFromConnector(connector.id)}
                            disabled={creating}
                            className="inline-flex items-center px-3 py-2 border border-green-300 rounded-md text-sm font-medium text-green-700 bg-green-50 hover:bg-green-100 disabled:opacity-50"
                          >
                            {creating ? (
                              <RefreshCw className="w-4 h-4 animate-spin mr-1" />
                            ) : (
                              <Plus className="w-4 h-4 mr-1" />
                            )}
                            Add to Dataset
                          </button>
                        )}
                        
                        <button
                          onClick={() => handleSyncWithMindsDB(connector.id)}
                          disabled={syncing[connector.id]}
                          className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                        >
                          {syncing[connector.id] ? (
                            <RefreshCw className="w-4 h-4 animate-spin" />
                          ) : (
                            <Zap className="w-4 h-4" />
                          )}
                        </button>
                        
                        <button
                          onClick={() => handleTestConnection(connector.id)}
                          disabled={testing[connector.id]}
                          className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                        >
                          {testing[connector.id] ? (
                            <RefreshCw className="w-4 h-4 animate-spin" />
                          ) : (
                            <TestTube className="w-4 h-4" />
                          )}
                        </button>
                        
                        <button
                          onClick={() => handleDeleteConnector(connector.id)}
                          className="inline-flex items-center px-3 py-2 border border-red-300 rounded-md text-sm font-medium text-red-700 bg-red-50 hover:bg-red-100"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Modals */}
        {showCreateProxy && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
            <div className="relative mx-auto p-5 border w-11/12 md:w-3/4 lg:w-2/3 shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
              <ProxyConnectorForm
                onSubmit={handleCreateProxy}
                onCancel={() => setShowCreateProxy(false)}
                isSubmitting={creating}
              />
            </div>
          </div>
        )}

        {showCreateLink && selectedProxyForLink && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
            <div className="relative mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
              <SharedLinkForm
                proxyConnectorId={selectedProxyForLink.id}
                proxyConnectorName={selectedProxyForLink.name}
                onSubmit={handleCreateSharedLink}
                onCancel={() => {
                  setShowCreateLink(false);
                  setSelectedProxyForLink(null);
                }}
                isSubmitting={creating}
              />
            </div>
          </div>
        )}

        {showCreateConnector && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
            <div className="relative mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white max-h-[80vh] overflow-y-auto">
              <SimplifiedConnectorForm
                onSubmit={handleCreateConnector}
                onCancel={() => setShowCreateConnector(false)}
                isSubmitting={creating}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}