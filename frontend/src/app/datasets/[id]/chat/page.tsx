'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { datasetsAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
  const [chatHistory, setChatHistory] = useState<any[]>([]);
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
      const response = await datasetsAPI.chatWithDataset(datasetId, userMessage);
      
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
        message: error.response?.data?.detail || 'Failed to connect to chat service. Please ensure MindsDB is running and properly configured.',
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

  if (error) {
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
            Chat with "{dataset.name}"
          </h1>
          <p className="mt-1 text-sm text-gray-600">
            Ask questions about your dataset and get AI-powered insights using MindsDB
          </p>
        </div>

        {/* Chat Interface */}
        <Card variant="elevated">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center">
                  <span className="mr-2">💬</span>
                  AI Chat Assistant
                </CardTitle>
                <CardDescription>
                  Powered by MindsDB and Google Gemini
                </CardDescription>
              </div>
              {chatHistory.length > 0 && (
                <Button variant="outline" size="sm" onClick={clearChat}>
                  Clear Chat
                </Button>
              )}
            </div>
          </CardHeader>
          
          <CardContent>
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
                      <p className="text-sm whitespace-pre-wrap">{message.message}</p>
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
                  Ask a question about your data
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
                  <Button
                    onClick={handleChat}
                    disabled={!chatMessage.trim() || isChatting}
                    variant="gradient"
                    className="px-6"
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
                  </Button>
                </div>
              </div>

              {/* Suggestions */}
              {chatHistory.length === 0 && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-blue-800 mb-2">💡 Try asking questions like:</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {[
                      "What insights can you provide about this dataset?",
                      "How many records are in this dataset?",
                      "What are the key patterns in the data?",
                      "Can you summarize the main findings?",
                      "What columns are available in this dataset?",
                      "Are there any data quality issues?"
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
              <Card variant="outlined" className="bg-gray-50 border-gray-200">
                <CardContent className="p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <span className="text-gray-500 text-lg">ℹ️</span>
                    </div>
                    <div className="ml-3">
                      <h4 className="text-sm font-medium text-gray-800">Chat Information</h4>
                      <div className="mt-1 text-sm text-gray-600">
                        <p>
                          This chat feature uses MindsDB to analyze your dataset and provide insights. 
                          Make sure MindsDB is running and properly configured with Google Gemini API for the best experience.
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}