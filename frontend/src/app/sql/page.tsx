'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useAuth } from '@/components/auth/AuthProvider';
import { useState, useEffect, useRef } from 'react';
import { datasetsAPI } from '@/lib/api';

export default function SQLPlaygroundPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <SQLPlaygroundContent />
      </DashboardLayout>
    </ProtectedRoute>
  );
}

function SQLPlaygroundContent() {
  const { user } = useAuth();
  const [datasets, setDatasets] = useState<any[]>([]);
  const [selectedDataset, setSelectedDataset] = useState('');
  const [sqlQuery, setSqlQuery] = useState('');
  const [aiQuery, setAiQuery] = useState('');
  const [results, setResults] = useState<any>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [isAiProcessing, setIsAiProcessing] = useState(false);
  const [queryHistory, setQueryHistory] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'sql' | 'ai'>('sql');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    fetchDatasets();
    loadQueryHistory();
  }, []);

  const fetchDatasets = async () => {
    try {
      // Mock datasets
      const mockDatasets = [
        { id: 1, name: 'Customer Sales Data', table_name: 'customer_sales' },
        { id: 2, name: 'Marketing Analytics', table_name: 'marketing_data' },
        { id: 3, name: 'Product Catalog', table_name: 'products' }
      ];
      setDatasets(mockDatasets);
    } catch (error) {
      console.error('Failed to fetch datasets:', error);
    }
  };

  const loadQueryHistory = () => {
    const history = JSON.parse(localStorage.getItem('sqlQueryHistory') || '[]');
    setQueryHistory(history);
  };

  const saveQueryToHistory = (query: string, results: any) => {
    const historyItem = {
      id: Date.now(),
      query,
      dataset: selectedDataset,
      timestamp: new Date().toISOString(),
      rowCount: results?.rows?.length || 0
    };
    
    const newHistory = [historyItem, ...queryHistory.slice(0, 9)]; // Keep last 10
    setQueryHistory(newHistory);
    localStorage.setItem('sqlQueryHistory', JSON.stringify(newHistory));
  };

  const executeSQL = async () => {
    if (!sqlQuery.trim() || !selectedDataset) return;

    try {
      setIsExecuting(true);
      
      // Simulate SQL execution with mock data
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockResults = {
        columns: ['customer_id', 'name', 'email', 'total_spent', 'last_purchase'],
        rows: [
          [1, 'John Doe', 'john@example.com', 1250.50, '2024-01-15'],
          [2, 'Jane Smith', 'jane@example.com', 890.25, '2024-01-14'],
          [3, 'Bob Johnson', 'bob@example.com', 2100.75, '2024-01-16'],
          [4, 'Alice Wilson', 'alice@example.com', 750.00, '2024-01-13'],
          [5, 'Charlie Brown', 'charlie@example.com', 1800.30, '2024-01-12']
        ],
        execution_time: '127ms',
        query: sqlQuery
      };
      
      setResults(mockResults);
      saveQueryToHistory(sqlQuery, mockResults);
      
    } catch (error) {
      console.error('Query execution failed:', error);
      setResults({ error: 'Query execution failed: ' + error });
    } finally {
      setIsExecuting(false);
    }
  };

  const processAIQuery = async () => {
    if (!aiQuery.trim() || !selectedDataset) return;

    try {
      setIsAiProcessing(true);
      
      // Simulate AI processing
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Generate SQL based on natural language
      const generatedSQL = generateSQLFromNaturalLanguage(aiQuery);
      setSqlQuery(generatedSQL);
      setActiveTab('sql');
      
      // Auto-execute the generated query
      setTimeout(() => {
        executeSQL();
      }, 500);
      
    } catch (error) {
      console.error('AI processing failed:', error);
    } finally {
      setIsAiProcessing(false);
    }
  };

  const generateSQLFromNaturalLanguage = (naturalQuery: string): string => {
    const lowerQuery = naturalQuery.toLowerCase();
    const datasetObj = datasets.find(d => d.id.toString() === selectedDataset);
    const tableName = datasetObj?.table_name || 'data';
    
    // Simple NL to SQL conversion (would use actual AI in production)
    if (lowerQuery.includes('customer') && lowerQuery.includes('spent') && lowerQuery.includes('most')) {
      return `SELECT customer_id, name, total_spent 
FROM ${tableName} 
ORDER BY total_spent DESC 
LIMIT 10;`;
    } else if (lowerQuery.includes('average') || lowerQuery.includes('avg')) {
      return `SELECT AVG(total_spent) as average_spending 
FROM ${tableName};`;
    } else if (lowerQuery.includes('count') || lowerQuery.includes('how many')) {
      return `SELECT COUNT(*) as total_customers 
FROM ${tableName};`;
    } else if (lowerQuery.includes('recent') || lowerQuery.includes('last')) {
      return `SELECT * 
FROM ${tableName} 
ORDER BY last_purchase DESC 
LIMIT 20;`;
    } else {
      return `SELECT * 
FROM ${tableName} 
LIMIT 100;`;
    }
  };

  const exportResults = (format: 'csv' | 'json') => {
    if (!results?.rows) return;

    let content = '';
    let filename = `query_results_${Date.now()}`;

    if (format === 'csv') {
      const headers = results.columns.join(',');
      const rows = results.rows.map((row: any[]) => row.join(',')).join('\n');
      content = `${headers}\n${rows}`;
      filename += '.csv';
    } else {
      const jsonData = results.rows.map((row: any[]) => {
        const obj: any = {};
        results.columns.forEach((col: string, index: number) => {
          obj[col] = row[index];
        });
        return obj;
      });
      content = JSON.stringify(jsonData, null, 2);
      filename += '.json';
    }

    const blob = new Blob([content], { type: format === 'csv' ? 'text/csv' : 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">SQL Playground</h1>
          <p className="mt-1 text-sm text-gray-600">
            Query your organization's data with SQL or natural language using AI assistance.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Panel - Dataset Selection & History */}
          <div className="lg:col-span-1 space-y-6">
            {/* Dataset Selection */}
            <div className="bg-white shadow rounded-lg p-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Data Source</h3>
              <select
                value={selectedDataset}
                onChange={(e) => setSelectedDataset(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Select dataset...</option>
                {datasets.map((dataset) => (
                  <option key={dataset.id} value={dataset.id}>
                    {dataset.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Query History */}
            <div className="bg-white shadow rounded-lg p-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Recent Queries</h3>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {queryHistory.length === 0 ? (
                  <p className="text-sm text-gray-500">No query history</p>
                ) : (
                  queryHistory.map((item) => (
                    <div
                      key={item.id}
                      onClick={() => setSqlQuery(item.query)}
                      className="p-2 border border-gray-200 rounded cursor-pointer hover:bg-gray-50"
                    >
                      <p className="text-xs text-gray-900 truncate">{item.query}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(item.timestamp).toLocaleString()} • {item.rowCount} rows
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Main Panel - Query Interface */}
          <div className="lg:col-span-3 space-y-6">
            {/* Query Interface */}
            <div className="bg-white shadow rounded-lg">
              {/* Tabs */}
              <div className="border-b border-gray-200">
                <nav className="-mb-px flex">
                  <button
                    onClick={() => setActiveTab('sql')}
                    className={`py-2 px-4 border-b-2 font-medium text-sm ${
                      activeTab === 'sql'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    SQL Query
                  </button>
                  <button
                    onClick={() => setActiveTab('ai')}
                    className={`py-2 px-4 border-b-2 font-medium text-sm ${
                      activeTab === 'ai'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    🤖 AI Assistant
                  </button>
                </nav>
              </div>

              <div className="p-6">
                {activeTab === 'sql' ? (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        SQL Query
                      </label>
                      <textarea
                        ref={textareaRef}
                        value={sqlQuery}
                        onChange={(e) => setSqlQuery(e.target.value)}
                        rows={8}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        placeholder="SELECT * FROM table_name WHERE condition..."
                        style={{ fontSize: '14px', lineHeight: '1.5' }}
                      />
                    </div>
                    <div className="flex justify-between items-center">
                      <div className="text-sm text-gray-500">
                        Use Ctrl+Enter to execute query
                      </div>
                      <button
                        onClick={executeSQL}
                        disabled={!sqlQuery.trim() || !selectedDataset || isExecuting}
                        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                      >
                        {isExecuting && (
                          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                        )}
                        Execute Query
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Ask in Natural Language
                      </label>
                      <textarea
                        value={aiQuery}
                        onChange={(e) => setAiQuery(e.target.value)}
                        rows={4}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        placeholder="e.g., Show me the top 10 customers by total spending..."
                      />
                    </div>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <h4 className="font-medium text-blue-900 mb-2">Try these examples:</h4>
                      <div className="space-y-1 text-sm text-blue-800">
                        <div 
                          className="cursor-pointer hover:underline"
                          onClick={() => setAiQuery("Show me the customers who spent the most money")}
                        >
                          • "Show me the customers who spent the most money"
                        </div>
                        <div 
                          className="cursor-pointer hover:underline"
                          onClick={() => setAiQuery("What's the average spending per customer?")}
                        >
                          • "What's the average spending per customer?"
                        </div>
                        <div 
                          className="cursor-pointer hover:underline"
                          onClick={() => setAiQuery("How many customers do we have?")}
                        >
                          • "How many customers do we have?"
                        </div>
                        <div 
                          className="cursor-pointer hover:underline"
                          onClick={() => setAiQuery("Show me recent purchases")}
                        >
                          • "Show me recent purchases"
                        </div>
                      </div>
                    </div>
                    <div className="flex justify-end">
                      <button
                        onClick={processAIQuery}
                        disabled={!aiQuery.trim() || !selectedDataset || isAiProcessing}
                        className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                      >
                        {isAiProcessing && (
                          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                        )}
                        🤖 Generate SQL
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Results */}
            {results && (
              <div className="bg-white shadow rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Query Results</h3>
                  {results.rows && (
                    <div className="flex space-x-2">
                      <button
                        onClick={() => exportResults('csv')}
                        className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                      >
                        Export CSV
                      </button>
                      <button
                        onClick={() => exportResults('json')}
                        className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                      >
                        Export JSON
                      </button>
                    </div>
                  )}
                </div>

                {results.error ? (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
                    {results.error}
                  </div>
                ) : (
                  <div>
                    <div className="mb-4 flex items-center space-x-4 text-sm text-gray-600">
                      <span>{results.rows?.length || 0} rows returned</span>
                      <span>Execution time: {results.execution_time}</span>
                    </div>
                    
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            {results.columns?.map((column: string, index: number) => (
                              <th
                                key={index}
                                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                              >
                                {column}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {results.rows?.map((row: any[], rowIndex: number) => (
                            <tr key={rowIndex}>
                              {row.map((cell, cellIndex) => (
                                <td
                                  key={cellIndex}
                                  className="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
                                >
                                  {cell}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 