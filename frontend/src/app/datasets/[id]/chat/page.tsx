'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { datasetsAPI, agentsAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { DataVisualization } from '@/components/DataVisualization';
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
  const [availableAgents, setAvailableAgents] = useState<any[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>('auto');
  const [useAgents, setUseAgents] = useState(true);
  const [agentsLoading, setAgentsLoading] = useState(false);

  useEffect(() => {
    fetchDataset();
    fetchAvailableAgents();
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

  const fetchAvailableAgents = async () => {
    try {
      setAgentsLoading(true);
      const agents = await agentsAPI.getAvailableAgents();
      setAvailableAgents(agents);
    } catch (error: any) {
      console.error('Failed to fetch available agents:', error);
      // Don't show error for agents, just disable agent features
      setUseAgents(false);
    } finally {
      setAgentsLoading(false);
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

      // Determine agent to use
      const agentName = selectedAgent === 'auto' ? undefined : selectedAgent;

      const response = await datasetsAPI.chatWithDataset(datasetId, userMessage, agentName, useAgents);

      // Add AI response to history
      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        message: response.answer || response.response || 'No response received',
        timestamp: new Date().toISOString(),
        model: response.model,
        tokens_used: response.tokens_used,
        visualizations: response.visualizations || [], // New combined visualizations array
        plotly_figures: response.plotly_figures || [], // Plotly-specific figures
        matplotlib_figures: response.matplotlib_figures || [], // Matplotlib-specific figures
        dataAnalysis: response.data_analysis,
        hasVisualizations: response.has_visualizations || (response.visualizations && response.visualizations.length > 0) || false,
        agent_used: response.agent_used,
        agent_system: response.agent_system,
        planner: response.planner,
        code: response.code,
        execution_output: response.execution_output,
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
              <div className="mb-6 space-y-4 max-h-[600px] overflow-y-auto">
                {chatHistory.map((message) => (
                  <div key={message.id}>
                    {message.type === 'user' ? (
                      <div className="flex justify-end">
                        <div className="max-w-xs lg:max-w-md px-4 py-2 rounded-lg bg-blue-600 text-white">
                          <p className="text-sm whitespace-pre-wrap">{message.message}</p>
                          <p className="text-xs mt-1 opacity-75">
                            {new Date(message.timestamp).toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <div className="flex justify-start">
                          <div className={`max-w-2xl px-4 py-2 rounded-lg ${
                            message.error
                              ? 'bg-red-50 border border-red-200 text-red-700'
                              : 'bg-gray-100 text-gray-900'
                          }`}>
                            {/* Agent information */}
                            {message.agent_system && message.agent_used && (
                              <div className="mb-2 p-2 bg-blue-50 border border-blue-200 rounded text-xs">
                                <div className="flex items-center space-x-2">
                                  <span className="text-blue-600 font-medium">
                                    🤖 Agent: {availableAgents.find(a => a.name === message.agent_used)?.display_name || message.agent_used}
                                  </span>
                                  {message.planner && (
                                    <Badge variant="outline" className="text-xs">
                                      Auto-routed by Planner
                                    </Badge>
                                  )}
                                </div>
                                {message.planner?.reasoning && (
                                  <p className="text-blue-600 mt-1">{message.planner.reasoning}</p>
                                )}
                              </div>
                            )}

                            <p className="text-sm whitespace-pre-wrap">{message.message}</p>

                            {/* Show generated code if available */}
                            {message.code && (
                              <div className="mt-3 p-3 bg-gray-800 text-green-400 rounded text-xs font-mono overflow-x-auto">
                                <div className="flex items-center justify-between mb-2">
                                  <span className="text-gray-300">Generated Code:</span>
                                  <Badge variant="secondary" className="text-xs">
                                    {message.agent_used || 'AI'}
                                  </Badge>
                                </div>
                                <pre className="whitespace-pre-wrap">{message.code}</pre>
                              </div>
                            )}

                            {/* Show execution output if available */}
                            {message.execution_output && (
                              <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded text-xs">
                                <div className="flex items-center mb-2">
                                  <span className="text-blue-700 font-medium">📄 Execution Output:</span>
                                </div>
                                <pre className="whitespace-pre-wrap text-blue-600">{message.execution_output}</pre>
                              </div>
                            )}

                            <p className="text-xs mt-1 opacity-75">
                              {new Date(message.timestamp).toLocaleTimeString()}
                              {message.model && !message.error && (
                                <span className="ml-2">• {message.model}</span>
                              )}
                              {message.tokens_used && !message.error && (
                                <span className="ml-1">• {message.tokens_used} tokens</span>
                              )}
                              {message.agent_system && (
                                <span className="ml-1 text-blue-600">• Agent System</span>
                              )}
                            </p>
                          </div>
                        </div>
                        
                        {/* Show visualizations if available */}
                        {message.hasVisualizations && (message.visualizations || message.dataAnalysis) && (
                          <div className="ml-0">
                            <DataVisualization
                              visualizations={message.visualizations}
                              dataAnalysis={message.dataAnalysis}
                            />
                          </div>
                        )}
                      </div>
                    )}
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

            {/* Agent Selection */}
            {useAgents && availableAgents.length > 0 && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-medium text-blue-800">🤖 AI Agent Selection</h4>
                  <Badge variant="secondary" className="text-xs">
                    {useAgents ? 'Agents Enabled' : 'Standard Chat'}
                  </Badge>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-blue-700 mb-1">
                      Choose Agent
                    </label>
                    <Select value={selectedAgent} onValueChange={setSelectedAgent}>
                      <SelectTrigger className="bg-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="auto">
                          🎯 Auto-Route (Planner chooses best agent)
                        </SelectItem>
                        {availableAgents.map((agent) => (
                          <SelectItem key={agent.name} value={agent.name}>
                            {agent.icon} {agent.display_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-blue-700 mb-1">
                      Agent Description
                    </label>
                    <div className="text-xs text-blue-600 bg-white p-2 rounded border min-h-[2.5rem] flex items-center">
                      {selectedAgent === 'auto' ? (
                        'Let the AI planner automatically choose the most suitable agent for your task.'
                      ) : (
                        availableAgents.find(a => a.name === selectedAgent)?.description || 'Select an agent to see description'
                      )}
                    </div>
                  </div>
                </div>
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
                    onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleChat()}
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
                  <h4 className="text-sm font-medium text-blue-800 mb-2">
                    💡 Try asking questions like:
                    {useAgents && availableAgents.length > 0 && (
                      <span className="ml-2 text-xs font-normal">(Agents will automatically assist)</span>
                    )}
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {[
                      "📊 Show visualizations of this dataset",
                      "📈 Analyze the data distribution with charts",
                      "🔍 What are the key patterns and correlations?",
                      "📉 Create statistical analysis with graphs",
                      "@data_viz_agent Create advanced visualizations",
                      "@statistical_analytics_agent Perform statistical analysis",
                      "Show me the data quality and missing values",
                      "Create a comprehensive data report with charts"
                    ].map((suggestion, index) => (
                      <button
                        key={index}
                        onClick={() => setChatMessage(suggestion)}
                        className="text-left text-sm text-blue-700 hover:text-blue-900 p-2 rounded hover:bg-blue-100 transition-colors"
                      >
                        <span className="block">
                          {suggestion.startsWith('@') && (
                            <Badge variant="outline" className="mr-1 text-xs">
                              Agent
                            </Badge>
                          )}
                          "{suggestion}"
                        </span>
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
                          {useAgents && availableAgents.length > 0 ? (
                            <>
                              This chat feature uses AI agents to analyze your dataset and provide specialized insights.
                              Agents can help with data preprocessing, statistical analysis, machine learning, and visualization.
                              You can specify an agent with "@agent_name" or let the planner auto-route your request.
                            </>
                          ) : (
                            <>
                              This chat feature uses MindsDB to analyze your dataset and provide insights.
                              Make sure MindsDB is running and properly configured with Google Gemini API for the best experience.
                            </>
                          )}
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