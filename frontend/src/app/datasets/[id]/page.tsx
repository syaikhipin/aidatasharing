'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useAuth } from '@/components/auth/AuthProvider';
import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { datasetsAPI, dataSharingAPI, organizationsAPI } from '@/lib/api';
import { createApiClient } from '../../../../unified-api-client';
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
  Database,
  UserCheck,
  Upload,
  Edit,
  FileText,
  Sparkles
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
  
  // Initialize unified API client
  const unifiedClient = createApiClient({
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    getAuthToken: () => localStorage.getItem('access_token')
  });
  
  const [dataset, setDataset] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [enhancedPreview, setEnhancedPreview] = useState<any>(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
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
  
  // Ownership transfer state
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [transferForm, setTransferForm] = useState({
    new_owner_id: '',
    new_owner_email: ''
  });
  const [isTransferring, setIsTransferring] = useState(false);
  const [orgUsers, setOrgUsers] = useState<any[]>([]);

  // Edit and Metadata state
  const [showEditModal, setShowEditModal] = useState(false);
  const [showMetadataModal, setShowMetadataModal] = useState(false);
  const [showRenameModal, setShowRenameModal] = useState(false);
  const [showReuploadModal, setShowReuploadModal] = useState(false);
  const [editForm, setEditForm] = useState({
    name: '',
    description: '',
    content: ''
  });
  const [renameForm, setRenameForm] = useState({
    name: '',
    description: ''
  });
  const [reuploadFile, setReuploadFile] = useState<File | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isRenaming, setIsRenaming] = useState(false);
  const [isReuploading, setIsReuploading] = useState(false);
  const [detailedMetadata, setDetailedMetadata] = useState<any>(null);
  const [isLoadingMetadata, setIsLoadingMetadata] = useState(false);

  useEffect(() => {
    fetchDataset();
    fetchSharedLinks();
    fetchEnhancedPreview();
  }, [datasetId]);

  const fetchDataset = async () => {
    try {
      setIsLoading(true);
      setError(null);
      console.log('Fetching dataset with ID:', datasetId);
      const response = await datasetsAPI.getDataset(datasetId);
      console.log('Dataset API response:', response);
      
      // Check if response contains validation error objects (Pydantic errors have type, loc, msg fields)
      if (response && typeof response === 'object' && 
          ('type' in response && 'loc' in response && 'msg' in response)) {
        console.error('Received validation error as dataset:', response);
        setError('Invalid dataset data received. Please try refreshing the page.');
        return;
      }
      
      // Check if response is empty object
      if (!response || (typeof response === 'object' && Object.keys(response).length === 0)) {
        console.error('Received empty response for dataset:', response);
        setError('Dataset not found or no data returned. Please check if the dataset exists.');
        return;
      }
      
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

  const fetchEnhancedPreview = async () => {
    try {
      setIsLoadingPreview(true);
      const response = await datasetsAPI.getDatasetPreview(datasetId);
      
      // Check if response contains validation error objects
      if (response && typeof response === 'object' && ('type' in response || 'loc' in response || 'msg' in response)) {
        console.error('Received validation error as preview:', response);
        setEnhancedPreview({
          type: 'error',
          message: 'Invalid preview data received',
          error: 'Validation error in response'
        });
        return;
      }
      
      // The backend returns the response structure with preview data nested inside
      console.log('Preview API response:', response);
      
      // Extract the actual preview data from the response
      let previewData = response.preview || response;
      
      // Enhanced fallback handling for different preview types
      if (previewData && dataset) {
        // If type is unknown or basic, try to infer type from dataset info
        if (!previewData.type || previewData.type === 'unknown' || previewData.type === 'basic') {
          const fileType = dataset.type?.toLowerCase();
          
          if (fileType === 'csv' && previewData.headers) {
            previewData = {
              ...previewData,
              type: 'tabular',
              format: 'csv'
            };
          } else if (fileType === 'json') {
            previewData = {
              ...previewData,
              type: 'json',
              format: 'json'
            };
          } else if (fileType === 'xlsx' || fileType === 'xls') {
            previewData = {
              ...previewData,
              type: 'excel',
              format: fileType
            };
          }
        }
        
        // Add file size if not present
        if (!previewData.file_size_bytes && dataset.size_bytes) {
          previewData.file_size_bytes = dataset.size_bytes;
        }
        
        // Add row/column counts if available from dataset
        if (!previewData.estimated_total_rows && dataset.row_count) {
          previewData.estimated_total_rows = dataset.row_count;
        }
        
        if (!previewData.total_columns && dataset.column_count) {
          previewData.total_columns = dataset.column_count;
        }
      }
      
      setEnhancedPreview(previewData);
    } catch (error) {
      console.error('Failed to fetch enhanced preview:', error);
      // Set a fallback preview structure
      setEnhancedPreview({
        type: 'error',
        message: 'Preview could not be loaded',
        error: error.response?.data?.detail || error.message
      });
    } finally {
      setIsLoadingPreview(false);
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

  const handleTransferOwnership = async () => {
    if (!transferForm.new_owner_id) {
      alert('Please select a new owner');
      return;
    }

    if (!confirm('Are you sure you want to transfer ownership of this dataset? This action cannot be undone.')) {
      return;
    }

    try {
      setIsTransferring(true);
      await datasetsAPI.transferOwnership(datasetId, parseInt(transferForm.new_owner_id));
      
      setShowTransferModal(false);
      setTransferForm({ new_owner_id: '', new_owner_email: '' });
      
      // Refresh dataset to show new owner
      await fetchDataset();
      
      alert('Dataset ownership transferred successfully!');
      
    } catch (error: any) {
      console.error('Failed to transfer ownership:', error);
      alert(error.response?.data?.detail || 'Failed to transfer ownership');
    } finally {
      setIsTransferring(false);
    }
  };

  const fetchOrgUsers = async () => {
    try {
      if (user?.organization_id) {
        const members = await organizationsAPI.getMembers(user.organization_id);
        // Filter out the current user from the list
        const filteredMembers = members.filter((member: any) => member.user_id !== user.id);
        setOrgUsers(filteredMembers);
      } else {
        setOrgUsers([]);
      }
    } catch (error) {
      console.error('Failed to fetch organization users:', error);
      setOrgUsers([]);
    }
  };

  const openTransferModal = () => {
    fetchOrgUsers();
    setShowTransferModal(true);
  };

  const handleEditDataset = async () => {
    if (!editForm.name.trim()) {
      alert('Dataset name is required');
      return;
    }

    try {
      setIsEditing(true);
      await datasetsAPI.editDataset(datasetId, {
        name: editForm.name,
        description: editForm.description,
        content: editForm.content
      });
      
      setShowEditModal(false);
      await fetchDataset(); // Refresh dataset data
      
    } catch (error: any) {
      console.error('Failed to edit dataset:', error);
      alert(error.response?.data?.detail || 'Failed to edit dataset');
    } finally {
      setIsEditing(false);
    }
  };

  const openEditModal = () => {
    setEditForm({
      name: dataset?.name || '',
      description: dataset?.description || '',
      content: dataset?.content_preview || ''
    });
    setShowEditModal(true);
  };

  const fetchDetailedMetadata = async () => {
    try {
      setIsLoadingMetadata(true);
      const metadata = await datasetsAPI.getDatasetMetadata(datasetId);
      setDetailedMetadata(metadata);
    } catch (error: any) {
      console.error('Failed to fetch metadata:', error);
      alert(error.response?.data?.detail || 'Failed to fetch metadata');
    } finally {
      setIsLoadingMetadata(false);
    }
  };

  const openMetadataModal = () => {
    setShowMetadataModal(true);
    if (!detailedMetadata) {
      fetchDetailedMetadata();
    }
  };

  const handleRenameDataset = async () => {
    if (!renameForm.name.trim()) {
      alert('Dataset name is required');
      return;
    }

    try {
      setIsRenaming(true);
      await datasetsAPI.updateDataset(datasetId, {
        name: renameForm.name,
        description: renameForm.description
      });
      
      setShowRenameModal(false);
      await fetchDataset(); // Refresh dataset data
      
    } catch (error: any) {
      console.error('Failed to rename dataset:', error);
      alert(error.response?.data?.detail || 'Failed to rename dataset');
    } finally {
      setIsRenaming(false);
    }
  };

  const openRenameModal = () => {
    setRenameForm({
      name: dataset?.name || '',
      description: dataset?.description || ''
    });
    setShowRenameModal(true);
  };

  const handleDownload = async (format = 'original') => {
    try {
      setIsLoading(true);
      
      const token = localStorage.getItem('access_token');
      if (!token) {
        alert('Authentication required. Please log in again.');
        return;
      }
      
      // Try direct file download first
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/datasets/${datasetId}/download`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ format })
      });
      
      if (response.ok) {
        const contentType = response.headers.get('Content-Type');
        
        // Check if response is a direct file download
        if (contentType && !contentType.includes('application/json')) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.style.display = 'none';
          a.href = url;
          a.download = `${dataset?.name || 'dataset'}.${format === 'original' ? dataset?.type || 'csv' : format}`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
          return;
        }
        
        // Handle JSON response with download info
        const downloadInfo = await response.json();
        if (downloadInfo.download_url) {
          window.open(downloadInfo.download_url, '_blank');
        } else if (downloadInfo.download_token) {
          alert('Download initiated. Please wait...');
        } else {
          throw new Error('Invalid download response');
        }
      } else if (response.status === 405) {
        // Method not allowed - try GET instead
        const getResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/datasets/${datasetId}/download?format=${format}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (getResponse.ok) {
          const blob = await getResponse.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.style.display = 'none';
          a.href = url;
          a.download = `${dataset?.name || 'dataset'}.${format === 'original' ? dataset?.type || 'csv' : format}`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
        } else {
          throw new Error(`Download failed with status ${getResponse.status}`);
        }
      } else {
        throw new Error(`Download failed with status ${response.status}`);
      }
    } catch (error: any) {
      console.error('Failed to download dataset:', error);
      alert(error.message || 'Failed to download dataset');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReuploadDataset = async () => {
    if (!reuploadFile) {
      alert('Please select a file to upload');
      return;
    }

    try {
      setIsReuploading(true);
      await datasetsAPI.reuploadDataset(datasetId, reuploadFile, {
        name: dataset?.name || '',
        description: dataset?.description || ''
      });
      
      setShowReuploadModal(false);
      setReuploadFile(null);
      await Promise.all([fetchDataset(), fetchEnhancedPreview()]);
      
    } catch (error: any) {
      console.error('Failed to reupload dataset:', error);
      alert(error.response?.data?.detail || 'Failed to reupload dataset');
    } finally {
      setIsReuploading(false);
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
              <div className="relative group">
                <button 
                  onClick={() => handleDownload('original')}
                  className="flex items-center bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download
                </button>
                <div className="absolute right-0 mt-1 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-10 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
                  <div className="py-1">
                    <button
                      onClick={() => handleDownload('original')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      📄 Original Format ({dataset?.type?.toUpperCase()})
                    </button>
                    <button
                      onClick={() => handleDownload('csv')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      📊 CSV Format
                    </button>
                    <button
                      onClick={() => handleDownload('json')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      📋 JSON Format
                    </button>
                  </div>
                </div>
              </div>
              {isOwner && (
                <>
                  <button
                    onClick={openRenameModal}
                    className="flex items-center bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                  >
                    <Edit className="w-4 h-4 mr-2" />
                    Rename
                  </button>
                  <button
                    onClick={() => setShowReuploadModal(true)}
                    className="flex items-center bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    Reupload
                  </button>
                </>
              )}
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
                  className="flex items-center bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium"
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
            {/* Enhanced Preview Section */}
            <div className="bg-white shadow rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Dataset Preview</h3>
                {isLoadingPreview && (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                )}
              </div>
              
              {enhancedPreview ? (
                <div className="space-y-6">
                  {/* Error State */}
                  {enhancedPreview.type === 'error' && (
                    <div className="bg-red-50 border border-red-200 rounded-md p-4">
                      <div className="flex">
                        <div className="flex-shrink-0">
                          <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 18.5c-.77.833.192 2.5 1.732 2.5z" />
                          </svg>
                        </div>
                        <div className="ml-3">
                          <h3 className="text-sm font-medium text-red-800">Preview Error</h3>
                          <div className="mt-2 text-sm text-red-700">
                            <p>{enhancedPreview.message || 'Failed to load preview'}</p>
                            {enhancedPreview.error && (
                              <p className="mt-1 text-xs">{enhancedPreview.error}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* CSV/Tabular Preview */}
                  {(enhancedPreview.type === 'tabular' || (enhancedPreview.headers && dataset?.type === 'csv')) && (
                    <div>
                      <h4 className="text-md font-medium text-gray-900 mb-3 flex items-center">
                        <FileText className="w-4 h-4 mr-2 text-blue-600" />
                        Data Preview ({enhancedPreview.total_rows_in_preview || enhancedPreview.total_rows || dataset?.row_count || 'Unknown'} rows)
                      </h4>
                      
                      {enhancedPreview.headers && (
                        <div className="bg-gray-50 rounded-md border overflow-hidden">
                          <div className="overflow-x-auto max-h-64">
                            <table className="w-full text-xs">
                              <thead className="bg-gray-100">
                                <tr>
                                  {enhancedPreview.headers.map((header: string) => (
                                    <th key={header} className="px-3 py-2 text-left font-medium text-gray-900 border-b">
                                      {header}
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {enhancedPreview.rows && enhancedPreview.rows.length > 0 ? (
                                  enhancedPreview.rows.slice(0, 10).map((row: any, index: number) => (
                                    <tr key={index} className="border-b border-gray-200 hover:bg-gray-50">
                                      {enhancedPreview.headers.map((header: string) => (
                                        <td key={header} className="px-3 py-2 text-gray-700 truncate max-w-32">
                                          {String(row[header] || '')}
                                        </td>
                                      ))}
                                    </tr>
                                  ))
                                ) : (
                                  <tr>
                                    <td colSpan={enhancedPreview.headers.length} className="px-3 py-4 text-center text-gray-500">
                                      <div className="flex flex-col items-center">
                                        <FileText className="w-8 h-8 text-gray-400 mb-2" />
                                        <p>Sample data not available</p>
                                        <p className="text-xs mt-1">Headers detected: {enhancedPreview.headers.length} columns</p>
                                      </div>
                                    </td>
                                  </tr>
                                )}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}
                      
                      {/* Column Types */}
                      {enhancedPreview.column_types && (
                        <div className="mt-3">
                          <h5 className="text-sm font-medium text-gray-900 mb-2">Column Types</h5>
                          <div className="flex flex-wrap gap-2">
                            {Object.entries(enhancedPreview.column_types).map(([col, type]: [string, any]) => (
                              <span key={col} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                {col}: {type}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Display available metadata if no sample data */}
                      {(!enhancedPreview.rows || enhancedPreview.rows.length === 0) && dataset && (
                        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-md">
                          <h5 className="text-sm font-medium text-blue-800 mb-2">Dataset Information</h5>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                            {dataset.row_count && (
                              <div>
                                <span className="font-medium text-blue-700">Rows:</span>
                                <p className="text-blue-900">{dataset.row_count.toLocaleString()}</p>
                              </div>
                            )}
                            {dataset.column_count && (
                              <div>
                                <span className="font-medium text-blue-700">Columns:</span>
                                <p className="text-blue-900">{dataset.column_count}</p>
                              </div>
                            )}
                            {dataset.size_bytes && (
                              <div>
                                <span className="font-medium text-blue-700">Size:</span>
                                <p className="text-blue-900">{formatFileSize(dataset.size_bytes)}</p>
                              </div>
                            )}
                            {dataset.type && (
                              <div>
                                <span className="font-medium text-blue-700">Format:</span>
                                <p className="text-blue-900">{dataset.type.toUpperCase()}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* JSON Preview */}
                  {(enhancedPreview.type === 'json' || dataset?.type === 'json') && (
                    <div>
                      <h4 className="text-md font-medium text-gray-900 mb-3 flex items-center">
                        <FileText className="w-4 h-4 mr-2 text-green-600" />
                        JSON Data Preview
                      </h4>
                      
                      {enhancedPreview.items && enhancedPreview.items.length > 0 && (
                        <div className="bg-gray-50 rounded-md p-4 max-h-64 overflow-y-auto">
                          <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                            {JSON.stringify(enhancedPreview.items.slice(0, 3), null, 2)}
                          </pre>
                          {enhancedPreview.items.length > 3 && (
                            <p className="text-xs text-gray-500 mt-2">
                              ... and {enhancedPreview.items.length - 3} more items
                            </p>
                          )}
                        </div>
                      )}

                      {enhancedPreview.content && (
                        <div className="bg-gray-50 rounded-md p-4 max-h-64 overflow-y-auto">
                          <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                            {JSON.stringify(enhancedPreview.content, null, 2)}
                          </pre>
                        </div>
                      )}
                      
                      {/* Fallback: try to show dataset content_preview if available */}
                      {(!enhancedPreview.items || enhancedPreview.items.length === 0) && 
                       !enhancedPreview.content && 
                       dataset?.content_preview && (
                        <div className="bg-gray-50 rounded-md p-4 max-h-64 overflow-y-auto">
                          <h5 className="text-sm font-medium text-gray-700 mb-2">Content Preview</h5>
                          <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                            {dataset.content_preview}
                          </pre>
                        </div>
                      )}
                      
                      {/* Show structure info if no content available */}
                      {(!enhancedPreview.items || enhancedPreview.items.length === 0) && 
                       !enhancedPreview.content && 
                       !dataset?.content_preview && (
                        <div className="bg-gray-50 rounded-md p-4 text-center">
                          <FileText className="w-8 h-8 text-gray-400 mb-2 mx-auto" />
                          <p className="text-gray-600">JSON content preview not available</p>
                          <p className="text-xs text-gray-500 mt-1">
                            File size: {dataset?.size_bytes ? formatFileSize(dataset.size_bytes) : 'Unknown'}
                          </p>
                        </div>
                      )}

                      {enhancedPreview.common_fields && enhancedPreview.common_fields.length > 0 && (
                        <div className="mt-3">
                          <h5 className="text-sm font-medium text-gray-900 mb-2">Common Fields</h5>
                          <div className="flex flex-wrap gap-2">
                            {enhancedPreview.common_fields.map((field: string) => (
                              <span key={field} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                {field}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Show basic file info for JSON */}
                      {dataset?.type === 'json' && (
                        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-md">
                          <h5 className="text-sm font-medium text-green-800 mb-2">JSON File Information</h5>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                            {dataset.size_bytes && (
                              <div>
                                <span className="font-medium text-green-700">Size:</span>
                                <p className="text-green-900">{formatFileSize(dataset.size_bytes)}</p>
                              </div>
                            )}
                            <div>
                              <span className="font-medium text-green-700">Format:</span>
                              <p className="text-green-900">JSON</p>
                            </div>
                            {dataset.created_at && (
                              <div>
                                <span className="font-medium text-green-700">Created:</span>
                                <p className="text-green-900">{new Date(dataset.created_at).toLocaleDateString()}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Excel Preview */}
                  {enhancedPreview.type === 'excel' && enhancedPreview.sheets && (
                    <div>
                      <h4 className="text-md font-medium text-gray-900 mb-3 flex items-center">
                        <FileText className="w-4 h-4 mr-2 text-orange-600" />
                        Excel Preview ({enhancedPreview.sheet_count} sheets)
                      </h4>
                      
                      {Object.entries(enhancedPreview.sheets).map(([sheetName, sheetData]: [string, any]) => (
                        <div key={sheetName} className="mb-4">
                          <h5 className="text-sm font-medium text-gray-900 mb-2">Sheet: {sheetName}</h5>
                          <div className="bg-gray-50 rounded-md border overflow-hidden">
                            <div className="overflow-x-auto max-h-48">
                              <table className="w-full text-xs">
                                <thead className="bg-gray-100">
                                  <tr>
                                    {sheetData.headers && sheetData.headers.map((header: string) => (
                                      <th key={header} className="px-3 py-2 text-left font-medium text-gray-900 border-b">
                                        {header}
                                      </th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody>
                                  {sheetData.rows && sheetData.rows.slice(0, 5).map((row: any, index: number) => (
                                    <tr key={index} className="border-b border-gray-200 hover:bg-gray-50">
                                      {sheetData.headers && sheetData.headers.map((header: string) => (
                                        <td key={header} className="px-3 py-2 text-gray-700 truncate max-w-32">
                                          {String(row[header] || '')}
                                        </td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Image Preview */}
                  {(enhancedPreview.type === 'image' || enhancedPreview.content_type === 'image') && (
                    <div>
                      <h4 className="text-md font-medium text-gray-900 mb-3 flex items-center">
                        <FileText className="w-4 h-4 mr-2 text-purple-600" />
                        Image Preview
                      </h4>
                      
                      {enhancedPreview.dimensions && (
                        <div className="bg-purple-50 border border-purple-200 rounded-md p-4 mb-4">
                          <h5 className="text-sm font-medium text-purple-800 mb-2">Image Information</h5>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                            <div>
                              <span className="font-medium text-purple-700">Dimensions:</span>
                              <p className="text-purple-900">{enhancedPreview.dimensions.width} × {enhancedPreview.dimensions.height}</p>
                            </div>
                            {enhancedPreview.format && (
                              <div>
                                <span className="font-medium text-purple-700">Format:</span>
                                <p className="text-purple-900">{enhancedPreview.format}</p>
                              </div>
                            )}
                            {enhancedPreview.color_mode && (
                              <div>
                                <span className="font-medium text-purple-700">Color Mode:</span>
                                <p className="text-purple-900">{enhancedPreview.color_mode}</p>
                              </div>
                            )}
                            {enhancedPreview.file_size_bytes && (
                              <div>
                                <span className="font-medium text-purple-700">File Size:</span>
                                <p className="text-purple-900">{formatFileSize(enhancedPreview.file_size_bytes)}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {enhancedPreview.image_metadata && (
                        <div className="bg-gray-50 rounded-md p-4 mb-4">
                          <h5 className="text-sm font-medium text-gray-900 mb-2">Technical Details</h5>
                          <div className="grid grid-cols-2 gap-3 text-sm">
                            {Object.entries(enhancedPreview.image_metadata).map(([key, value]: [string, any]) => (
                              <div key={key}>
                                <span className="font-medium text-gray-700 capitalize">{key.replace('_', ' ')}:</span>
                                <p className="text-gray-900">{String(value)}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {enhancedPreview.exif_data && Object.keys(enhancedPreview.exif_data).length > 0 && (
                        <div className="bg-gray-50 rounded-md p-4">
                          <h5 className="text-sm font-medium text-gray-900 mb-2">EXIF Data</h5>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs max-h-32 overflow-y-auto">
                            {Object.entries(enhancedPreview.exif_data).slice(0, 10).map(([key, value]: [string, any]) => (
                              <div key={key} className="flex justify-between">
                                <span className="font-medium text-gray-600">{key}:</span>
                                <span className="text-gray-800 truncate ml-2">{String(value)}</span>
                              </div>
                            ))}
                          </div>
                          {Object.keys(enhancedPreview.exif_data).length > 10 && (
                            <p className="text-xs text-gray-500 mt-2">
                              ... and {Object.keys(enhancedPreview.exif_data).length - 10} more EXIF fields
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  {/* PDF Preview */}
                  {enhancedPreview.type === 'pdf' && (
                    <div>
                      <h4 className="text-md font-medium text-gray-900 mb-3 flex items-center">
                        <FileText className="w-4 h-4 mr-2 text-red-600" />
                        PDF Preview ({enhancedPreview.page_count} pages)
                      </h4>
                      
                      {enhancedPreview.pages && enhancedPreview.pages.length > 0 && (
                        <div className="space-y-3">
                          {enhancedPreview.pages.map((page: any, index: number) => (
                            <div key={index} className="bg-gray-50 rounded-md p-4">
                              <h5 className="text-sm font-medium text-gray-900 mb-2">
                                Page {page.page_number}
                              </h5>
                              <div className="text-sm text-gray-700 max-h-32 overflow-y-auto">
                                <pre className="whitespace-pre-wrap font-mono">
                                  {page.text_content || 'No extractable text found'}
                                </pre>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                      
                      {enhancedPreview.error && (
                        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                          <p className="text-sm text-yellow-800">{enhancedPreview.error}</p>
                          {enhancedPreview.note && (
                            <p className="text-xs text-yellow-700 mt-1">{enhancedPreview.note}</p>
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Basic Statistics */}
                  {enhancedPreview.basic_stats && (
                    <div>
                      <h4 className="text-md font-medium text-gray-900 mb-3">Statistics</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-blue-50 rounded-md p-3">
                          <span className="text-sm font-medium text-blue-700">Rows</span>
                          <p className="text-sm text-blue-900 mt-1">{enhancedPreview.basic_stats.row_count?.toLocaleString()}</p>
                        </div>
                        <div className="bg-blue-50 rounded-md p-3">
                          <span className="text-sm font-medium text-blue-700">Columns</span>
                          <p className="text-sm text-blue-900 mt-1">{enhancedPreview.basic_stats.column_count}</p>
                        </div>
                        {enhancedPreview.basic_stats.numeric_columns?.length > 0 && (
                          <div className="bg-blue-50 rounded-md p-3">
                            <span className="text-sm font-medium text-blue-700">Numeric Cols</span>
                            <p className="text-sm text-blue-900 mt-1">{enhancedPreview.basic_stats.numeric_columns.length}</p>
                          </div>
                        )}
                        {enhancedPreview.basic_stats.text_columns?.length > 0 && (
                          <div className="bg-blue-50 rounded-md p-3">
                            <span className="text-sm font-medium text-blue-700">Text Cols</span>
                            <p className="text-sm text-blue-900 mt-1">{enhancedPreview.basic_stats.text_columns.length}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* General File Information */}
                  {(enhancedPreview.estimated_total_rows || enhancedPreview.total_columns || enhancedPreview.file_size_bytes) && (
                    <div>
                      <h4 className="text-md font-medium text-gray-900 mb-3">File Information</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {enhancedPreview.estimated_total_rows && (
                          <div className="bg-gray-50 rounded-md p-3">
                            <span className="text-sm font-medium text-gray-700">Total Rows</span>
                            <p className="text-sm text-gray-900 mt-1">{enhancedPreview.estimated_total_rows?.toLocaleString()}</p>
                          </div>
                        )}
                        {enhancedPreview.total_columns && (
                          <div className="bg-gray-50 rounded-md p-3">
                            <span className="text-sm font-medium text-gray-700">Columns</span>
                            <p className="text-sm text-gray-900 mt-1">{enhancedPreview.total_columns}</p>
                          </div>
                        )}
                        {enhancedPreview.file_size_bytes && (
                          <div className="bg-gray-50 rounded-md p-3">
                            <span className="text-sm font-medium text-gray-700">File Size</span>
                            <p className="text-sm text-gray-900 mt-1">{formatFileSize(enhancedPreview.file_size_bytes)}</p>
                          </div>
                        )}
                        {enhancedPreview.format && (
                          <div className="bg-gray-50 rounded-md p-3">
                            <span className="text-sm font-medium text-gray-700">Format</span>
                            <p className="text-sm text-gray-900 mt-1">{enhancedPreview.format.toUpperCase()}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Fallback for other types */}
                  {enhancedPreview.basic_info && enhancedPreview.type === 'basic' && (
                    <div>
                      <h4 className="text-md font-medium text-gray-900 mb-3">Basic Information</h4>
                      <div className="bg-gray-50 rounded-md p-4">
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="font-medium text-gray-700">Name:</span>
                            <p className="text-gray-900">{enhancedPreview.basic_info.name}</p>
                          </div>
                          <div>
                            <span className="font-medium text-gray-700">Size:</span>
                            <p className="text-gray-900">{enhancedPreview.basic_info.size_bytes ? formatFileSize(enhancedPreview.basic_info.size_bytes) : 'Unknown'}</p>
                          </div>
                          {enhancedPreview.basic_info.row_count && (
                            <div>
                              <span className="font-medium text-gray-700">Rows:</span>
                              <p className="text-gray-900">{enhancedPreview.basic_info.row_count.toLocaleString()}</p>
                            </div>
                          )}
                          {enhancedPreview.basic_info.column_count && (
                            <div>
                              <span className="font-medium text-gray-700">Columns:</span>
                              <p className="text-gray-900">{enhancedPreview.basic_info.column_count}</p>
                            </div>
                          )}
                        </div>
                        {enhancedPreview.message && (
                          <p className="text-sm text-gray-600 mt-3">{enhancedPreview.message}</p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ) : !isLoadingPreview && (
                <div className="text-center py-8">
                  <p className="text-gray-500">Preview not available</p>
                  <button
                    onClick={fetchEnhancedPreview}
                    className="mt-2 text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    Try loading again
                  </button>
                </div>
              )}
            </div>

            {/* Document Preview (for document datasets) */}
            {dataset.document_type && (
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Document Preview</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div>
                    <span className="text-sm font-medium text-gray-500">Document Type</span>
                    <p className="mt-1 text-sm text-gray-900 uppercase">{dataset.document_type}</p>
                  </div>
                  {dataset.page_count && (
                    <div>
                      <span className="text-sm font-medium text-gray-500">Pages</span>
                      <p className="mt-1 text-sm text-gray-900">{dataset.page_count}</p>
                    </div>
                  )}
                  {dataset.word_count && (
                    <div>
                      <span className="text-sm font-medium text-gray-500">Words</span>
                      <p className="mt-1 text-sm text-gray-900">{dataset.word_count.toLocaleString()}</p>
                    </div>
                  )}
                  {dataset.text_extraction_method && (
                    <div>
                      <span className="text-sm font-medium text-gray-500">Extraction</span>
                      <p className="mt-1 text-sm text-gray-900">{dataset.text_extraction_method}</p>
                    </div>
                  )}
                </div>
                {dataset.extracted_text && (
                  <div>
                    <span className="text-sm font-medium text-gray-500 mb-2 block">Text Preview</span>
                    <div className="bg-gray-50 rounded-md p-4 max-h-64 overflow-y-auto">
                      <pre className="whitespace-pre-wrap text-sm text-gray-700">
                        {dataset.extracted_text.substring(0, 1000)}
                        {dataset.extracted_text.length > 1000 && '...'}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Dataset Info with Edit and Metadata Features */}
            <div className="bg-white shadow rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Dataset Information</h3>
                <div className="flex space-x-2">
                  <button
                    onClick={openMetadataModal}
                    className="flex items-center px-3 py-1.5 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100"
                  >
                    <Database className="w-4 h-4 mr-1.5" />
                    View Metadata
                  </button>
                  {isOwner && (
                    <button
                      onClick={openEditModal}
                      className="flex items-center px-3 py-1.5 text-sm font-medium text-green-700 bg-green-50 border border-green-200 rounded-md hover:bg-green-100"
                    >
                      <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                      Edit Dataset
                    </button>
                  )}
                </div>
              </div>
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
                <button 
                  onClick={() => handleDownload('original')}
                  className="w-full flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  <Download className="w-5 h-5 text-green-600 mr-3" />
                  <div className="text-left">
                    <p className="text-sm font-medium text-gray-900">Download Dataset</p>
                    <p className="text-xs text-gray-500">Export as CSV, JSON, or original format</p>
                  </div>
                </button>

                {isOwner && (
                  <>
                    <button
                      onClick={openRenameModal}
                      className="w-full flex items-center p-3 border border-gray-200 rounded-lg hover:bg-blue-50"
                    >
                      <Edit className="w-5 h-5 text-blue-600 mr-3" />
                      <div className="text-left">
                        <p className="text-sm font-medium text-gray-900">Rename Dataset</p>
                        <p className="text-xs text-gray-500">Change name and description</p>
                      </div>
                    </button>

                    <button
                      onClick={() => setShowReuploadModal(true)}
                      className="w-full flex items-center p-3 border border-gray-200 rounded-lg hover:bg-orange-50"
                    >
                      <Upload className="w-5 h-5 text-orange-600 mr-3" />
                      <div className="text-left">
                        <p className="text-sm font-medium text-gray-900">Reupload File</p>
                        <p className="text-xs text-gray-500">Replace with new file</p>
                      </div>
                    </button>

                    <button
                      onClick={openTransferModal}
                      className="w-full flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                    >
                      <UserCheck className="w-5 h-5 text-orange-600 mr-3" />
                      <div className="text-left">
                        <p className="text-sm font-medium text-gray-900">Transfer Ownership</p>
                        <p className="text-xs text-gray-500">Transfer to another user</p>
                      </div>
                    </button>
                  </>
                )}

                <Link
                  href={`/models/create?dataset_id=${datasetId}`}
                  className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  <Database className="w-5 h-5 text-indigo-600 mr-3" />
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
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
            <div className="relative mx-auto p-5 border w-96 shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
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

        {/* Transfer Ownership Modal */}
        {showTransferModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
            <div className="relative mx-auto p-5 border w-96 shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Transfer Dataset Ownership</h3>
                
                <div className="space-y-4">
                  <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                    <div className="flex">
                      <div className="flex-shrink-0">
                        <svg className="h-5 w-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 18.5c-.77.833.192 2.5 1.732 2.5z" />
                        </svg>
                      </div>
                      <div className="ml-3">
                        <p className="text-sm text-yellow-800">
                          <strong>Warning:</strong> This action cannot be undone. You will lose ownership of this dataset.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Select New Owner
                    </label>
                    <select
                      value={transferForm.new_owner_id}
                      onChange={(e) => {
                        const selectedUser = orgUsers.find(u => u.id.toString() === e.target.value);
                        setTransferForm({
                          new_owner_id: e.target.value,
                          new_owner_email: selectedUser?.email || ''
                        });
                      }}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">Select a user...</option>
                      {orgUsers.filter(u => u.id !== user?.id).map(orgUser => (
                        <option key={orgUser.id} value={orgUser.id}>
                          {orgUser.full_name || 'No name'} ({orgUser.email}) - {orgUser.role}
                        </option>
                      ))}
                    </select>
                  </div>

                  {transferForm.new_owner_email && (
                    <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                      <p className="text-sm text-blue-800">
                        Dataset ownership will be transferred to: <strong>{transferForm.new_owner_email}</strong>
                      </p>
                    </div>
                  )}
                </div>

                <div className="flex space-x-3 mt-6">
                  <button
                    onClick={() => {
                      setShowTransferModal(false);
                      setTransferForm({ new_owner_id: '', new_owner_email: '' });
                    }}
                    className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 border border-gray-300 rounded-md hover:bg-gray-300"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleTransferOwnership}
                    disabled={isTransferring || !transferForm.new_owner_id}
                    className="flex-1 px-4 py-2 text-sm font-medium text-white bg-orange-600 border border-transparent rounded-md hover:bg-orange-700 disabled:opacity-50"
                  >
                    {isTransferring ? 'Transferring...' : 'Transfer Ownership'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Edit Dataset Modal */}
        {showEditModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
            <div className="relative mx-auto p-5 border w-[600px] shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Edit Dataset</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Dataset Name
                    </label>
                    <input
                      type="text"
                      value={editForm.name}
                      onChange={(e) => setEditForm({...editForm, name: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Description
                    </label>
                    <textarea
                      value={editForm.description}
                      onChange={(e) => setEditForm({...editForm, description: e.target.value})}
                      rows={3}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  {dataset?.type === 'csv' || dataset?.type === 'json' ? (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Content Preview
                      </label>
                      <textarea
                        value={editForm.content}
                        onChange={(e) => setEditForm({...editForm, content: e.target.value})}
                        rows={8}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        placeholder="Dataset content..."
                      />
                    </div>
                  ) : (
                    <div className="bg-gray-50 border border-gray-200 rounded-md p-3">
                      <p className="text-sm text-gray-600">
                        Content editing is only available for CSV and JSON datasets.
                      </p>
                    </div>
                  )}
                </div>

                <div className="flex space-x-3 mt-6">
                  <button
                    onClick={() => setShowEditModal(false)}
                    className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 border border-gray-300 rounded-md hover:bg-gray-300"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleEditDataset}
                    disabled={isEditing || !editForm.name.trim()}
                    className="flex-1 px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 disabled:opacity-50"
                  >
                    {isEditing ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Metadata Modal */}
        {showMetadataModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
            <div className="relative mx-auto p-5 border w-[700px] shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Detailed Metadata</h3>
                
                {isLoadingMetadata ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  </div>
                ) : detailedMetadata ? (
                  <div className="space-y-6">
                    {/* Basic Information */}
                    <div>
                      <h4 className="text-md font-medium text-gray-900 mb-3">Basic Information</h4>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium text-gray-500">Name:</span>
                          <p className="text-gray-900">{detailedMetadata.name}</p>
                        </div>
                        <div>
                          <span className="font-medium text-gray-500">Type:</span>
                          <p className="text-gray-900">{detailedMetadata.type?.toUpperCase()}</p>
                        </div>
                        <div>
                          <span className="font-medium text-gray-500">Status:</span>
                          <p className="text-gray-900">{detailedMetadata.status}</p>
                        </div>
                        <div>
                          <span className="font-medium text-gray-500">Size:</span>
                          <p className="text-gray-900">{detailedMetadata.size_bytes ? formatFileSize(detailedMetadata.size_bytes) : 'Unknown'}</p>
                        </div>
                        <div>
                          <span className="font-medium text-gray-500">Created:</span>
                          <p className="text-gray-900">{new Date(detailedMetadata.created_at).toLocaleString()}</p>
                        </div>
                        <div>
                          <span className="font-medium text-gray-500">Modified:</span>
                          <p className="text-gray-900">{new Date(detailedMetadata.updated_at).toLocaleString()}</p>
                        </div>
                      </div>
                    </div>

                    {/* AI Processing */}
                    <div>
                      <h4 className="text-md font-medium text-gray-900 mb-3">AI Processing</h4>
                      <div className="grid grid-cols-1 gap-4 text-sm">
                        <div>
                          <span className="font-medium text-gray-500">Processing Status:</span>
                          <p className="text-gray-900">{detailedMetadata.ai_processing_status}</p>
                        </div>
                        {detailedMetadata.ai_summary && (
                          <div>
                            <span className="font-medium text-gray-500">AI Summary:</span>
                            <p className="text-gray-900 mt-1 p-3 bg-blue-50 rounded-md">{detailedMetadata.ai_summary}</p>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Organization */}
                    {detailedMetadata.organization && (
                      <div>
                        <h4 className="text-md font-medium text-gray-900 mb-3">Organization</h4>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="font-medium text-gray-500">Organization:</span>
                            <p className="text-gray-900">{detailedMetadata.organization.name}</p>
                          </div>
                          <div>
                            <span className="font-medium text-gray-500">Owner:</span>
                            <p className="text-gray-900">{detailedMetadata.owner?.full_name || 'Unknown'}</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* File Information */}
                    {detailedMetadata.source_url && (
                      <div>
                        <h4 className="text-md font-medium text-gray-900 mb-3">File Information</h4>
                        <div className="text-sm">
                          <div>
                            <span className="font-medium text-gray-500">File Path:</span>
                            <p className="text-gray-900 break-all">{detailedMetadata.source_url}</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Sharing Information */}
                    <div>
                      <h4 className="text-md font-medium text-gray-900 mb-3">Sharing</h4>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium text-gray-500">Sharing Level:</span>
                          <p className="text-gray-900">{detailedMetadata.sharing_level || 'private'}</p>
                        </div>
                        <div>
                          <span className="font-medium text-gray-500">Public Share:</span>
                          <p className="text-gray-900">{detailedMetadata.is_public ? 'Enabled' : 'Disabled'}</p>
                        </div>
                        {detailedMetadata.share_expires_at && (
                          <>
                            <div>
                              <span className="font-medium text-gray-500">Share Expires:</span>
                              <p className="text-gray-900">{new Date(detailedMetadata.share_expires_at).toLocaleString()}</p>
                            </div>
                            <div>
                              <span className="font-medium text-gray-500">Share Views:</span>
                              <p className="text-gray-900">{detailedMetadata.share_view_count || 0}</p>
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-gray-600">Failed to load metadata</p>
                  </div>
                )}

                <div className="flex justify-end mt-6">
                  <button
                    onClick={() => setShowMetadataModal(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 border border-gray-300 rounded-md hover:bg-gray-300"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Rename Dataset Modal */}
        {showRenameModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
            <div className="relative mx-auto p-5 border w-96 shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Rename Dataset</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Dataset Name
                    </label>
                    <input
                      type="text"
                      value={renameForm.name}
                      onChange={(e) => setRenameForm({...renameForm, name: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Description
                    </label>
                    <textarea
                      value={renameForm.description}
                      onChange={(e) => setRenameForm({...renameForm, description: e.target.value})}
                      rows={3}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>

                <div className="flex space-x-3 mt-6">
                  <button
                    onClick={() => setShowRenameModal(false)}
                    className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 border border-gray-300 rounded-md hover:bg-gray-300"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleRenameDataset}
                    disabled={isRenaming || !renameForm.name.trim()}
                    className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {isRenaming ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Reupload Dataset Modal */}
        {showReuploadModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
            <div className="relative mx-auto p-5 border w-96 shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Reupload Dataset File</h3>
                
                <div className="space-y-4">
                  <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                    <div className="flex">
                      <div className="flex-shrink-0">
                        <svg className="h-5 w-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 18.5c-.77.833.192 2.5 1.732 2.5z" />
                        </svg>
                      </div>
                      <div className="ml-3">
                        <p className="text-sm text-yellow-800">
                          <strong>Warning:</strong> This will replace the current dataset file. Make sure the new file has the same structure.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Select New File
                    </label>
                    <input
                      type="file"
                      onChange={(e) => setReuploadFile(e.target.files?.[0] || null)}
                      accept=".csv,.json,.xlsx,.xls"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Supported formats: CSV, JSON, Excel (.xlsx, .xls)
                    </p>
                  </div>

                  {reuploadFile && (
                    <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                      <p className="text-sm text-blue-800">
                        Selected file: <strong>{reuploadFile.name}</strong> ({formatFileSize(reuploadFile.size)})
                      </p>
                    </div>
                  )}
                </div>

                <div className="flex space-x-3 mt-6">
                  <button
                    onClick={() => {
                      setShowReuploadModal(false);
                      setReuploadFile(null);
                    }}
                    className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 border border-gray-300 rounded-md hover:bg-gray-300"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleReuploadDataset}
                    disabled={isReuploading || !reuploadFile}
                    className="flex-1 px-4 py-2 text-sm font-medium text-white bg-orange-600 border border-transparent rounded-md hover:bg-orange-700 disabled:opacity-50"
                  >
                    {isReuploading ? 'Uploading...' : 'Reupload File'}
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