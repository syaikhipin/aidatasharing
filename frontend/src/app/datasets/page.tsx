'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useAuth } from '@/components/auth/AuthProvider';
import { useState, useEffect } from 'react';
import Link from 'next/link';

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

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      setIsLoading(true);
      // Mock data for demonstration
      const mockDatasets = [
        {
          id: 1,
          name: 'Customer Sales Data',
          description: 'Quarterly sales data for all customers',
          type: 'csv',
          sharing_level: 'organization',
          size_bytes: 2048000,
          owner: { full_name: 'John Doe' },
          created_at: '2024-01-15T10:30:00Z',
        }
      ];
      setDatasets(mockDatasets);
    } catch (error) {
      console.error('Failed to fetch datasets:', error);
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
            <Link
              href="/datasets/upload"
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
            >
              Upload Dataset
            </Link>
          </div>
        </div>

        {datasets.length === 0 ? (
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
                        <p className="mt-1 text-sm text-gray-600">{dataset.description}</p>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                          View
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