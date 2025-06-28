'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { datasetsAPI } from '@/lib/api';
import Link from 'next/link';

export default function DatasetChatPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <DatasetChatContent />
      </DashboardLayout>
    </ProtectedRoute>
  );
}

function DatasetChatContent() {
  const params = useParams();
  const datasetId = parseInt(params.id as string);
  
  const [dataset, setDataset] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [chatMessage, setChatMessage] = useState('');
  const [chatResponse, setChatResponse] = useState<any>(null);
  const [isChatting, setIsChatting] = useState(false);

  useEffect(() => {
    fetchDataset();
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
            <p className="text-red-700">{error}</p>
            <Link href="/datasets" className="text-red-600 hover:text-red-800 text-sm">
              ← Back to datasets
            </Link>
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
            <Link
              href="/datasets"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 mt-4"
            >
              ← Back to datasets
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="py-6">
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
            Chat with "{dataset.name}"
          </h1>
          <p className="mt-1 text-sm text-gray-600">
            Ask questions about your dataset and get AI-powered insights
          </p>
        </div>

        {/* Chat Interface */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="space-y-4">
            {/* Chat Input */}
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

            {/* Chat Response */}
            {chatResponse && (
              <div className={`p-4 rounded-md ${
                chatResponse.error 
                  ? 'bg-red-50 border border-red-200' 
                  : 'bg-blue-50 border border-blue-200'
              }`}>
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
                    <h4 className={`text-sm font-medium ${
                      chatResponse.error ? 'text-red-800' : 'text-blue-800'
                    }`}>
                      {chatResponse.error ? 'Error' : 'AI Response'}
                    </h4>
                    <div className={`mt-2 text-sm ${
                      chatResponse.error ? 'text-red-700' : 'text-blue-700'
                    }`}>
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

            {/* Suggestions */}
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
    </div>
  );
} 