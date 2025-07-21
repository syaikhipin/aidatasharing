'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useAuth } from '@/components/auth/AuthProvider';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { datasetsAPI } from '@/lib/api';

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export default function DatasetsPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <DatasetsContent />
      </DashboardLayout>
    </ProtectedRoute>
  );
}

function DatasetsContent() {
  const { user } = useAuth();
  const [datasets, setDatasets] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDatasets, setShowDatasets] = useState(false);

  // Remove automatic fetching on component mount

  const fetchDatasets = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await datasetsAPI.getDatasets();
      setDatasets(response);
    } catch (error: any) {
      console.error('Failed to fetch datasets:', error);
      setError(error.response?.data?.detail || 'Failed to fetch datasets');
      setDatasets([]); // Set empty array on error
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteDataset = async (datasetId: number, datasetName: string) => {
    if (!confirm(`Are you sure you want to delete the dataset "${datasetName}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await datasetsAPI.deleteDataset(datasetId);
      // Remove the deleted dataset from the local state
      setDatasets(datasets.filter(dataset => dataset.id !== datasetId));
    } catch (error: any) {
      console.error('Failed to delete dataset:', error);
      alert(error.response?.data?.detail || 'Failed to delete dataset');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
        <div className="mb-8">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">Data Sharing Platform</h1>
            <p className="text-lg text-gray-600 mb-8">
              Choose how you want to share your data
            </p>
            
            {/* Two Mode Selection */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto mb-8">
              {/* File Upload Mode */}
              <Link href="/datasets/upload" className="group">
                <div className="bg-white border-2 border-gray-200 rounded-lg p-8 hover:border-blue-500 hover:shadow-lg transition-all duration-200">
                  <div className="text-center">
                    <div className="mx-auto h-16 w-16 bg-blue-100 rounded-full flex items-center justify-center mb-4 group-hover:bg-blue-200">
                      <svg className="h-8 w-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">File Upload</h3>
                    <p className="text-gray-600">
                      Upload CSV, Excel, or other data files directly from your computer
                    </p>
                  </div>
                </div>
              </Link>
              
              {/* Connector Mode */}
              <Link href="/connections" className="group">
                <div className="bg-white border-2 border-gray-200 rounded-lg p-8 hover:border-green-500 hover:shadow-lg transition-all duration-200">
                  <div className="text-center">
                    <div className="mx-auto h-16 w-16 bg-green-100 rounded-full flex items-center justify-center mb-4 group-hover:bg-green-200">
                      <svg className="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                      </svg>
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">Data Connector</h3>
                    <p className="text-gray-600">
                      Connect to databases, APIs, and other data sources
                    </p>
                  </div>
                </div>
              </Link>
            </div>
            
            <div className="flex justify-center">
               <button
                 onClick={() => {
                   if (!showDatasets) {
                     setShowDatasets(true);
                     fetchDatasets();
                   } else {
                     setShowDatasets(false);
                   }
                 }}
                 className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-md text-sm font-medium"
               >
                 {showDatasets ? 'Hide Datasets' : 'View Existing Datasets'}
               </button>
             </div>
          </div>
        </div>

        {showDatasets && (
          <div className="mt-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Your Datasets</h2>
            
            {error && (
              <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
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
                      <button
                        onClick={fetchDatasets}
                        className="text-sm font-medium text-red-800 hover:text-red-600"
                      >
                        Try again
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {datasets.length === 0 && !error && !isLoading ? (
              <div className="bg-white shadow rounded-lg">
                <div className="text-center py-12">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No datasets found</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Get started by uploading your first dataset.
                  </p>
                  <div className="mt-6">
                    <Link
                      href="/datasets/upload"
                      className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                    >
                      Upload Dataset
                    </Link>
                  </div>
                </div>
              </div>
            ) : datasets.length > 0 ? (
              <div className="bg-white shadow overflow-hidden sm:rounded-md">
                <ul className="divide-y divide-gray-200">
                  {datasets.map((dataset) => (
                    <li key={dataset.id}>
                      <div className="px-6 py-4 hover:bg-gray-50">
                        <div className="flex items-center justify-between">
                          <div className="flex-1 min-w-0">
                            <h3 className="text-lg font-medium text-gray-900">
                              {dataset.name}
                            </h3>
                            <p className="mt-1 text-sm text-gray-600">
                              {dataset.description || 'No description provided'}
                            </p>
                            <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                              <span>Type: {dataset.type?.toUpperCase() || 'Unknown'}</span>
                              <span>Sharing: {dataset.sharing_level || 'Private'}</span>
                              {dataset.size_bytes && (
                                <span>Size: {formatFileSize(dataset.size_bytes)}</span>
                              )}
                              <span>Created: {new Date(dataset.created_at).toLocaleDateString()}</span>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Link
                              href={`/datasets/${dataset.id}`}
                              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                            >
                              View
                            </Link>
                            <button 
                              onClick={() => window.open(`/datasets/${dataset.id}/chat`, '_blank')}
                              className="text-purple-600 hover:text-purple-800 text-sm font-medium"
                            >
                              Chat
                            </button>
                            <button className="text-green-600 hover:text-green-800 text-sm font-medium">
                              Download
                            </button>
                            <button 
                              onClick={() => handleDeleteDataset(dataset.id, dataset.name)}
                              className="text-red-600 hover:text-red-800 text-sm font-medium"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}