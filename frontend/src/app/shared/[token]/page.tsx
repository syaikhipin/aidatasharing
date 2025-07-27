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
  const [showChat, setShowChat] = useState(false);
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<any[]>([]);
  const [isChatting, setIsChatting] = useState(false);

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

  const handleChat = async () => {
    if (!chatMessage.trim() || !token) return;
    
    const userMessage = chatMessage.trim();
    setChatMessage('');
    
    // Add user message to history
    const newUserMessage = {
      id: Date.now(),
      type: 'user',
      message: userMessage,
      timestamp: new Date().toISOString()
    };
    setChatHistory(prev => [...prev, newUserMessage]);
    
    try {
      setIsChatting(true);
      const response = await dataSharingAPI.chatWithSharedDataset(token, userMessage);
      
      // Add AI response to history
      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        message: response.answer || response.response || 'No response received',
        timestamp: new Date().toISOString(),
        model: response.model,
        tokens_used: response.tokens_used,
        error: false
      };
      setChatHistory(prev => [...prev, aiMessage]);
      
    } catch (error: any) {
      console.error('Chat failed:', error);
      
      // Add error message to history
      const errorMessage = {
        id: Date.now() + 1,
        type: 'ai',
        message: error.response?.data?.detail || 'Failed to connect to chat service. Please try again.',
        timestamp: new Date().toISOString(),
        error: true
      };
      setChatHistory(prev => [...prev, errorMessage]);
    } finally {
      setIsChatting(false);
    }
  };

  const clearChat = () => {
    setChatHistory([]);
  };

  const generateConnectionString = (dataset: SharedDataset, token: string): string => {
    const host = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
    const proxyHost = `${host}:${getPortForType(dataset.file_type)}`;
    const encodedDatasetName = encodeURIComponent(dataset.dataset_name);
    
    switch (dataset.file_type?.toLowerCase()) {
      case 'mysql':
        return `mysql://proxy_user:${token}@${proxyHost}/${encodedDatasetName}`;
      case 'postgresql':
        return `postgresql://proxy_user:${token}@${proxyHost}/${encodedDatasetName}`;
      case 'clickhouse':
        return `clickhouse://proxy_user:${token}@${proxyHost}/${encodedDatasetName}`;
      case 's3':
        return `s3://${proxyHost}/${encodedDatasetName}?access_key=proxy_user&secret_key=${token}`;
      case 'mongodb':
        return `mongodb://proxy_user:${token}@${proxyHost}/${encodedDatasetName}`;
      case 'api':
        return `https://${proxyHost}/api/${encodedDatasetName}?token=${token}`;
      default:
        return `${proxyHost}/${encodedDatasetName}?token=${token}`;
    }
  };

  const getPortForType = (fileType?: string): string => {
    switch (fileType?.toLowerCase()) {
      case 'mysql':
        return '10101';  // MindsDB proxy MySQL port
      case 'postgresql':
        return '10102';  // MindsDB proxy PostgreSQL port
      case 'clickhouse':
        return '10104';  // MindsDB proxy ClickHouse port
      case 'mongodb':
        return '10105'; // MindsDB proxy MongoDB port
      case 's3':
        return '10106';  // MindsDB proxy S3 port
      case 'api':
        return '10103';  // MindsDB proxy API port
      default:
        return '10103';
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
                  <button 
                    onClick={() => setShowChat(!showChat)}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <MessageSquare className="h-4 w-4 mr-2" />
                    {showChat ? 'Hide Chat' : 'Chat with Data'}
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

        {/* Chat Interface */}
        {showChat && dataset.enable_chat && (
          <div className="bg-white shadow rounded-lg mb-6">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <MessageSquare className="h-5 w-5 text-blue-600 mr-2" />
                  <h2 className="text-lg font-medium text-gray-900">AI Chat Assistant</h2>
                </div>
                {chatHistory.length > 0 && (
                  <button
                    onClick={clearChat}
                    className="text-sm text-gray-500 hover:text-gray-700"
                  >
                    Clear Chat
                  </button>
                )}
              </div>
              <p className="mt-1 text-sm text-gray-600">
                Ask questions about the shared dataset and get AI-powered insights
              </p>
            </div>
            
            <div className="px-6 py-4">
              {/* Chat History */}
              {chatHistory.length > 0 && (
                <div className="mb-6 space-y-4 max-h-96 overflow-y-auto">
                  {chatHistory.map((message) => (
                    <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        message.type === 'user' 
                          ? 'bg-blue-600 text-white' 
                          : message.error
                          ? 'bg-red-50 border border-red-200 text-red-700'
                          : 'bg-gray-100 text-gray-900'
                      }`}>
                        <div className="text-sm whitespace-pre-wrap prose prose-sm max-w-none">
                          {message.type === 'ai' ? (
                            <div dangerouslySetInnerHTML={{ 
                              __html: message.message.replace(/\n/g, '<br/>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\*(.*?)\*/g, '<em>$1</em>') 
                            }} />
                          ) : (
                            message.message
                          )}
                        </div>
                        <p className="text-xs mt-1 opacity-75">
                          {new Date(message.timestamp).toLocaleTimeString()}
                          {message.model && !message.error && (
                            <span className="ml-2">• {message.model}</span>
                          )}
                          {message.tokens_used && !message.error && (
                            <span className="ml-1">• {message.tokens_used} tokens</span>
                          )}
                        </p>
                      </div>
                    </div>
                  ))}
                  {isChatting && (
                    <div className="flex justify-start">
                      <div className="bg-gray-100 text-gray-900 px-4 py-2 rounded-lg">
                        <div className="flex items-center space-x-2">
                          <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-300 border-t-blue-600"></div>
                          <span className="text-sm">AI is thinking...</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Chat Input */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Ask a question about the data
                  </label>
                  <div className="flex space-x-3">
                    <input
                      type="text"
                      value={chatMessage}
                      onChange={(e) => setChatMessage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleChat()}
                      placeholder="What insights can you provide about this dataset?"
                      className="flex-1 border border-gray-300 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      disabled={isChatting}
                    />
                    <button
                      onClick={handleChat}
                      disabled={!chatMessage.trim() || isChatting}
                      className="px-6 py-3 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isChatting ? (
                        <div className="flex items-center">
                          <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                          Asking...
                        </div>
                      ) : (
                        <>
                          <span className="mr-1">🚀</span>
                          Ask AI
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* Suggestions */}
                {chatHistory.length === 0 && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-blue-800 mb-2">💡 Try asking questions like:</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {[
                        "What insights can you provide about this dataset?",
                        "Analyze the data distribution and patterns",
                        "What are the key statistics in this data?",
                        "Can you summarize the main findings?",
                        "What columns are available in this dataset?",
                        "Suggest visualizations for this data"
                      ].map((suggestion, index) => (
                        <button
                          key={index}
                          onClick={() => setChatMessage(suggestion)}
                          className="text-left text-sm text-blue-700 hover:text-blue-900 p-2 rounded hover:bg-blue-100 transition-colors"
                        >
                          "{suggestion}"
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Information */}
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <span className="text-gray-500 text-lg">ℹ️</span>
                    </div>
                    <div className="ml-3">
                      <h4 className="text-sm font-medium text-gray-800">Chat Information</h4>
                      <div className="mt-1 text-sm text-gray-600">
                        <p>
                          This chat feature provides AI-powered analysis of the shared dataset. 
                          Ask questions to get comprehensive insights, statistical analysis, and visualization recommendations.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}