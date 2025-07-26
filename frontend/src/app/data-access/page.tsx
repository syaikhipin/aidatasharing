'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useAuth } from '@/components/auth/AuthProvider';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { datasetsAPI, dataAccessAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface Dataset {
  id: number;
  name: string;
  description?: string;
  type: string;
  sharing_level: string;
  size_bytes?: number;
  created_at: string;
  owner_name?: string;
  organization_name?: string;
  can_access: boolean;
}

interface AccessRequest {
  id: number;
  dataset_id: number;
  dataset_name: string;
  requester_name: string;
  request_type: string;
  status: string;
  created_at: string;
  purpose?: string;
}

export default function DataAccessPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <DataAccessContent />
      </DashboardLayout>
    </ProtectedRoute>
  );
}

function DataAccessContent() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'browse' | 'requests'>('browse');
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [accessRequests, setAccessRequests] = useState<AccessRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSharingLevel, setSelectedSharingLevel] = useState('all');

  useEffect(() => {
    fetchData();
    fetchAccessRequests();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch accessible datasets using the data-access API
      const datasetsResponse = await dataAccessAPI.getAccessibleDatasets();
      console.log('Raw accessible datasets response:', datasetsResponse);
      
      // Process datasets from data-access API (already filtered for accessibility)
      const processedDatasets = (datasetsResponse || []).map((dataset: any) => {
        return {
          ...dataset,
          can_access: dataset.has_access,
          owner_name: dataset.owner,
          is_own_dataset: false, // Data-access API only returns others' datasets
          can_request_access: dataset.can_request,
          sharing_level: dataset.sharing_level.toLowerCase() // Normalize to lowercase for display
        };
      });
      
      console.log('Processed accessible datasets:', processedDatasets);
      
      // No need to filter since data-access API already returns only accessible datasets
      setDatasets(processedDatasets);
      
      // Mock access requests since we don't have this endpoint yet
      setAccessRequests([]);
      
    } catch (error) {
      console.error('Error fetching data:', error);
      setDatasets([]);
      setAccessRequests([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRequestAccess = async (datasetId: number) => {
    try {
      const purpose = prompt('Please enter the purpose for accessing this dataset:');
      if (!purpose) return;
      
      const justification = prompt('Please provide justification for this access request:');
      if (!justification) return;
      
      const response = await dataAccessAPI.createAccessRequest({
        dataset_id: datasetId,
        request_type: 'access',
        requested_level: 'read',
        purpose: purpose,
        justification: justification,
        urgency: 'medium',
        category: 'analysis'
      });
      
      alert('Access request submitted successfully! You will be notified when it is reviewed.');
      
      // Refresh the access requests
      fetchAccessRequests();
      
    } catch (error) {
      console.error('Error requesting access:', error);
      alert('Failed to submit access request. Please try again.');
    }
  };

  const fetchAccessRequests = async () => {
    try {
      const requests = await dataAccessAPI.getAccessRequests({ my_requests: true });
      setAccessRequests(requests);
    } catch (error) {
      console.error('Error fetching access requests:', error);
    }
  };

  const handleDownloadDataset = async (datasetId: number) => {
    try {
      console.log('Attempting to download dataset:', datasetId);
      
      // First initiate the download to get a secure token
      const downloadInfo = await datasetsAPI.initiateDownload(datasetId, 'original');
      console.log('Download info received:', downloadInfo);
      
      if (downloadInfo.download_token) {
        // Create a download link using the token with the correct API path
        const downloadUrl = `/api/datasets/download/${downloadInfo.download_token}`;
        
        // Create a temporary link and trigger download
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = downloadInfo.filename || `dataset_${datasetId}`;
        link.target = '_blank'; // Open in new tab to handle any auth issues
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        console.log('Download initiated successfully');
      } else {
        throw new Error('No download token received');
      }
      
    } catch (error) {
      console.error('Error downloading dataset:', error);
      alert('Failed to download dataset. Please try again.');
    }
  };

  const filteredDatasets = datasets.filter(dataset => {
    const matchesSearch = dataset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (dataset.description && dataset.description.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesLevel = selectedSharingLevel === 'all' || dataset.sharing_level === selectedSharingLevel;
    return matchesSearch && matchesLevel;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center space-y-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"></div>
          <p className="text-gray-600">Loading data access portal...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="py-6 animate-fade-in">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Data Access Portal</h1>
          <p className="text-gray-600 mt-2">
            Browse available datasets and manage access requests
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="mb-8">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('browse')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'browse'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Browse Datasets
            </button>
            <button
              onClick={() => setActiveTab('requests')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'requests'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              My Requests
            </button>
          </nav>
        </div>

        {activeTab === 'browse' && (
          <div className="space-y-6">
            {/* Search and Filters */}
            <Card variant="outlined">
              <CardContent className="p-6">
                <div className="flex flex-col sm:flex-row gap-4">
                  <div className="flex-1">
                    <input
                      type="text"
                      placeholder="Search datasets..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <select
                    value={selectedSharingLevel}
                    onChange={(e) => setSelectedSharingLevel(e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="all">All Sharing Levels</option>
                    <option value="public">Public</option>
                    <option value="organization">Organization</option>
                    <option value="private">Private</option>
                  </select>
                </div>
              </CardContent>
            </Card>

            {/* Datasets Grid */}
            {filteredDatasets.length === 0 ? (
              <Card variant="outlined">
                <CardContent className="p-12 text-center">
                  <div className="w-24 h-24 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                    <span className="text-4xl">🔍</span>
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No datasets available for access</h3>
                  <p className="text-gray-600">
                    {searchTerm || selectedSharingLevel !== 'all'
                      ? 'Try adjusting your search or filter criteria.'
                      : 'No datasets from other users are available for access at the moment. Datasets may be private or you may already have access to all available datasets.'
                    }</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {filteredDatasets.map((dataset) => (
                  <Card key={dataset.id} variant="elevated" interactive className="hover-lift">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-lg">{dataset.name}</CardTitle>
                          <CardDescription className="mt-2">
                            {dataset.description || 'No description available'}
                          </CardDescription>
                        </div>
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          dataset.sharing_level === 'public' ? 'bg-green-100 text-green-800' :
                          dataset.sharing_level === 'organization' ? 'bg-blue-100 text-blue-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {dataset.sharing_level}
                        </span>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex items-center text-sm text-gray-600">
                          <span className="mr-2">📁</span>
                          <span>{dataset.type?.toUpperCase() || 'Unknown'}</span>
                        </div>
                        {dataset.size && (
                          <div className="flex items-center text-sm text-gray-600">
                            <span className="mr-2">💾</span>
                            <span>{dataset.size} GB</span>
                          </div>
                        )}
                        <div className="flex items-center text-sm text-gray-600">
                          <span className="mr-2">👤</span>
                          <span>{dataset.owner_name || 'Unknown'}</span>
                        </div>
                        <div className="flex items-center text-sm text-gray-600">
                          <span className="mr-2">📅</span>
                          <span>{new Date(dataset.last_updated).toLocaleDateString()}</span>
                        </div>
                      </div>
                      
                      <div className="mt-4 flex space-x-2">
                        {dataset.can_access ? (
                          <>
                            <Link href={`/datasets/${dataset.id}`}>
                              <Button variant="outline" size="sm" className="flex-1">
                                <span className="mr-1">👁️</span>
                                View Dataset
                              </Button>
                            </Link>
                            <Button 
                              variant="gradient" 
                              size="sm" 
                              className="flex-1"
                              onClick={() => handleDownloadDataset(dataset.id)}
                            >
                              <span className="mr-1">⬇️</span>
                              Download
                            </Button>
                          </>
                        ) : dataset.can_request_access ? (
                          <Button 
                            variant="gradient" 
                            size="sm" 
                            className="flex-1"
                            onClick={() => handleRequestAccess(dataset.id)}
                          >
                            <span className="mr-1">🔑</span>
                            Request Access
                          </Button>
                        ) : null}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'requests' && (
          <Card variant="elevated">
            <CardHeader>
              <CardTitle>My Access Requests</CardTitle>
              <CardDescription>
                Track the status of your data access requests
              </CardDescription>
            </CardHeader>
            <CardContent>
              {accessRequests.length === 0 ? (
                <div className="text-center py-12">
                  <div className="w-24 h-24 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                    <span className="text-4xl">📋</span>
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No access requests</h3>
                  <p className="text-gray-600">
                    You haven't made any access requests yet. Browse datasets to request access.
                  </p>
                  <Button 
                    variant="gradient" 
                    className="mt-4"
                    onClick={() => setActiveTab('browse')}
                  >
                    Browse Datasets
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {accessRequests.map((request) => (
                    <div key={request.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="font-medium text-gray-900">{request.dataset_name}</h4>
                          <p className="text-sm text-gray-600 mt-1">
                            Request type: {request.request_type} | Level: {request.requested_level}
                          </p>
                          <p className="text-sm text-gray-600 mt-1">
                            Purpose: {request.purpose}
                          </p>
                          <p className="text-sm text-gray-600 mt-1">
                            Justification: {request.justification}
                          </p>
                          <p className="text-xs text-gray-500 mt-2">
                            Requested on {new Date(request.request_date).toLocaleDateString()}
                          </p>
                        </div>
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          request.status === 'approved' ? 'bg-green-100 text-green-800' :
                          request.status === 'rejected' ? 'bg-red-100 text-red-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {request.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}