'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { 
  ArrowLeft, 
  Play, 
  Download, 
  Share2, 
  Settings, 
  AlertCircle, 
  TrendingUp, 
  Activity,
  Calendar,
  Database,
  Zap,
  BarChart3,
  FileText,
  Clock,
  CheckCircle,
  XCircle
} from 'lucide-react';

interface ModelData {
  id: string;
  name: string;
  description: string;
  engine: string;
  status: 'active' | 'training' | 'failed' | 'stopped';
  accuracy: number;
  totalPredictions: number;
  createdAt: string;
  lastTrainedAt: string;
  trainingTime: number;
  targetColumn: string;
  dataset: {
    id: string;
    name: string;
    rows: number;
    columns: number;
  };
  organization: {
    id: string;
    name: string;
  };
  creator: {
    id: string;
    name: string;
    email: string;
  };
  performance: {
    precision: number;
    recall: number;
    f1Score: number;
    confusionMatrix: number[][];
    featureImportance: Array<{
      feature: string;
      importance: number;
    }>;
  };
  versions: Array<{
    id: string;
    version: string;
    accuracy: number;
    createdAt: string;
    isActive: boolean;
  }>;
  predictions: Array<{
    id: string;
    input: Record<string, any>;
    output: any;
    confidence: number;
    timestamp: string;
  }>;
}

interface PredictionRequest {
  [key: string]: string | number;
}

export default function ModelDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const modelId = params?.id as string;
  
  const [model, setModel] = useState<ModelData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'performance' | 'predictions' | 'versions'>('overview');
  
  // Prediction interface state
  const [predictionInput, setPredictionInput] = useState<PredictionRequest>({});
  const [predictionResult, setPredictionResult] = useState<any>(null);
  const [predictionLoading, setPredictionLoading] = useState(false);
  const [predictionError, setPredictionError] = useState<string | null>(null);

  useEffect(() => {
    fetchModelDetails();
  }, [modelId]);

  const fetchModelDetails = async () => {
    try {
      setLoading(true);
      // Mock data for demonstration - replace with actual API call
      const mockModel: ModelData = {
        id: modelId,
        name: "Customer Churn Prediction Model",
        description: "Advanced machine learning model to predict customer churn based on usage patterns, demographics, and engagement metrics.",
        engine: "LightGBM",
        status: "active",
        accuracy: 0.924,
        totalPredictions: 15847,
        createdAt: "2024-01-10T10:30:00Z",
        lastTrainedAt: "2024-01-15T14:22:00Z",
        trainingTime: 45.6,
        targetColumn: "will_churn",
        dataset: {
          id: "dataset_001",
          name: "Customer_Behavior_Analysis_Q4_2023",
          rows: 50000,
          columns: 23
        },
        organization: {
          id: "org_001",
          name: "TechCorp Analytics"
        },
        creator: {
          id: "user_001",
          name: "Sarah Johnson",
          email: "sarah.johnson@techcorp.com"
        },
        performance: {
          precision: 0.918,
          recall: 0.931,
          f1Score: 0.924,
          confusionMatrix: [
            [8420, 380],
            [340, 8860]
          ],
          featureImportance: [
            { feature: "monthly_charges", importance: 0.284 },
            { feature: "total_charges", importance: 0.192 },
            { feature: "contract_type", importance: 0.156 },
            { feature: "tenure_months", importance: 0.134 },
            { feature: "payment_method", importance: 0.098 },
            { feature: "internet_service", importance: 0.076 },
            { feature: "support_calls", importance: 0.060 }
          ]
        },
        versions: [
          {
            id: "v3",
            version: "3.0.0",
            accuracy: 0.924,
            createdAt: "2024-01-15T14:22:00Z",
            isActive: true
          },
          {
            id: "v2",
            version: "2.1.0",
            accuracy: 0.912,
            createdAt: "2024-01-08T09:15:00Z",
            isActive: false
          },
          {
            id: "v1",
            version: "1.0.0",
            accuracy: 0.887,
            createdAt: "2024-01-01T16:45:00Z",
            isActive: false
          }
        ],
        predictions: [
          {
            id: "pred_001",
            input: { monthly_charges: 85.50, tenure_months: 6, contract_type: "month_to_month" },
            output: { will_churn: true, probability: 0.847 },
            confidence: 0.847,
            timestamp: "2024-01-16T11:30:00Z"
          },
          {
            id: "pred_002",
            input: { monthly_charges: 45.20, tenure_months: 24, contract_type: "two_year" },
            output: { will_churn: false, probability: 0.143 },
            confidence: 0.857,
            timestamp: "2024-01-16T11:28:00Z"
          }
        ]
      };
      
      setModel(mockModel);
      
      // Initialize prediction input with sample values
      setPredictionInput({
        monthly_charges: '',
        tenure_months: '',
        contract_type: '',
        total_charges: '',
        payment_method: '',
        internet_service: '',
        support_calls: ''
      });
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load model details');
    } finally {
      setLoading(false);
    }
  };

  const handlePrediction = async () => {
    try {
      setPredictionLoading(true);
      setPredictionError(null);
      
      // Validate input
      const requiredFields = ['monthly_charges', 'tenure_months', 'contract_type'];
      const missingFields = requiredFields.filter(field => !predictionInput[field]);
      
      if (missingFields.length > 0) {
        setPredictionError(`Please fill in required fields: ${missingFields.join(', ')}`);
        return;
      }
      
      // Mock prediction - replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const mockResult = {
        prediction: Math.random() > 0.5 ? 'Will Churn' : 'Will Not Churn',
        probability: Math.random(),
        confidence: 0.8 + Math.random() * 0.2,
        factors: [
          { factor: 'Monthly Charges', impact: 0.35, direction: 'negative' },
          { factor: 'Tenure', impact: 0.28, direction: 'positive' },
          { factor: 'Contract Type', impact: 0.22, direction: 'negative' }
        ]
      };
      
      setPredictionResult(mockResult);
      
    } catch (err) {
      setPredictionError(err instanceof Error ? err.message : 'Prediction failed');
    } finally {
      setPredictionLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'training': return <Activity className="w-5 h-5 text-blue-600 animate-pulse" />;
      case 'failed': return <XCircle className="w-5 h-5 text-red-600" />;
      case 'stopped': return <AlertCircle className="w-5 h-5 text-gray-600" />;
      default: return <AlertCircle className="w-5 h-5 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'training': return 'bg-blue-100 text-blue-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'stopped': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
            <div className="bg-white rounded-lg shadow h-64"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !model) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="flex items-center">
              <AlertCircle className="w-6 h-6 text-red-600 mr-3" />
              <h2 className="text-lg font-semibold text-red-800">Error Loading Model</h2>
            </div>
            <p className="text-red-700 mt-2">{error || 'Model not found'}</p>
            <button
              onClick={() => router.push('/models')}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Back to Models
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/models')}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Back to Models
          </button>
          
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{model.name}</h1>
              <p className="text-gray-600 mt-2">{model.description}</p>
              <div className="flex items-center mt-3 space-x-4">
                <div className="flex items-center">
                  {getStatusIcon(model.status)}
                  <span className={`ml-2 px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(model.status)}`}>
                    {model.status.charAt(0).toUpperCase() + model.status.slice(1)}
                  </span>
                </div>
                <span className="text-gray-500">•</span>
                <span className="text-gray-600">Engine: {model.engine}</span>
                <span className="text-gray-500">•</span>
                <span className="text-gray-600">ID: {model.id}</span>
              </div>
            </div>
            
            <div className="flex space-x-3">
              <button className="flex items-center px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                <Download className="w-4 h-4 mr-2" />
                Export
              </button>
              <button className="flex items-center px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                <Share2 className="w-4 h-4 mr-2" />
                Share
              </button>
              <button className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                <Settings className="w-4 h-4 mr-2" />
                Settings
              </button>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-3 bg-green-100 rounded-lg">
                <TrendingUp className="w-6 h-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Accuracy</p>
                <p className="text-2xl font-bold text-gray-900">{(model.accuracy * 100).toFixed(1)}%</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Zap className="w-6 h-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Predictions</p>
                <p className="text-2xl font-bold text-gray-900">{model.totalPredictions.toLocaleString()}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-3 bg-purple-100 rounded-lg">
                <Clock className="w-6 h-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Training Time</p>
                <p className="text-2xl font-bold text-gray-900">{model.trainingTime}s</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-3 bg-orange-100 rounded-lg">
                <Database className="w-6 h-6 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Dataset Rows</p>
                <p className="text-2xl font-bold text-gray-900">{model.dataset.rows.toLocaleString()}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {[
                { id: 'overview', label: 'Overview', icon: FileText },
                { id: 'performance', label: 'Performance', icon: BarChart3 },
                { id: 'predictions', label: 'Predictions', icon: Play },
                { id: 'versions', label: 'Versions', icon: Calendar }
              ].map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`flex items-center py-4 px-2 border-b-2 font-medium text-sm ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <Icon className="w-4 h-4 mr-2" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Model Information */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Model Information</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Target Column:</span>
                        <span className="font-medium">{model.targetColumn}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Engine:</span>
                        <span className="font-medium">{model.engine}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Created By:</span>
                        <span className="font-medium">{model.creator.name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Organization:</span>
                        <span className="font-medium">{model.organization.name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Created:</span>
                        <span className="font-medium">{new Date(model.createdAt).toLocaleDateString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Last Trained:</span>
                        <span className="font-medium">{new Date(model.lastTrainedAt).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Dataset Information</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Dataset Name:</span>
                        <span className="font-medium">{model.dataset.name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Rows:</span>
                        <span className="font-medium">{model.dataset.rows.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Columns:</span>
                        <span className="font-medium">{model.dataset.columns}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Interactive Prediction */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Make a Prediction</h3>
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                      {Object.keys(predictionInput).map((field) => (
                        <div key={field}>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            {field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </label>
                          <input
                            type={field.includes('charges') || field.includes('months') || field.includes('calls') ? 'number' : 'text'}
                            value={predictionInput[field]}
                            onChange={(e) => setPredictionInput({
                              ...predictionInput,
                              [field]: e.target.value
                            })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder={field.includes('type') || field.includes('method') || field.includes('service') 
                              ? 'Enter option' 
                              : 'Enter value'}
                          />
                        </div>
                      ))}
                    </div>
                    
                    <button
                      onClick={handlePrediction}
                      disabled={predictionLoading}
                      className="flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {predictionLoading ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Running Prediction...
                        </>
                      ) : (
                        <>
                          <Play className="w-4 h-4 mr-2" />
                          Run Prediction
                        </>
                      )}
                    </button>
                    
                    {predictionError && (
                      <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-red-700">{predictionError}</p>
                      </div>
                    )}
                    
                    {predictionResult && (
                      <div className="mt-6 p-6 bg-white border border-gray-200 rounded-lg">
                        <h4 className="text-lg font-semibold text-gray-900 mb-4">Prediction Result</h4>
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                          <div>
                            <div className="space-y-3">
                              <div className="flex justify-between">
                                <span className="text-gray-600">Prediction:</span>
                                <span className={`font-bold ${predictionResult.prediction.includes('Will Churn') ? 'text-red-600' : 'text-green-600'}`}>
                                  {predictionResult.prediction}
                                </span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600">Probability:</span>
                                <span className="font-medium">{(predictionResult.probability * 100).toFixed(1)}%</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600">Confidence:</span>
                                <span className="font-medium">{(predictionResult.confidence * 100).toFixed(1)}%</span>
                              </div>
                            </div>
                          </div>
                          
                          <div>
                            <h5 className="font-medium text-gray-900 mb-3">Key Factors</h5>
                            <div className="space-y-2">
                              {predictionResult.factors.map((factor: any, index: number) => (
                                <div key={index} className="flex items-center justify-between">
                                  <span className="text-sm text-gray-600">{factor.factor}</span>
                                  <div className="flex items-center">
                                    <div className={`w-2 h-2 rounded-full mr-2 ${factor.direction === 'positive' ? 'bg-green-400' : 'bg-red-400'}`}></div>
                                    <span className="text-sm font-medium">{(factor.impact * 100).toFixed(1)}%</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'performance' && (
              <div className="space-y-6">
                {/* Performance Metrics */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="bg-blue-50 p-6 rounded-lg">
                    <h4 className="font-semibold text-blue-900 mb-2">Precision</h4>
                    <p className="text-3xl font-bold text-blue-600">{(model.performance.precision * 100).toFixed(1)}%</p>
                    <p className="text-sm text-blue-700 mt-1">True Positives / (True Positives + False Positives)</p>
                  </div>
                  
                  <div className="bg-green-50 p-6 rounded-lg">
                    <h4 className="font-semibold text-green-900 mb-2">Recall</h4>
                    <p className="text-3xl font-bold text-green-600">{(model.performance.recall * 100).toFixed(1)}%</p>
                    <p className="text-sm text-green-700 mt-1">True Positives / (True Positives + False Negatives)</p>
                  </div>
                  
                  <div className="bg-purple-50 p-6 rounded-lg">
                    <h4 className="font-semibold text-purple-900 mb-2">F1 Score</h4>
                    <p className="text-3xl font-bold text-purple-600">{(model.performance.f1Score * 100).toFixed(1)}%</p>
                    <p className="text-sm text-purple-700 mt-1">Harmonic mean of Precision and Recall</p>
                  </div>
                </div>

                {/* Feature Importance */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Feature Importance</h3>
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <div className="space-y-4">
                      {model.performance.featureImportance.map((feature, index) => (
                        <div key={index}>
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-sm font-medium text-gray-700">{feature.feature}</span>
                            <span className="text-sm text-gray-600">{(feature.importance * 100).toFixed(1)}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full" 
                              style={{ width: `${feature.importance * 100}%` }}
                            ></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Confusion Matrix */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Confusion Matrix</h3>
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <div className="grid grid-cols-2 gap-4 max-w-md">
                      <div className="text-center">
                        <div className="bg-green-100 p-4 rounded-lg">
                          <p className="text-2xl font-bold text-green-600">{model.performance.confusionMatrix[0][0]}</p>
                          <p className="text-sm text-green-700">True Negatives</p>
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="bg-red-100 p-4 rounded-lg">
                          <p className="text-2xl font-bold text-red-600">{model.performance.confusionMatrix[0][1]}</p>
                          <p className="text-sm text-red-700">False Positives</p>
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="bg-red-100 p-4 rounded-lg">
                          <p className="text-2xl font-bold text-red-600">{model.performance.confusionMatrix[1][0]}</p>
                          <p className="text-sm text-red-700">False Negatives</p>
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="bg-green-100 p-4 rounded-lg">
                          <p className="text-2xl font-bold text-green-600">{model.performance.confusionMatrix[1][1]}</p>
                          <p className="text-sm text-green-700">True Positives</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'predictions' && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-semibold text-gray-900">Recent Predictions</h3>
                  <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                    Export All
                  </button>
                </div>
                
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Timestamp
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Input
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Output
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Confidence
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {model.predictions.map((prediction) => (
                        <tr key={prediction.id}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {new Date(prediction.timestamp).toLocaleString()}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-900">
                            <div className="max-w-xs overflow-hidden">
                              {Object.entries(prediction.input).map(([key, value]) => (
                                <div key={key} className="text-xs">
                                  <span className="font-medium">{key}:</span> {value}
                                </div>
                              ))}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              prediction.output.will_churn ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                            }`}>
                              {prediction.output.will_churn ? 'Will Churn' : 'Will Not Churn'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            <div className="flex items-center">
                              <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                                <div 
                                  className="bg-blue-600 h-2 rounded-full" 
                                  style={{ width: `${prediction.confidence * 100}%` }}
                                ></div>
                              </div>
                              <span>{(prediction.confidence * 100).toFixed(1)}%</span>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'versions' && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-semibold text-gray-900">Model Versions</h3>
                  <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                    Create New Version
                  </button>
                </div>
                
                <div className="space-y-4">
                  {model.versions.map((version) => (
                    <div key={version.id} className={`border rounded-lg p-6 ${version.isActive ? 'border-blue-200 bg-blue-50' : 'border-gray-200 bg-white'}`}>
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="flex items-center">
                            <h4 className="text-lg font-semibold text-gray-900">{version.version}</h4>
                            {version.isActive && (
                              <span className="ml-3 px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
                                Active
                              </span>
                            )}
                          </div>
                          <p className="text-gray-600 mt-1">
                            Created on {new Date(version.createdAt).toLocaleDateString()}
                          </p>
                          <div className="mt-3">
                            <span className="text-sm text-gray-600">Accuracy: </span>
                            <span className="text-sm font-semibold text-green-600">
                              {(version.accuracy * 100).toFixed(1)}%
                            </span>
                          </div>
                        </div>
                        
                        <div className="flex space-x-2">
                          {!version.isActive && (
                            <button className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50">
                              Activate
                            </button>
                          )}
                          <button className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50">
                            Compare
                          </button>
                          <button className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50">
                            Download
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 