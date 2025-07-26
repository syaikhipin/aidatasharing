'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { dataSharingAPI } from '@/lib/api';
import { Eye, Download, MessageSquare, Lock, Calendar, User, Database, Shield, Copy } from 'lucide-react';

interface SharedDataset {
  dataset_id: number;
  dataset_name: string;
  description?: string;
  file_type?: string;
  size_bytes?: number;
  row_count?: number;
  column_count?: number;
  owner_name?: string;
  organization_name?: string;
  shared_at?: string;
  expires_at?: string;
  access_allowed: boolean;
  requires_password: boolean;
  enable_chat: boolean;
  preview_data?: any;
}

export default function SharedDatasetPage() {
  const params = useParams();
  const token = params.token as string;
  
  const [dataset, setDataset] = useState<SharedDataset | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [password, setPassword] = useState('');
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [isAuthenticating, setIsAuthenticating] = useState(false);

  useEffect(() => {
    if (token) {
      fetchSharedDataset();
    }
  }, [token]);

  const fetchSharedDataset = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // First try public access (no authentication required)
      try {
        const response = await dataSharingAPI.getPublicSharedDataset(token);
        setDataset(response);
        
        if (response.requires_password && !response.access_allowed) {
          setShowPasswordForm(true);
        }
        return;
      } catch (publicError: any) {
        // If public access fails, try authenticated access
        console.log('Public access failed, trying authenticated access:', publicError.response?.status);
        
        if (publicError.response?.status === 401 || publicError.response?.status === 403) {
          // This might be an organization-level dataset requiring authentication
          try {
            const response = await dataSharingAPI.getSharedDataset(token);
            setDataset(response);
            
            if (response.requires_password && !response.access_allowed) {
              setShowPasswordForm(true);
            }
            return;
          } catch (authError: any) {
            // If authenticated access also fails, show appropriate error
            if (authError.response?.status === 401) {
              setError('This dataset requires you to be logged in. Please login and try again.');
            } else {
              throw authError;
            }
          }
        } else {
          throw publicError;
        }
      }
    } catch (error: any) {
      console.error('Failed to fetch shared dataset:', error);
      setError(error.response?.data?.detail || 'Failed to access shared dataset');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setIsAuthenticating(true);
      setError(null);
      
      // First try public access with password
      try {
        const response = await dataSharingAPI.accessPublicSharedDatasetWithPassword(token, password);
        setDataset(response);
        setShowPasswordForm(false);
        return;
      } catch (publicError: any) {
        // If public access fails, try authenticated access with password
        if (publicError.response?.status === 401 || publicError.response?.status === 403) {
          const response = await dataSharingAPI.accessSharedDatasetWithPassword(token, password);
          setDataset(response);
          setShowPasswordForm(false);
        } else {
          throw publicError;
        }
      }
    } catch (error: any) {
      console.error('Password authentication failed:', error);
      setError(error.response?.data?.detail || 'Invalid password');
    } finally {
      setIsAuthenticating(false);
    }
  };

  const handleDownload = async () => {
    try {
      // Create download URL
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const downloadUrl = `${API_BASE_URL}/api/data-sharing/shared/${token}/download`;
      
      // Open download in new window
      window.open(downloadUrl, '_blank');
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const formatFileSize = (bytes?: number): string => {
    if (!bytes) return 'Unknown size';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString?: string): string => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // Simple toast notification - can be enhanced with proper toast library
    const originalTitle = document.title;
    document.title = '✓ Copied to clipboard!';
    setTimeout(() => {
      document.title = originalTitle;
    }, 2000);
  };

  const generateConnectionString = (dataset: SharedDataset, token: string): string => {
    const host = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
    const proxyHost = `${host}:${getPortForType(dataset.file_type)}`;
    
    switch (dataset.file_type?.toLowerCase()) {
      case 'mysql':
        return `mysql://proxy_user:${token}@${proxyHost}/${dataset.dataset_name}`;
      case 'postgresql':
        return `postgresql://proxy_user:${token}@${proxyHost}/${dataset.dataset_name}`;
      case 'clickhouse':
        return `clickhouse://proxy_user:${token}@${proxyHost}/${dataset.dataset_name}`;
      case 's3':
        return `s3://${proxyHost}/${dataset.dataset_name}?access_key=proxy_user&secret_key=${token}`;
      case 'mongodb':
        return `mongodb://proxy_user:${token}@${proxyHost}/${dataset.dataset_name}`;
      case 'api':
        return `https://${proxyHost}/api/${dataset.dataset_name}?token=${token}`;
      default:
        return `${proxyHost}/${dataset.dataset_name}?token=${token}`;
    }
  };

  const getPortForType = (fileType?: string): string => {
    switch (fileType?.toLowerCase()) {
      case 'mysql':
        return '3306';
      case 'postgresql':
        return '5432';
      case 'clickhouse':
        return '8123';
      case 'mongodb':
        return '27017';
      case 's3':
        return '443';
      case 'api':
        return '443';
      default:
        return '8080';
    }
  };

  const getSupportedOperations = (fileType?: string): string[] => {
    switch (fileType?.toLowerCase()) {
      case 'mysql':
      case 'postgresql':
      case 'clickhouse':
        return ['SELECT', 'SHOW', 'DESCRIBE'];
      case 's3':
        return ['GET', 'LIST'];
      case 'api':
        return ['GET'];
      case 'mongodb':
        return ['find', 'aggregate'];
      default:
        return ['READ'];
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading shared dataset...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
              <Lock className="h-6 w-6 text-red-600" />
            </div>
            <h3 className="mt-2 text-lg font-medium text-gray-900">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (showPasswordForm) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
          <div className="text-center mb-6">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-blue-100">
              <Lock className="h-6 w-6 text-blue-600" />
            </div>
            <h3 className="mt-2 text-lg font-medium text-gray-900">Password Required</h3>
            <p className="mt-1 text-sm text-gray-500">This shared dataset is password protected</p>
          </div>

          <form onSubmit={handlePasswordSubmit}>
            <div className="mb-4">
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter password"
                required
              />
            </div>

            {error && (
              <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={isAuthenticating}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {isAuthenticating ? 'Verifying...' : 'Access Dataset'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  if (!dataset || !dataset.access_allowed) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
              <Lock className="h-6 w-6 text-red-600" />
            </div>
            <h3 className="mt-2 text-lg font-medium text-gray-900">Access Not Allowed</h3>
            <p className="mt-1 text-sm text-gray-500">You don't have permission to access this dataset</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="bg-white shadow rounded-lg mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{dataset.dataset_name}</h1>
                {dataset.description && (
                  <p className="mt-1 text-sm text-gray-600">{dataset.description}</p>
                )}
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={handleDownload}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download
                </button>
                {dataset.enable_chat && (
                  <button className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                    <MessageSquare className="h-4 w-4 mr-2" />
                    Chat with Data
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Dataset Info */}
          <div className="px-6 py-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="flex items-center">
                <Database className="h-5 w-5 text-gray-400 mr-2" />
                <div>
                  <div className="text-sm font-medium text-gray-900">Type</div>
                  <div className="text-sm text-gray-600">{dataset.file_type?.toUpperCase() || 'Unknown'}</div>
                </div>
              </div>
              <div className="flex items-center">
                <Eye className="h-5 w-5 text-gray-400 mr-2" />
                <div>
                  <div className="text-sm font-medium text-gray-900">Size</div>
                  <div className="text-sm text-gray-600">{formatFileSize(dataset.size_bytes)}</div>
                </div>
              </div>
              <div className="flex items-center">
                <User className="h-5 w-5 text-gray-400 mr-2" />
                <div>
                  <div className="text-sm font-medium text-gray-900">Shared by</div>
                  <div className="text-sm text-gray-600">{dataset.owner_name || 'Unknown'}</div>
                </div>
              </div>
              <div className="flex items-center">
                <Calendar className="h-5 w-5 text-gray-400 mr-2" />
                <div>
                  <div className="text-sm font-medium text-gray-900">Expires</div>
                  <div className="text-sm text-gray-600">{formatDate(dataset.expires_at)}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Proxy Connection Details */}
        <div className="bg-white shadow rounded-lg mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center">
              <Shield className="h-5 w-5 text-blue-600 mr-2" />
              <h2 className="text-lg font-medium text-gray-900">Third-Party Database Access</h2>
            </div>
            <p className="mt-1 text-sm text-gray-600">
              Connect to this dataset using your preferred database client or BI tool
            </p>
          </div>
          <div className="px-6 py-4">
            <div className="grid gap-4">
              {/* Connection Details */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center">
                    <Database className="h-5 w-5 text-blue-600 mr-2" />
                    <span className="font-medium text-blue-900">
                      {dataset.file_type?.toUpperCase() || 'DATABASE'} Connection
                    </span>
                  </div>
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                    Secure Proxy
                  </span>
                </div>
                
                {/* Connection String */}
                <div className="mb-3">
                  <label className="block text-sm font-medium text-blue-900 mb-1">
                    Connection String
                  </label>
                  <div className="flex items-center space-x-2">
                    <code className="flex-1 text-sm bg-white border border-blue-200 rounded px-3 py-2 font-mono">
                      {generateConnectionString(dataset, token)}
                    </code>
                    <button
                      onClick={() => copyToClipboard(generateConnectionString(dataset, token))}
                      className="p-2 text-blue-600 hover:bg-blue-100 rounded"
                      title="Copy connection string"
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {/* Credentials */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-blue-900 mb-1">
                      Username
                    </label>
                    <div className="flex items-center space-x-2">
                      <code className="flex-1 text-sm bg-white border border-blue-200 rounded px-3 py-2">
                        proxy_user
                      </code>
                      <button
                        onClick={() => copyToClipboard('proxy_user')}
                        className="p-2 text-blue-600 hover:bg-blue-100 rounded"
                        title="Copy username"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-blue-900 mb-1">
                      Password/Token
                    </label>
                    <div className="flex items-center space-x-2">
                      <code className="flex-1 text-sm bg-white border border-blue-200 rounded px-3 py-2 font-mono">
                        {token}
                      </code>
                      <button
                        onClick={() => copyToClipboard(token)}
                        className="p-2 text-blue-600 hover:bg-blue-100 rounded"
                        title="Copy token"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Additional Connection Info */}
                <div className="mt-3 pt-3 border-t border-blue-200">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                    <div>
                      <span className="font-medium text-blue-900">Host:</span>
                      <span className="ml-1 text-blue-700">{typeof window !== 'undefined' ? window.location.hostname : 'localhost'}</span>
                    </div>
                    <div>
                      <span className="font-medium text-blue-900">Port:</span>
                      <span className="ml-1 text-blue-700">{getPortForType(dataset.file_type)}</span>
                    </div>
                    <div>
                      <span className="font-medium text-blue-900">Database:</span>
                      <span className="ml-1 text-blue-700">{dataset.dataset_name}</span>
                    </div>
                    <div>
                      <span className="font-medium text-blue-900">SSL:</span>
                      <span className="ml-1 text-blue-700">Required</span>
                    </div>
                  </div>
                </div>

                {/* Supported Operations */}
                <div className="mt-3 pt-3 border-t border-blue-200">
                  <span className="text-sm font-medium text-blue-900">Supported Operations: </span>
                  <span className="text-sm text-blue-700">
                    {getSupportedOperations(dataset.file_type).join(', ')}
                  </span>
                </div>
              </div>

              {/* Usage Instructions */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">How to Connect</h4>
                <div className="text-sm text-gray-700 space-y-2">
                  <p>1. Copy the connection string above</p>
                  <p>2. Use it in your preferred database client (DBeaver, TablePlus, etc.)</p>
                  <p>3. Or use the individual credentials for manual configuration</p>
                  <p className="text-xs text-gray-500 mt-2">
                    Note: This is a secure proxy connection that provides read-only access to the shared dataset.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Preview Section */}
        {dataset.preview_data && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">Data Preview</h2>
            </div>
            <div className="px-6 py-4">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      {dataset.preview_data.headers?.map((header: string, index: number) => (
                        <th
                          key={index}
                          scope="col"
                          className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {dataset.preview_data.rows?.slice(0, 10).map((row: any[], rowIndex: number) => (
                      <tr key={rowIndex} className={rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        {row.map((cell: any, cellIndex: number) => (
                          <td key={cellIndex} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {cell !== null && cell !== undefined ? String(cell) : (
                              <span className="text-gray-400 italic">null</span>
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}