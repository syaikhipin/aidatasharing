'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useAuth } from '@/components/auth/AuthProvider';
import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { datasetsAPI, dataSharingAPI } from '@/lib/api';
import Link from 'next/link';
import { 
  Download, 
  Share2, 
  Link as LinkIcon, 
  Clock, 
  Eye, 
  MessageSquare, 
  Shield, 
  Copy, 
  Trash2, 
  Power, 
  PowerOff,
  ExternalLink,
  Calendar,
  Users,
  Database
} from 'lucide-react';

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export default function DatasetDetailPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <DatasetDetailContent />
      </DashboardLayout>
    </ProtectedRoute>
  );
}

function DatasetDetailContent() {
  const { user } = useAuth();
  const params = useParams();
  const router = useRouter();
  const datasetId = parseInt(params.id as string);
  
  const [dataset, setDataset] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [chatMessage, setChatMessage] = useState('');
  const [chatResponse, setChatResponse] = useState<any>(null);
  const [isChatting, setIsChatting] = useState(false);
  
  // Sharing state
  const [shareLinks, setShareLinks] = useState<any[]>([]);
  const [showCreateShareModal, setShowCreateShareModal] = useState(false);
  const [shareForm, setShareForm] = useState({
    expires_in_hours: 24,
    password: '',
    enable_chat: true
  });
  const [isCreatingShare, setIsCreatingShare] = useState(false);
  const [isLoadingShares, setIsLoadingShares] = useState(false);

  useEffect(() => {
    fetchDataset();
    fetchSharedLinks();
  }, [datasetId]);

  const fetchDataset = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await datasetsAPI.getDataset(datasetId);
      setDataset(response);
    } catch (error: any) {
      console.error('Failed to fetch dataset:', error);
      setError(error.response?.data?.detail || 'Failed to fetch dataset');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchSharedLinks = async () => {
    try {
      setIsLoadingShares(true);
      const response = await dataSharingAPI.getMySharedDatasets();
      const datasetShares = response.filter((share: any) => share.id === datasetId);
      setShareLinks(datasetShares);
    } catch (error) {
      console.error('Failed to fetch shared links:', error);
    } finally {
      setIsLoadingShares(false);
    }
  };

  const handleCreateShareLink = async () => {
    try {
      setIsCreatingShare(true);
      const response = await dataSharingAPI.createShareLink({
        dataset_id: datasetId,
        expires_in_hours: shareForm.expires_in_hours || undefined,
        password: shareForm.password || undefined,
        enable_chat: shareForm.enable_chat
      });
      
      setShowCreateShareModal(false);
      setShareForm({
        expires_in_hours: 24,
        password: '',
        enable_chat: true
      });
      
      // Refresh dataset and share links
      await Promise.all([fetchDataset(), fetchSharedLinks()]);
      
    } catch (error: any) {
      console.error('Failed to create share link:', error);
      alert(error.response?.data?.detail || 'Failed to create share link');
    } finally {
      setIsCreatingShare(false);
    }
  };

  const handleDisableSharing = async () => {
    if (!confirm('Are you sure you want to disable sharing for this dataset? This will invalidate all existing share links.')) {
      return;
    }

    try {
      await dataSharingAPI.disableSharing(datasetId);
      await Promise.all([fetchDataset(), fetchSharedLinks()]);
    } catch (error: any) {
      console.error('Failed to disable sharing:', error);
      alert(error.response?.data?.detail || 'Failed to disable sharing');
    }
  };

  const copyShareLink = (shareToken: string) => {
    const shareUrl = `${window.location.origin}/shared/${shareToken}`;
    navigator.clipboard.writeText(shareUrl);
    alert('Share link copied to clipboard!');
  };

  const handleChat = async () => {
    if (!chatMessage.trim()) return;
    
    try {
      setIsChatting(true);
      const response = await datasetsAPI.chatWithDataset(datasetId, chatMessage);
      setChatResponse(response);
      setChatMessage('');
    } catch (error: any) {
      console.error('Chat failed:', error);
      setChatResponse({
        error: true,
        answer: error.response?.data?.detail || 'Failed to connect to chat service'
      });
    } finally {
      setIsChatting(false);
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
        <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 18.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error loading dataset</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
                </div>
                <div className="mt-3">
                  <Link href="/datasets" className="text-sm font-medium text-red-800 hover:text-red-600">
                    ← Back to datasets
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!dataset) {
    return (
      <div className="py-6">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8">
          <div className="text-center">
            <h3 className="text-lg font-medium text-gray-900">Dataset not found</h3>
            <p className="mt-1 text-sm text-gray-600">
              The dataset you're looking for doesn't exist or you don't have access to it.
            </p>
            <div className="mt-6">
              <Link
                href="/datasets"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                ← Back to datasets
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const isOwner = dataset.owner_id === user?.id;

  return (
    <div className="py-6">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 md:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <Link
                href="/datasets"
                className="text-sm text-gray-500 hover:text-gray-700 mb-2 inline-block"
              >
                ← Back to datasets
              </Link>
              <h1 className="text-2xl font-bold text-gray-900">{dataset.name}</h1>
              <p className="mt-1 text-sm text-gray-600">
                {dataset.description || 'No description provided'}
              </p>
            </div>
            <div className="flex space-x-3">
              <button className="flex items-center bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium">
                <Download className="w-4 h-4 mr-2" />
                Download
              </button>
              <Link
                href={`/datasets/${datasetId}/chat`}
                className="flex items-center bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                <MessageSquare className="w-4 h-4 mr-2" />
                Chat
              </Link>
              {isOwner && (
                <button 
                  onClick={() => setShowCreateShareModal(true)}
                  className="flex items-center bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                >
                  <Share2 className="w-4 h-4 mr-2" />
                  Share
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Dataset Info */}
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Dataset Information</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div>
                  <span className="text-sm font-medium text-gray-500">Type</span>
                  <p className="mt-1 text-sm text-gray-900">{dataset.type?.toUpperCase()}</p>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500">Sharing Level</span>
                  <p className="mt-1 text-sm text-gray-900">{dataset.sharing_level}</p>
                </div>
                {dataset.size_bytes && (
                  <div>
                    <span className="text-sm font-medium text-gray-500">Size</span>
                    <p className="mt-1 text-sm text-gray-900">{formatFileSize(dataset.size_bytes)}</p>
                  </div>
                )}
                <div>
                  <span className="text-sm font-medium text-gray-500">Created</span>
                  <p className="mt-1 text-sm text-gray-900">
                    {new Date(dataset.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500">Owner</span>
                  <p className="mt-1 text-sm text-gray-900">{dataset.owner?.full_name || 'Unknown'}</p>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500">Status</span>
                  <p className="mt-1 text-sm text-gray-900">
                    <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                      {dataset.status}
                    </span>
                  </p>
                </div>
                {dataset.row_count && (
                  <div>
                    <span className="text-sm font-medium text-gray-500">Rows</span>
                    <p className="mt-1 text-sm text-gray-900">{dataset.row_count.toLocaleString()}</p>
                  </div>
                )}
                {dataset.column_count && (
                  <div>
                    <span className="text-sm font-medium text-gray-500">Columns</span>
                    <p className="mt-1 text-sm text-gray-900">{dataset.column_count}</p>
                  </div>
                )}
              </div>
            </div>

            {/* AI Chat */}
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Chat with AI about this dataset</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Ask a question about your data
                  </label>
                  <div className="flex space-x-3">
                    <input
                      type="text"
                      value={chatMessage}
                      onChange={(e) => setChatMessage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleChat()}
                      placeholder="What insights can you provide about this dataset?"
                      className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                    <button
                      onClick={handleChat}
                      disabled={!chatMessage.trim() || isChatting}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isChatting ? 'Asking...' : 'Ask AI'}
                    </button>
                  </div>
                </div>

                {chatResponse && (
                  <div className={`p-4 rounded-md ${chatResponse.error ? 'bg-red-50 border border-red-200' : 'bg-blue-50 border border-blue-200'}`}>
                    <div className="flex">
                      <div className="flex-shrink-0">
                        {chatResponse.error ? (
                          <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 18.5c-.77.833.192 2.5 1.732 2.5z" />
                          </svg>
                        ) : (
                          <svg className="h-5 w-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                          </svg>
                        )}
                      </div>
                      <div className="ml-3">
                        <h4 className={`text-sm font-medium ${chatResponse.error ? 'text-red-800' : 'text-blue-800'}`}>
                          {chatResponse.error ? 'Error' : 'AI Response'}
                        </h4>
                        <div className={`mt-2 text-sm ${chatResponse.error ? 'text-red-700' : 'text-blue-700'}`}>
                          <p className="whitespace-pre-wrap">{chatResponse.answer}</p>
                        </div>
                        {!chatResponse.error && chatResponse.model && (
                          <div className="mt-2 text-xs text-blue-600">
                            Model: {chatResponse.model} | Tokens: {chatResponse.tokens_used || 0}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                <div className="text-xs text-gray-500">
                  <p>💡 Try asking questions like:</p>
                  <ul className="mt-1 list-disc list-inside">
                    <li>What insights can you provide about this dataset?</li>
                    <li>How many records are in this dataset?</li>
                    <li>What are the key patterns in the data?</li>
                    <li>Can you summarize the main findings?</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1">
            {/* Sharing Management */}
            {isOwner && (
              <div className="bg-white shadow rounded-lg p-6 mb-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Data Sharing</h3>
                  {dataset.public_share_enabled && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      <div className="w-1.5 h-1.5 bg-green-400 rounded-full mr-1"></div>
                      Active
                    </span>
                  )}
                </div>

                {dataset.public_share_enabled ? (
                  <div className="space-y-4">
                    <div className="bg-green-50 border border-green-200 rounded-md p-3">
                      <div className="flex items-center">
                        <Shield className="h-4 w-4 text-green-600 mr-2" />
                        <span className="text-sm font-medium text-green-800">Sharing is enabled</span>
                      </div>
                      {dataset.share_token && (
                        <div className="mt-2">
                          <div className="flex items-center space-x-2">
                            <input
                              type="text"
                              value={`${window.location.origin}/shared/${dataset.share_token}`}
                              readOnly
                              className="flex-1 text-xs bg-white border border-green-300 rounded px-2 py-1"
                            />
                            <button
                              onClick={() => copyShareLink(dataset.share_token)}
                              className="text-green-600 hover:text-green-800"
                            >
                              <Copy className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => window.open(`/shared/${dataset.share_token}`, '_blank')}
                              className="text-green-600 hover:text-green-800"
                            >
                              <ExternalLink className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="flex space-x-2">
                      <button
                        onClick={handleDisableSharing}
                        className="flex-1 flex items-center justify-center px-3 py-2 border border-red-300 text-red-700 rounded-md hover:bg-red-50 text-sm"
                      >
                        <PowerOff className="w-4 h-4 mr-1" />
                        Disable
                      </button>
                    </div>

                    {dataset.share_expires_at && (
                      <div className="text-xs text-gray-500 flex items-center">
                        <Clock className="w-3 h-3 mr-1" />
                        Expires: {new Date(dataset.share_expires_at).toLocaleString()}
                      </div>
                    )}

                    {dataset.share_view_count > 0 && (
                      <div className="text-xs text-gray-500 flex items-center">
                        <Eye className="w-3 h-3 mr-1" />
                        Views: {dataset.share_view_count}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-4">
                    <p className="text-sm text-gray-600">
                      Create a shareable link to allow others to access and chat with this dataset.
                    </p>
                    <button
                      onClick={() => setShowCreateShareModal(true)}
                      className="w-full flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                    >
                      <Share2 className="w-4 h-4 mr-2" />
                      Create Share Link
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Quick Actions */}
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <Link
                  href={`/datasets/${datasetId}/chat`}
                  className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  <MessageSquare className="w-5 h-5 text-purple-600 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">Chat with Data</p>
                    <p className="text-xs text-gray-500">Ask questions about this dataset</p>
                  </div>
                </Link>

                <button className="w-full flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
                  <Download className="w-5 h-5 text-green-600 mr-3" />
                  <div className="text-left">
                    <p className="text-sm font-medium text-gray-900">Download Dataset</p>
                    <p className="text-xs text-gray-500">Export as CSV or JSON</p>
                  </div>
                </button>

                <Link
                  href={`/models/create?dataset_id=${datasetId}`}
                  className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  <Database className="w-5 h-5 text-blue-600 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">Create AI Model</p>
                    <p className="text-xs text-gray-500">Build ML models from this data</p>
                  </div>
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Create Share Link Modal */}
        {showCreateShareModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Create Share Link</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Expires in (hours)
                    </label>
                    <input
                      type="number"
                      value={shareForm.expires_in_hours}
                      onChange={(e) => setShareForm({...shareForm, expires_in_hours: parseInt(e.target.value) || 0})}
                      placeholder="24"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Leave empty for no expiration</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Password (optional)
                    </label>
                    <input
                      type="password"
                      value={shareForm.password}
                      onChange={(e) => setShareForm({...shareForm, password: e.target.value})}
                      placeholder="Optional password protection"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="enable_chat"
                      checked={shareForm.enable_chat}
                      onChange={(e) => setShareForm({...shareForm, enable_chat: e.target.checked})}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="enable_chat" className="ml-2 block text-sm text-gray-900">
                      Enable AI chat for shared dataset
                    </label>
                  </div>
                </div>

                <div className="flex space-x-3 mt-6">
                  <button
                    onClick={() => setShowCreateShareModal(false)}
                    className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 border border-gray-300 rounded-md hover:bg-gray-300"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCreateShareLink}
                    disabled={isCreatingShare}
                    className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {isCreatingShare ? 'Creating...' : 'Create Link'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 