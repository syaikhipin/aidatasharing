'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { datasetsAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import Link from 'next/link';

export default function SharedDatasetPage() {
  const params = useParams();
  const token = params.token as string;
  
  const [dataset, setDataset] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<any[]>([]);
  const [isLoadingData, setIsLoadingData] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const itemsPerPage = 10;

  useEffect(() => {
    if (token) {
      fetchSharedDataset();
    }
  }, [token]);

  const fetchSharedDataset = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await datasetsAPI.getSharedDataset(token);
      setDataset(response);
      
      // Also fetch the data
      await fetchSharedData(1);
    } catch (error: any) {
      console.error('Failed to fetch shared dataset:', error);
      setError(error.response?.data?.detail || 'Failed to access shared dataset');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchSharedData = async (page: number) => {
    try {
      setIsLoadingData(true);
      const response = await datasetsAPI.getSharedDatasetData(token, page, itemsPerPage);
      setData(response.data || []);
      setTotalPages(Math.ceil((response.total || 0) / itemsPerPage));
      setCurrentPage(page);
    } catch (error: any) {
      console.error('Failed to fetch shared data:', error);
      setError(error.response?.data?.detail || 'Failed to load dataset data');
    } finally {
      setIsLoadingData(false);
    }
  };

  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      fetchSharedData(page);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
        <div className="flex items-center justify-center h-screen">
          <div className="flex flex-col items-center space-y-4">
            <div className="h-16 w-16 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"></div>
            <p className="text-gray-600 text-lg">Loading shared dataset...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
        <div className="flex items-center justify-center h-screen">
          <div className="max-w-md w-full mx-4">
            <Card variant="elevated" className="bg-white shadow-xl">
              <CardContent className="p-8 text-center">
                <div className="w-20 h-20 mx-auto mb-6 bg-red-100 rounded-full flex items-center justify-center">
                  <span className="text-4xl">❌</span>
                </div>
                <h1 className="text-xl font-bold text-gray-900 mb-2">Access Denied</h1>
                <p className="text-gray-600 mb-6">{error}</p>
                <div className="space-y-3">
                  <p className="text-sm text-gray-500">
                    This link may have expired or been revoked.
                  </p>
                  <Link href="/">
                    <Button variant="gradient" className="w-full">
                      Go to AI Share Platform
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  if (!dataset) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
        <div className="flex items-center justify-center h-screen">
          <div className="max-w-md w-full mx-4">
            <Card variant="elevated" className="bg-white shadow-xl">
              <CardContent className="p-8 text-center">
                <div className="w-20 h-20 mx-auto mb-6 bg-gray-100 rounded-full flex items-center justify-center">
                  <span className="text-4xl">❓</span>
                </div>
                <h1 className="text-xl font-bold text-gray-900 mb-2">Dataset Not Found</h1>
                <p className="text-gray-600 mb-6">
                  The shared dataset you're looking for doesn't exist or is no longer available.
                </p>
                <Link href="/">
                  <Button variant="gradient" className="w-full">
                    Go to AI Share Platform
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">AI</span>
                </div>
              </div>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">AI Share Platform</h1>
                <p className="text-xs text-gray-500">Shared Dataset View</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                🔗 Shared Access
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="py-8 animate-fade-in">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Dataset Info */}
          <div className="mb-8">
            <Card variant="elevated" className="bg-white shadow-lg">
              <CardHeader className="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-t-lg">
                <CardTitle className="text-2xl flex items-center">
                  <span className="mr-3">📊</span>
                  {dataset.name}
                </CardTitle>
                <CardDescription className="text-blue-100">
                  {dataset.description || 'No description provided'}
                </CardDescription>
              </CardHeader>
              
              <CardContent className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                        <span className="text-blue-600">👤</span>
                      </div>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">Owner</p>
                      <p className="text-sm text-gray-600">{dataset.owner?.username || 'Unknown'}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                        <span className="text-green-600">📅</span>
                      </div>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">Created</p>
                      <p className="text-sm text-gray-600">
                        {new Date(dataset.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                        <span className="text-purple-600">🔢</span>
                      </div>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">Records</p>
                      <p className="text-sm text-gray-600">{dataset.record_count || 0}</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Data Table */}
          <Card variant="elevated" className="bg-white shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center">
                  <span className="mr-2">📋</span>
                  Dataset Preview
                </span>
                {isLoadingData && (
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent"></div>
                    <span className="text-sm text-gray-600">Loading...</span>
                  </div>
                )}
              </CardTitle>
              <CardDescription>
                Viewing page {currentPage} of {totalPages} ({dataset.record_count || 0} total records)
              </CardDescription>
            </CardHeader>
            
            <CardContent>
              {data.length === 0 ? (
                <div className="text-center py-12">
                  <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                    <span className="text-2xl">📭</span>
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No data available</h3>
                  <p className="text-gray-600">
                    This dataset doesn't contain any records yet.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Table */}
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          {Object.keys(data[0] || {}).map((key) => (
                            <th
                              key={key}
                              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                            >
                              {key}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {data.map((row, index) => (
                          <tr key={index} className="hover:bg-gray-50">
                            {Object.values(row).map((value: any, cellIndex) => (
                              <td
                                key={cellIndex}
                                className="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
                              >
                                {value !== null && value !== undefined ? String(value) : '-'}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Pagination */}
                  {totalPages > 1 && (
                    <div className="flex items-center justify-between border-t border-gray-200 pt-4">
                      <div className="flex items-center space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handlePageChange(currentPage - 1)}
                          disabled={currentPage === 1 || isLoadingData}
                        >
                          ← Previous
                        </Button>
                        <span className="text-sm text-gray-600">
                          Page {currentPage} of {totalPages}
                        </span>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handlePageChange(currentPage + 1)}
                          disabled={currentPage === totalPages || isLoadingData}
                        >
                          Next →
                        </Button>
                      </div>
                      <div className="text-sm text-gray-500">
                        Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, dataset.record_count || 0)} of {dataset.record_count || 0} results
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Footer Info */}
          <div className="mt-8 text-center">
            <Card variant="outlined" className="bg-gray-50 border-gray-200">
              <CardContent className="p-6">
                <div className="flex items-center justify-center space-x-2 text-sm text-gray-600">
                  <span>🔒</span>
                  <span>This is a read-only view of a shared dataset.</span>
                  <span>•</span>
                  <Link href="/" className="text-blue-600 hover:text-blue-700">
                    Create your own account
                  </Link>
                  <span>to upload and share your own datasets.</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}