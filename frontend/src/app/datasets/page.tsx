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
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
      setDatasets([]); // Set empty array on error
    } finally {
      setIsLoading(false);
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
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Datasets</h1>
              <p className="mt-1 text-sm text-gray-600">
                Manage and explore your organization's datasets.
              </p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={fetchDatasets}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Refresh
              </button>
              <Link
                href="/datasets/upload"
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Upload Dataset
              </Link>
            </div>
          </div>
        </div>

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

        {datasets.length === 0 && !error ? (
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
        ) : (
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
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
} 