'use client';

import { useState, useEffect } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Users, 
  Database, 
  Activity,
  Calendar,
  Download,
  Filter,
  RefreshCw,
  Eye,
  Share2,
  Clock,
  Zap,
  HardDrive,
  DollarSign,
  Target,
  AlertTriangle,
  CheckCircle,
  Layers
} from 'lucide-react';

interface AnalyticsData {
  organization: {
    id: string;
    name: string;
    totalUsers: number;
    totalDatasets: number;
    totalModels: number;
    storageUsed: number;
    storageLimit: number;
  };
  usage: {
    totalApiCalls: number;
    totalPredictions: number;
    averageResponseTime: number;
    uptime: number;
  };
  trends: {
    datasetUploads: Array<{ date: string; count: number }>;
    modelCreations: Array<{ date: string; count: number }>;
    predictions: Array<{ date: string; count: number }>;
    userActivity: Array<{ date: string; active_users: number }>;
  };
  modelPerformance: Array<{
    id: string;
    name: string;
    accuracy: number;
    predictions: number;
    lastUpdated: string;
    status: 'excellent' | 'good' | 'needs_attention';
  }>;
  userActivity: Array<{
    userId: string;
    name: string;
    lastActive: string;
    actionsToday: number;
    role: string;
    department: string;
  }>;
  dataUsage: {
    mostAccessedDatasets: Array<{
      id: string;
      name: string;
      accessCount: number;
      lastAccessed: string;
      sharingLevel: string;
    }>;
    storageByDepartment: Array<{
      department: string;
      storage: number;
      percentage: number;
    }>;
  };
  costs: {
    totalCost: number;
    costByCategory: Array<{
      category: string;
      amount: number;
      percentage: number;
    }>;
    projectedMonthlyCost: number;
  };
}

interface DateRange {
  start: string;
  end: string;
  label: string;
}

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDateRange, setSelectedDateRange] = useState<DateRange>({
    start: '2024-01-01',
    end: '2024-01-16',
    label: 'Last 30 Days'
  });
  const [activeTab, setActiveTab] = useState<'overview' | 'models' | 'users' | 'data' | 'costs'>('overview');

  const dateRanges: DateRange[] = [
    { start: '2024-01-16', end: '2024-01-16', label: 'Today' },
    { start: '2024-01-09', end: '2024-01-16', label: 'Last 7 Days' },
    { start: '2024-01-01', end: '2024-01-16', label: 'Last 30 Days' },
    { start: '2023-10-01', end: '2024-01-16', label: 'Last 3 Months' }
  ];

  useEffect(() => {
    fetchAnalytics();
  }, [selectedDateRange]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      
      // Mock analytics data - replace with actual API call
      const mockAnalytics: AnalyticsData = {
        organization: {
          id: "org_001",
          name: "TechCorp Analytics",
          totalUsers: 127,
          totalDatasets: 89,
          totalModels: 34,
          storageUsed: 245.7, // GB
          storageLimit: 500 // GB
        },
        usage: {
          totalApiCalls: 45678,
          totalPredictions: 123456,
          averageResponseTime: 245, // ms
          uptime: 99.7 // percentage
        },
        trends: {
          datasetUploads: [
            { date: '2024-01-10', count: 12 },
            { date: '2024-01-11', count: 8 },
            { date: '2024-01-12', count: 15 },
            { date: '2024-01-13', count: 18 },
            { date: '2024-01-14', count: 22 },
            { date: '2024-01-15', count: 19 },
            { date: '2024-01-16', count: 14 }
          ],
          modelCreations: [
            { date: '2024-01-10', count: 3 },
            { date: '2024-01-11', count: 2 },
            { date: '2024-01-12', count: 5 },
            { date: '2024-01-13', count: 4 },
            { date: '2024-01-14', count: 6 },
            { date: '2024-01-15', count: 3 },
            { date: '2024-01-16', count: 2 }
          ],
          predictions: [
            { date: '2024-01-10', count: 1250 },
            { date: '2024-01-11', count: 1100 },
            { date: '2024-01-12', count: 1450 },
            { date: '2024-01-13', count: 1680 },
            { date: '2024-01-14', count: 1920 },
            { date: '2024-01-15', count: 1750 },
            { date: '2024-01-16', count: 1340 }
          ],
          userActivity: [
            { date: '2024-01-10', active_users: 89 },
            { date: '2024-01-11', active_users: 76 },
            { date: '2024-01-12', active_users: 94 },
            { date: '2024-01-13', active_users: 102 },
            { date: '2024-01-14', active_users: 98 },
            { date: '2024-01-15', active_users: 87 },
            { date: '2024-01-16', active_users: 91 }
          ]
        },
        modelPerformance: [
          {
            id: "model_001",
            name: "Customer Churn Prediction",
            accuracy: 0.924,
            predictions: 15847,
            lastUpdated: "2024-01-15T14:22:00Z",
            status: "excellent"
          },
          {
            id: "model_002",
            name: "Sales Forecasting",
            accuracy: 0.887,
            predictions: 8932,
            lastUpdated: "2024-01-14T09:15:00Z",
            status: "good"
          },
          {
            id: "model_003",
            name: "Demand Prediction",
            accuracy: 0.756,
            predictions: 3421,
            lastUpdated: "2024-01-12T16:45:00Z",
            status: "needs_attention"
          },
          {
            id: "model_004",
            name: "Price Optimization",
            accuracy: 0.913,
            predictions: 12054,
            lastUpdated: "2024-01-16T11:30:00Z",
            status: "excellent"
          }
        ],
        userActivity: [
          {
            userId: "user_001",
            name: "Sarah Johnson",
            lastActive: "2024-01-16T14:22:00Z",
            actionsToday: 23,
            role: "Data Scientist",
            department: "Analytics"
          },
          {
            userId: "user_002",
            name: "Mike Chen",
            lastActive: "2024-01-16T13:45:00Z",
            actionsToday: 17,
            role: "Manager",
            department: "Engineering"
          },
          {
            userId: "user_003",
            name: "Emily Rodriguez",
            lastActive: "2024-01-16T12:30:00Z",
            actionsToday: 31,
            role: "Admin",
            department: "IT"
          },
          {
            userId: "user_004",
            name: "David Kim",
            lastActive: "2024-01-16T11:15:00Z",
            actionsToday: 12,
            role: "Analyst",
            department: "Marketing"
          }
        ],
        dataUsage: {
          mostAccessedDatasets: [
            {
              id: "dataset_001",
              name: "Customer_Behavior_Analysis_Q4_2023",
              accessCount: 247,
              lastAccessed: "2024-01-16T13:20:00Z",
              sharingLevel: "ORGANIZATION"
            },
            {
              id: "dataset_002",
              name: "Sales_Data_2023_Complete",
              accessCount: 189,
              lastAccessed: "2024-01-16T12:45:00Z",
              sharingLevel: "DEPARTMENT"
            },
            {
              id: "dataset_003",
              name: "Market_Research_Consumer_Trends",
              accessCount: 156,
              lastAccessed: "2024-01-16T11:30:00Z",
              sharingLevel: "ORGANIZATION"
            }
          ],
          storageByDepartment: [
            { department: "Analytics", storage: 89.4, percentage: 36.4 },
            { department: "Engineering", storage: 67.2, percentage: 27.3 },
            { department: "Marketing", storage: 45.8, percentage: 18.6 },
            { department: "IT", storage: 28.9, percentage: 11.8 },
            { department: "Sales", storage: 14.4, percentage: 5.9 }
          ]
        },
        costs: {
          totalCost: 2847.50,
          costByCategory: [
            { category: "Storage", amount: 1245.30, percentage: 43.7 },
            { category: "API Calls", amount: 892.15, percentage: 31.3 },
            { category: "Model Training", amount: 456.78, percentage: 16.0 },
            { category: "Data Processing", amount: 253.27, percentage: 8.9 }
          ],
          projectedMonthlyCost: 8542.50
        }
      };
      
      setAnalytics(mockAnalytics);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'excellent': return 'text-green-600 bg-green-100';
      case 'good': return 'text-blue-600 bg-blue-100';
      case 'needs_attention': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'excellent': return <CheckCircle className="w-4 h-4" />;
      case 'good': return <Target className="w-4 h-4" />;
      case 'needs_attention': return <AlertTriangle className="w-4 h-4" />;
      default: return <Activity className="w-4 h-4" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="bg-white p-6 rounded-lg shadow h-32"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="flex items-center">
              <AlertTriangle className="w-6 h-6 text-red-600 mr-3" />
              <h2 className="text-lg font-semibold text-red-800">Error Loading Analytics</h2>
            </div>
            <p className="text-red-700 mt-2">{error || 'Analytics data not available'}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
            <p className="text-gray-600 mt-2">Organization insights and performance metrics for {analytics.organization.name}</p>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Date Range Selector */}
            <div className="relative">
              <select
                value={selectedDateRange.label}
                onChange={(e) => {
                  const range = dateRanges.find(r => r.label === e.target.value);
                  if (range) setSelectedDateRange(range);
                }}
                className="appearance-none bg-white border border-gray-300 rounded-lg px-4 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {dateRanges.map((range) => (
                  <option key={range.label} value={range.label}>{range.label}</option>
                ))}
              </select>
              <Calendar className="absolute right-2 top-2.5 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>
            
            <button
              onClick={fetchAnalytics}
              className="flex items-center px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </button>
            
            <button className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              <Download className="w-4 h-4 mr-2" />
              Export Report
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Active Users</p>
                <p className="text-2xl font-bold text-gray-900">{analytics.organization.totalUsers}</p>
                <p className="text-sm text-green-600">+12% from last month</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-3 bg-green-100 rounded-lg">
                <Database className="w-6 h-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Datasets</p>
                <p className="text-2xl font-bold text-gray-900">{analytics.organization.totalDatasets}</p>
                <p className="text-sm text-green-600">+8% from last month</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-3 bg-purple-100 rounded-lg">
                <BarChart3 className="w-6 h-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">AI Models</p>
                <p className="text-2xl font-bold text-gray-900">{analytics.organization.totalModels}</p>
                <p className="text-sm text-green-600">+15% from last month</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-3 bg-orange-100 rounded-lg">
                <Zap className="w-6 h-6 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Predictions</p>
                <p className="text-2xl font-bold text-gray-900">{analytics.usage.totalPredictions.toLocaleString()}</p>
                <p className="text-sm text-green-600">+23% from last month</p>
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {[
                { id: 'overview', label: 'Overview', icon: BarChart3 },
                { id: 'models', label: 'Model Performance', icon: Target },
                { id: 'users', label: 'User Activity', icon: Users },
                { id: 'data', label: 'Data Usage', icon: Database },
                { id: 'costs', label: 'Cost Analysis', icon: DollarSign }
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
                {/* System Health */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="bg-gradient-to-r from-green-50 to-green-100 p-6 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-semibold text-green-900">System Uptime</h3>
                        <p className="text-3xl font-bold text-green-600">{analytics.usage.uptime}%</p>
                        <p className="text-sm text-green-700">Last 30 days</p>
                      </div>
                      <CheckCircle className="w-12 h-12 text-green-600" />
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-6 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-semibold text-blue-900">Avg Response Time</h3>
                        <p className="text-3xl font-bold text-blue-600">{analytics.usage.averageResponseTime}ms</p>
                        <p className="text-sm text-blue-700">API responses</p>
                      </div>
                      <Activity className="w-12 h-12 text-blue-600" />
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-r from-orange-50 to-orange-100 p-6 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-semibold text-orange-900">Storage Used</h3>
                        <p className="text-3xl font-bold text-orange-600">{analytics.organization.storageUsed}GB</p>
                        <p className="text-sm text-orange-700">of {analytics.organization.storageLimit}GB</p>
                      </div>
                      <HardDrive className="w-12 h-12 text-orange-600" />
                    </div>
                  </div>
                </div>

                {/* Activity Trends */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Dataset Uploads Trend</h3>
                    <div className="space-y-3">
                      {analytics.trends.datasetUploads.slice(-5).map((item, index) => (
                        <div key={index} className="flex items-center justify-between">
                          <span className="text-sm text-gray-600">{new Date(item.date).toLocaleDateString()}</span>
                          <div className="flex items-center">
                            <div className="w-20 bg-gray-200 rounded-full h-2 mr-3">
                              <div 
                                className="bg-blue-600 h-2 rounded-full" 
                                style={{ width: `${(item.count / 25) * 100}%` }}
                              ></div>
                            </div>
                            <span className="text-sm font-medium">{item.count}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Model Predictions Trend</h3>
                    <div className="space-y-3">
                      {analytics.trends.predictions.slice(-5).map((item, index) => (
                        <div key={index} className="flex items-center justify-between">
                          <span className="text-sm text-gray-600">{new Date(item.date).toLocaleDateString()}</span>
                          <div className="flex items-center">
                            <div className="w-20 bg-gray-200 rounded-full h-2 mr-3">
                              <div 
                                className="bg-green-600 h-2 rounded-full" 
                                style={{ width: `${(item.count / 2000) * 100}%` }}
                              ></div>
                            </div>
                            <span className="text-sm font-medium">{item.count.toLocaleString()}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Storage Usage by Department */}
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Storage Usage by Department</h3>
                  <div className="space-y-4">
                    {analytics.dataUsage.storageByDepartment.map((dept, index) => (
                      <div key={index}>
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm font-medium text-gray-700">{dept.department}</span>
                          <span className="text-sm text-gray-600">{dept.storage}GB ({dept.percentage}%)</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{ width: `${dept.percentage}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'models' && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-semibold text-gray-900">Model Performance Overview</h3>
                  <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                    Performance Report
                  </button>
                </div>
                
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-2 gap-6">
                  {analytics.modelPerformance.map((model) => (
                    <div key={model.id} className="bg-white border border-gray-200 rounded-lg p-6">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="text-lg font-semibold text-gray-900">{model.name}</h4>
                        <div className={`flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(model.status)}`}>
                          {getStatusIcon(model.status)}
                          <span className="ml-1 capitalize">{model.status.replace('_', ' ')}</span>
                        </div>
                      </div>
                      
                      <div className="space-y-4">
                        <div>
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-sm text-gray-600">Accuracy</span>
                            <span className="text-sm font-medium">{(model.accuracy * 100).toFixed(1)}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className={`h-2 rounded-full ${
                                model.accuracy >= 0.9 ? 'bg-green-600' : 
                                model.accuracy >= 0.8 ? 'bg-blue-600' : 'bg-red-600'
                              }`}
                              style={{ width: `${model.accuracy * 100}%` }}
                            ></div>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <p className="text-sm text-gray-600">Predictions</p>
                            <p className="text-lg font-semibold text-gray-900">{model.predictions.toLocaleString()}</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">Last Updated</p>
                            <p className="text-sm text-gray-900">{new Date(model.lastUpdated).toLocaleDateString()}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'users' && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-semibold text-gray-900">User Activity Overview</h3>
                  <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                    Activity Report
                  </button>
                </div>
                
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          User
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Role
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Department
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions Today
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Last Active
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {analytics.userActivity.map((user) => (
                        <tr key={user.userId}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                                <span className="text-sm font-medium text-blue-600">
                                  {user.name.split(' ').map(n => n[0]).join('')}
                                </span>
                              </div>
                              <div className="ml-3">
                                <p className="text-sm font-medium text-gray-900">{user.name}</p>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {user.role}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {user.department}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                              {user.actionsToday} actions
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {new Date(user.lastActive).toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'data' && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-semibold text-gray-900">Data Usage Analysis</h3>
                  <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                    Usage Report
                  </button>
                </div>
                
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">Most Accessed Datasets</h4>
                  <div className="space-y-4">
                    {analytics.dataUsage.mostAccessedDatasets.map((dataset, index) => (
                      <div key={dataset.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div className="flex items-center">
                          <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
                            <Database className="w-4 h-4 text-blue-600" />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-gray-900">{dataset.name}</p>
                            <p className="text-xs text-gray-600">
                              {dataset.accessCount} accesses • Last accessed {new Date(dataset.lastAccessed).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            dataset.sharingLevel === 'ORGANIZATION' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-blue-100 text-blue-800'
                          }`}>
                            {dataset.sharingLevel}
                          </span>
                          <button className="p-1 text-gray-400 hover:text-gray-600">
                            <Eye className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'costs' && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-semibold text-gray-900">Cost Analysis</h3>
                  <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                    Cost Report
                  </button>
                </div>
                
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="bg-gradient-to-r from-green-50 to-green-100 p-6 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-lg font-semibold text-green-900">Current Month</h4>
                        <p className="text-3xl font-bold text-green-600">${analytics.costs.totalCost.toLocaleString()}</p>
                        <p className="text-sm text-green-700">Total cost to date</p>
                      </div>
                      <DollarSign className="w-12 h-12 text-green-600" />
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-6 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-lg font-semibold text-blue-900">Projected Monthly</h4>
                        <p className="text-3xl font-bold text-blue-600">${analytics.costs.projectedMonthlyCost.toLocaleString()}</p>
                        <p className="text-sm text-blue-700">Based on current usage</p>
                      </div>
                      <TrendingUp className="w-12 h-12 text-blue-600" />
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-6 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-lg font-semibold text-purple-900">Cost per User</h4>
                        <p className="text-3xl font-bold text-purple-600">
                          ${(analytics.costs.totalCost / analytics.organization.totalUsers).toFixed(2)}
                        </p>
                        <p className="text-sm text-purple-700">Average monthly cost</p>
                      </div>
                      <Users className="w-12 h-12 text-purple-600" />
                    </div>
                  </div>
                </div>

                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">Cost Breakdown by Category</h4>
                  <div className="space-y-4">
                    {analytics.costs.costByCategory.map((category, index) => (
                      <div key={index}>
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm font-medium text-gray-700">{category.category}</span>
                          <span className="text-sm text-gray-600">
                            ${category.amount.toLocaleString()} ({category.percentage}%)
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{ width: `${category.percentage}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 