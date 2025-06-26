'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useAuth } from '@/components/auth/AuthProvider';
import { useState, useEffect } from 'react';
import { mindsdbAPI } from '@/lib/api';
import Link from 'next/link';

export default function ModelsPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <ModelsContent />
      </DashboardLayout>
    </ProtectedRoute>
  );
}

function ModelsContent() {
  const { user } = useAuth();
  const [models, setModels] = useState<any[]>([]);
  const [filteredModels, setFilteredModels] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterEngine, setFilterEngine] = useState('all');

  useEffect(() => {
    fetchModels();
  }, []);

  useEffect(() => {
    filterModels();
  }, [models, searchTerm, filterStatus, filterEngine]);

  const fetchModels = async () => {
    try {
      setIsLoading(true);
      
      // Mock data for demonstration
      const mockModels = [
        {
          id: 1,
          name: 'customer_churn_predictor',
          type: 'classifier',
          engine: 'lightgbm',
          status: 'complete',
          accuracy: 0.87,
          dataset: 'Customer Sales Data',
          target_column: 'will_churn',
          created_at: '2024-01-15T10:30:00Z',
          prediction_count: 1250,
        },
        {
          id: 2,
          name: 'sales_forecasting_model',
          type: 'regressor',
          engine: 'neural_network',
          status: 'training',
          dataset: 'Marketing Analytics',
          target_column: 'monthly_sales',
          created_at: '2024-01-16T09:15:00Z',
          prediction_count: 0,
        }
      ];
      
      setModels(mockModels);
    } catch (error) {
      console.error('Failed to fetch models:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const filterModels = () => {
    let filtered = models;

    if (searchTerm) {
      filtered = filtered.filter(model =>
        model.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        model.dataset?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (filterStatus !== 'all') {
      filtered = filtered.filter(model => model.status === filterStatus);
    }

    if (filterEngine !== 'all') {
      filtered = filtered.filter(model => model.engine === filterEngine);
    }

    setFilteredModels(filtered);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'complete': return 'bg-green-100 text-green-800';
      case 'training': return 'bg-yellow-100 text-yellow-800';
      case 'error': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getEngineColor = (engine: string) => {
    switch (engine) {
      case 'lightgbm': return 'bg-blue-100 text-blue-800';
      case 'neural_network': return 'bg-purple-100 text-purple-800';
      case 'openai': return 'bg-green-100 text-green-800';
      case 'google': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const handleDeleteModel = async (modelId: number, modelName: string) => {
    if (!confirm(`Are you sure you want to delete the model "${modelName}"?`)) return;

    try {
      await mindsdbAPI.deleteModel(modelName);
      setModels(models.filter(m => m.id !== modelId));
    } catch (error) {
      console.error('Failed to delete model:', error);
    }
  };

  const handleRetrainModel = async (modelName: string) => {
    try {
      // TODO: Implement retrain functionality
      console.log('Retraining model:', modelName);
    } catch (error) {
      console.error('Failed to retrain model:', error);
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
              <h1 className="text-2xl font-bold text-gray-900">AI Models</h1>
              <p className="mt-1 text-sm text-gray-600">
                Manage and monitor your organization's machine learning models.
              </p>
            </div>
            <Link
              href="/models/create"
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
            >
              Create Model
            </Link>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Active Models</dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {models.filter(m => m.status === 'complete').length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-purple-500 rounded-md flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total Predictions</dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {models.reduce((sum, m) => sum + (m.prediction_count || 0), 0).toLocaleString()}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white shadow rounded-lg mb-6">
          <div className="p-6">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search models..."
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="all">All Status</option>
                  <option value="complete">Complete</option>
                  <option value="training">Training</option>
                  <option value="error">Error</option>
                  <option value="pending">Pending</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Engine</label>
                <select
                  value={filterEngine}
                  onChange={(e) => setFilterEngine(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="all">All Engines</option>
                  <option value="lightgbm">LightGBM</option>
                  <option value="neural_network">Neural Network</option>
                  <option value="openai">OpenAI</option>
                  <option value="google">Google</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Models List */}
        {filteredModels.length === 0 ? (
          <div className="bg-white shadow rounded-lg">
            <div className="text-center py-12">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No models found</h3>
              <p className="mt-1 text-sm text-gray-500">
                {models.length === 0 
                  ? "Get started by creating your first AI model." 
                  : "Try adjusting your search or filter criteria."
                }
              </p>
              {models.length === 0 && (
                <div className="mt-6">
                  <Link
                    href="/models/create"
                    className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                  >
                    Create Model
                  </Link>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul className="divide-y divide-gray-200">
              {filteredModels.map((model) => (
                <li key={model.id}>
                  <div className="px-6 py-4 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3">
                          <h3 className="text-lg font-medium text-gray-900 truncate">
                            {model.name}
                          </h3>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(model.status)}`}>
                            {model.status.charAt(0).toUpperCase() + model.status.slice(1)}
                          </span>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getEngineColor(model.engine)}`}>
                            {model.engine}
                          </span>
                        </div>
                        
                        <div className="mt-2 flex items-center space-x-6 text-sm text-gray-500">
                          <span>Dataset: {model.dataset}</span>
                          <span>Target: {model.target_column}</span>
                          {model.accuracy && (
                            <span>Accuracy: {Math.round(model.accuracy * 100)}%</span>
                          )}
                          <span>Predictions: {model.prediction_count.toLocaleString()}</span>
                          <span>Created: {new Date(model.created_at).toLocaleDateString()}</span>
                        </div>

                        {model.error_message && (
                          <div className="mt-2 text-sm text-red-600">
                            Error: {model.error_message}
                          </div>
                        )}
                      </div>

                      <div className="flex items-center space-x-2">
                        <Link
                          href={`/models/${model.id}`}
                          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                        >
                          View
                        </Link>
                        {model.status === 'complete' && (
                          <>
                            <button
                              onClick={() => window.open(`/models/${model.id}/predict`, '_blank')}
                              className="text-green-600 hover:text-green-800 text-sm font-medium"
                            >
                              Predict
                            </button>
                            <button
                              onClick={() => handleRetrainModel(model.name)}
                              className="text-yellow-600 hover:text-yellow-800 text-sm font-medium"
                            >
                              Retrain
                            </button>
                          </>
                        )}
                        <button
                          onClick={() => handleDeleteModel(model.id, model.name)}
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
        )}

        {/* Summary */}
        <div className="mt-6 bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>Showing {filteredModels.length} of {models.length} models</span>
            <span>
              Total predictions: {models.reduce((sum, m) => sum + (m.prediction_count || 0), 0).toLocaleString()}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
} 