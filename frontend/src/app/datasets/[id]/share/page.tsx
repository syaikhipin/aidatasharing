'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { datasetsAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import Link from 'next/link';

export default function DatasetSharePage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <DatasetShareContent />
      </DashboardLayout>
    </ProtectedRoute>
  );
}

function DatasetShareContent() {
  const params = useParams();
  const datasetId = parseInt(params.id as string);
  
  const [dataset, setDataset] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [shareTokens, setShareTokens] = useState<any[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [newToken, setNewToken] = useState<any>(null);

  useEffect(() => {
    fetchDataset();
    fetchShareTokens();
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

  const fetchShareTokens = async () => {
    try {
      const response = await datasetsAPI.getShareTokens(datasetId);
      setShareTokens(response || []);
    } catch (error: any) {
      console.error('Failed to fetch share tokens:', error);
      // Don't set error here as it might be expected for datasets without tokens
    }
  };

  const generateShareToken = async () => {
    try {
      setIsGenerating(true);
      const response = await datasetsAPI.generateShareToken(datasetId);
      setNewToken(response);
      await fetchShareTokens(); // Refresh the list
    } catch (error: any) {
      console.error('Failed to generate share token:', error);
      setError(error.response?.data?.detail || 'Failed to generate share token');
    } finally {
      setIsGenerating(false);
    }
  };

  const revokeShareToken = async (tokenId: number) => {
    try {
      await datasetsAPI.revokeShareToken(datasetId, tokenId);
      await fetchShareTokens(); // Refresh the list
    } catch (error: any) {
      console.error('Failed to revoke share token:', error);
      setError(error.response?.data?.detail || 'Failed to revoke share token');
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      // You could add a toast notification here
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const getShareUrl = (token: string) => {
    return `${window.location.origin}/share/${token}`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center space-y-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"></div>
          <p className="text-gray-600">Loading dataset...</p>
        </div>
      </div>
    );
  }

  if (error && !dataset) {
    return (
      <div className="py-6">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8">
          <Card variant="outlined" className="bg-red-50 border-red-200">
            <CardContent className="p-6">
              <div className="flex">
                <div className="flex-shrink-0">
                  <span className="text-red-400 text-xl">❌</span>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Error Loading Dataset</h3>
                  <div className="mt-2 text-sm text-red-700">
                    <p>{error}</p>
                  </div>
                  <div className="mt-3">
                    <Link href="/datasets">
                      <Button variant="outline" size="sm">
                        ← Back to datasets
                      </Button>
                    </Link>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!dataset) {
    return (
      <div className="py-6">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8">
          <Card variant="elevated">
            <CardContent className="p-12 text-center">
              <div className="w-24 h-24 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                <span className="text-4xl">❓</span>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Dataset not found</h3>
              <p className="text-gray-600 mb-6">
                The dataset you're looking for doesn't exist or you don't have access to it.
              </p>
              <Link href="/datasets">
                <Button variant="gradient">
                  ← Back to datasets
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="py-6 animate-fade-in">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8">
        {/* Header */}
        <div className="mb-8">
          <Link
            href={`/datasets/${datasetId}`}
            className="text-sm text-gray-500 hover:text-gray-700 mb-2 inline-block"
          >
            ← Back to dataset
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">
            Share "{dataset.name}"
          </h1>
          <p className="mt-1 text-sm text-gray-600">
            Generate secure sharing links for your dataset
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <Card variant="outlined" className="bg-red-50 border-red-200 mb-6">
            <CardContent className="p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <span className="text-red-400">⚠️</span>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* New Token Alert */}
        {newToken && (
          <Card variant="outlined" className="bg-green-50 border-green-200 mb-6">
            <CardContent className="p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <span className="text-green-400 text-xl">✅</span>
                </div>
                <div className="ml-3 flex-1">
                  <h4 className="text-sm font-medium text-green-800">Share Link Generated!</h4>
                  <div className="mt-2 text-sm text-green-700">
                    <p className="mb-2">Your new share link is ready:</p>
                    <div className="bg-white border border-green-300 rounded-md p-3 font-mono text-xs break-all">
                      {getShareUrl(newToken.token)}
                    </div>
                  </div>
                  <div className="mt-3 flex space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(getShareUrl(newToken.token))}
                    >
                      📋 Copy Link
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setNewToken(null)}
                    >
                      Dismiss
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Generate New Token */}
          <Card variant="elevated">
            <CardHeader>
              <CardTitle className="flex items-center">
                <span className="mr-2">🔗</span>
                Generate Share Link
              </CardTitle>
              <CardDescription>
                Create a secure link to share this dataset with others
              </CardDescription>
            </CardHeader>
            
            <CardContent>
              <div className="space-y-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-blue-800 mb-2">🔒 Security Features</h4>
                  <ul className="text-sm text-blue-700 space-y-1">
                    <li>• Unique token-based authentication</li>
                    <li>• No login required for recipients</li>
                    <li>• Revokable at any time</li>
                    <li>• Read-only access</li>
                  </ul>
                </div>

                <Button
                  onClick={generateShareToken}
                  disabled={isGenerating}
                  variant="gradient"
                  className="w-full"
                >
                  {isGenerating ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                      Generating...
                    </div>
                  ) : (
                    <>
                      <span className="mr-2">🚀</span>
                      Generate New Share Link
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Active Share Tokens */}
          <Card variant="elevated">
            <CardHeader>
              <CardTitle className="flex items-center">
                <span className="mr-2">📋</span>
                Active Share Links
              </CardTitle>
              <CardDescription>
                Manage your existing share links
              </CardDescription>
            </CardHeader>
            
            <CardContent>
              {shareTokens.length === 0 ? (
                <div className="text-center py-8">
                  <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                    <span className="text-2xl">🔗</span>
                  </div>
                  <h3 className="text-sm font-medium text-gray-900 mb-1">No active share links</h3>
                  <p className="text-sm text-gray-600">
                    Generate your first share link to get started
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {shareTokens.map((token) => (
                    <div key={token.id} className="border border-gray-200 rounded-lg p-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              Active
                            </span>
                            <span className="text-xs text-gray-500">
                              Created {new Date(token.created_at).toLocaleDateString()}
                            </span>
                          </div>
                          <div className="font-mono text-xs text-gray-600 break-all bg-gray-50 p-2 rounded border">
                            {getShareUrl(token.token)}
                          </div>
                        </div>
                      </div>
                      <div className="mt-3 flex space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => copyToClipboard(getShareUrl(token.token))}
                        >
                          📋 Copy
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => revokeShareToken(token.id)}
                          className="text-red-600 hover:text-red-700 hover:border-red-300"
                        >
                          🗑️ Revoke
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Information */}
        <Card variant="outlined" className="bg-gray-50 border-gray-200 mt-6">
          <CardContent className="p-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <span className="text-gray-500 text-lg">ℹ️</span>
              </div>
              <div className="ml-3">
                <h4 className="text-sm font-medium text-gray-800">How Share Links Work</h4>
                <div className="mt-2 text-sm text-gray-600">
                  <p className="mb-2">
                    Share links allow you to give others access to your dataset without requiring them to create an account or log in.
                  </p>
                  <ul className="list-disc list-inside space-y-1">
                    <li>Recipients can view the dataset and its metadata</li>
                    <li>Links are secure and can be revoked at any time</li>
                    <li>No editing or downloading permissions are granted</li>
                    <li>All access is logged for security purposes</li>
                  </ul>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}