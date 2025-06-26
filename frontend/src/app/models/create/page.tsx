'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useAuth } from '@/components/auth/AuthProvider';
import { useState, useEffect } from 'react';
import { datasetsAPI, mindsdbAPI } from '@/lib/api';
import { useRouter } from 'next/navigation';

export default function CreateModelPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <CreateModelContent />
      </DashboardLayout>
    </ProtectedRoute>
  );
}

function CreateModelContent() {
  const { user } = useAuth();
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [datasets, setDatasets] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    dataset_id: '',
    target_column: '',
    feature_columns: [] as string[],
    engine: 'lightgbm',
    model_type: 'auto',
    advanced_settings: {}
  });

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      // Mock datasets for demo
      const mockDatasets = [
        {
          id: 1,
          name: 'Customer Sales Data',
          description: 'Customer transaction and behavior data',
          columns: ['customer_id', 'age', 'income', 'purchase_amount', 'will_churn'],
          row_count: 15000
        },
        {
          id: 2,
          name: 'Marketing Analytics',
          description: 'Campaign performance and conversion data',
          columns: ['campaign_id', 'clicks', 'impressions', 'cost', 'conversions'],
          row_count: 5000
        }
      ];
      setDatasets(mockDatasets);
    } catch (error) {
      console.error('Failed to fetch datasets:', error);
    }
  };

  const handleNext = () => {
    setCurrentStep(currentStep + 1);
  };

  const handleBack = () => {
    setCurrentStep(currentStep - 1);
  };

  const handleSubmit = async () => {
    try {
      setIsLoading(true);
      
      const modelConfig = {
        name: formData.name,
        description: formData.description,
        dataset_id: formData.dataset_id,
        target_column: formData.target_column,
        feature_columns: formData.feature_columns,
        engine: formData.engine,
        model_type: formData.model_type
      };

      // TODO: Replace with actual API call
      console.log('Creating model:', modelConfig);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      router.push('/models');
    } catch (error) {
      console.error('Failed to create model:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const selectedDataset = datasets.find(d => d.id.toString() === formData.dataset_id);

  return (
    <div className="py-6">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Create AI Model</h1>
          <p className="mt-1 text-sm text-gray-600">
            Build a new machine learning model for your organization.
          </p>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <nav aria-label="Progress">
            <ol className="flex items-center">
              {[
                { id: 1, name: 'Basic Info', status: currentStep >= 1 ? 'complete' : 'upcoming' },
                { id: 2, name: 'Data Selection', status: currentStep >= 2 ? 'complete' : currentStep === 2 ? 'current' : 'upcoming' },
                { id: 3, name: 'Model Configuration', status: currentStep >= 3 ? 'complete' : currentStep === 3 ? 'current' : 'upcoming' },
                { id: 4, name: 'Review & Create', status: currentStep === 4 ? 'current' : currentStep > 4 ? 'complete' : 'upcoming' },
              ].map((step, stepIdx) => (
                <li key={step.name} className={stepIdx !== 3 ? 'flex-1' : ''}>
                  <div className="flex items-center">
                    <div className="relative flex items-center justify-center">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                        step.status === 'complete' ? 'bg-blue-600 text-white' :
                        step.status === 'current' ? 'bg-blue-100 text-blue-600 border-2 border-blue-600' :
                        'bg-gray-100 text-gray-400'
                      }`}>
                        {step.status === 'complete' ? (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        ) : (
                          step.id
                        )}
                      </div>
                    </div>
                    <div className="ml-4 text-sm font-medium text-gray-900">{step.name}</div>
                    {stepIdx !== 3 && (
                      <div className="flex-1 ml-4 h-0.5 bg-gray-200" />
                    )}
                  </div>
                </li>
              ))}
            </ol>
          </nav>
        </div>

        {/* Form Content */}
        <div className="bg-white shadow rounded-lg">
          <div className="p-6">
            {/* Step 1: Basic Info */}
            {currentStep === 1 && (
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Model Name
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    placeholder="e.g., customer_churn_predictor"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    rows={3}
                    placeholder="Describe what this model will predict..."
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            )}

            {/* Step 2: Data Selection */}
            {currentStep === 2 && (
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Dataset
                  </label>
                  <select
                    value={formData.dataset_id}
                    onChange={(e) => setFormData({...formData, dataset_id: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Choose a dataset...</option>
                    {datasets.map((dataset) => (
                      <option key={dataset.id} value={dataset.id}>
                        {dataset.name} ({dataset.row_count.toLocaleString()} rows)
                      </option>
                    ))}
                  </select>
                </div>

                {selectedDataset && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">Dataset Preview</h4>
                    <p className="text-sm text-gray-600 mb-3">{selectedDataset.description}</p>
                    <div className="text-sm">
                      <strong>Columns:</strong> {selectedDataset.columns.join(', ')}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Step 3: Model Configuration */}
            {currentStep === 3 && selectedDataset && (
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Target Column (What to predict)
                  </label>
                  <select
                    value={formData.target_column}
                    onChange={(e) => setFormData({...formData, target_column: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select target column...</option>
                    {selectedDataset.columns.map((column) => (
                      <option key={column} value={column}>
                        {column}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    ML Engine
                  </label>
                  <select
                    value={formData.engine}
                    onChange={(e) => setFormData({...formData, engine: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="lightgbm">LightGBM (Recommended)</option>
                    <option value="neural_network">Neural Network</option>
                    <option value="openai">OpenAI</option>
                    <option value="google">Google AI</option>
                  </select>
                </div>
              </div>
            )}

            {/* Step 4: Review */}
            {currentStep === 4 && (
              <div className="space-y-6">
                <h3 className="text-lg font-medium text-gray-900">Review Model Configuration</h3>
                
                <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                  <div><strong>Name:</strong> {formData.name}</div>
                  <div><strong>Description:</strong> {formData.description}</div>
                  <div><strong>Dataset:</strong> {selectedDataset?.name}</div>
                  <div><strong>Target Column:</strong> {formData.target_column}</div>
                  <div><strong>Engine:</strong> {formData.engine}</div>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex">
                    <svg className="flex-shrink-0 w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div className="ml-3">
                      <p className="text-sm text-blue-700">
                        Model training will begin once created and may take several minutes depending on data size.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Navigation */}
          <div className="px-6 py-4 bg-gray-50 flex justify-between">
            <button
              onClick={handleBack}
              disabled={currentStep === 1}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Back
            </button>
            
            <div className="flex space-x-3">
              {currentStep < 4 ? (
                <button
                  onClick={handleNext}
                  disabled={
                    (currentStep === 1 && !formData.name) ||
                    (currentStep === 2 && !formData.dataset_id) ||
                    (currentStep === 3 && !formData.target_column)
                  }
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={isLoading}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  {isLoading && (
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  )}
                  Create Model
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 