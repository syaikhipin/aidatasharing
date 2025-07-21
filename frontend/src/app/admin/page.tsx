'use client';

import { useState, useEffect } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import Link from 'next/link';
import {
  Users,
  Database,
  Settings,
  Shield,
  Activity,
  FileText,
  BarChart3,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  Server,
  HardDrive,
  Cpu,
  Network,
  Eye,
  UserCheck,
  UserX,
  Download,
  Upload
} from 'lucide-react';

interface AdminStats {
  totalUsers: number;
  activeUsers: number;
  totalDatasets: number;
  pendingRequests: number;
  systemHealth: {
    uptime: string;
    cpuUsage: number;
    memoryUsage: number;
    diskUsage: number;
    networkStatus: 'healthy' | 'warning' | 'critical';
  };
  recentActivity: {
    id: string;
    type: 'user_registration' | 'dataset_upload' | 'access_request' | 'system_alert';
    description: string;
    timestamp: string;
    severity: 'info' | 'warning' | 'error';
  }[];
}

function AdminPanelContent() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState('overview');

  useEffect(() => {
    fetchAdminStats();
  }, []);

  const fetchAdminStats = async () => {
    try {
      setLoading(true);
      
      const response = await fetch('/api/admin/stats', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching admin stats:', error);
      
      // Fallback to mock data if API fails
      const mockStats: AdminStats = {
        totalUsers: 0,
        activeUsers: 0,
        totalDatasets: 0,
        pendingRequests: 0,
        systemHealth: {
          uptime: 'N/A',
          cpuUsage: 0,
          memoryUsage: 0,
          diskUsage: 0,
          networkStatus: 'critical'
        },
        recentActivity: []
      };
      
      setStats(mockStats);
    } finally {
      setLoading(false);
    }
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'user_registration': return <UserCheck className="h-4 w-4" />;
      case 'dataset_upload': return <Upload className="h-4 w-4" />;
      case 'access_request': return <FileText className="h-4 w-4" />;
      case 'system_alert': return <AlertTriangle className="h-4 w-4" />;
      default: return <Activity className="h-4 w-4" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error': return 'text-red-600';
      case 'warning': return 'text-yellow-600';
      case 'info': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Admin Panel</h1>
          <p className="mt-2 text-gray-600">Manage users, datasets, and system settings</p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Users className="h-8 w-8 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Users</p>
                <p className="text-2xl font-semibold text-gray-900">{stats?.totalUsers.toLocaleString()}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Activity className="h-8 w-8 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Active Users</p>
                <p className="text-2xl font-semibold text-gray-900">{stats?.activeUsers.toLocaleString()}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Database className="h-8 w-8 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Datasets</p>
                <p className="text-2xl font-semibold text-gray-900">{stats?.totalDatasets.toLocaleString()}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Clock className="h-8 w-8 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Pending Requests</p>
                <p className="text-2xl font-semibold text-gray-900">{stats?.pendingRequests}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Quick Actions */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Quick Actions</h3>
              </div>
              <div className="p-6 space-y-4">
                <Link
                  href="/admin/users"
                  className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
                >
                  <Users className="h-5 w-5 text-gray-400 mr-3" />
                  <span className="text-sm font-medium text-gray-900">Manage Users</span>
                </Link>
                
                <Link
                  href="/data-access"
                  className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
                >
                  <FileText className="h-5 w-5 text-gray-400 mr-3" />
                  <span className="text-sm font-medium text-gray-900">Access Requests</span>
                </Link>
                
                <Link
                  href="/datasets"
                  className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
                >
                  <Database className="h-5 w-5 text-gray-400 mr-3" />
                  <span className="text-sm font-medium text-gray-900">Manage Datasets</span>
                </Link>
                
                <Link
                  href="/analytics"
                  className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
                >
                  <BarChart3 className="h-5 w-5 text-gray-400 mr-3" />
                  <span className="text-sm font-medium text-gray-900">View Analytics</span>
                </Link>
              </div>
            </div>
          </div>

          {/* System Health & Recent Activity */}
          <div className="lg:col-span-2 space-y-8">
            {/* System Health */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">System Health</h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <Server className="h-8 w-8 text-green-600 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">Uptime</p>
                    <p className="text-lg font-semibold text-gray-900">{stats?.systemHealth.uptime}</p>
                  </div>
                  
                  <div className="text-center">
                    <Cpu className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">CPU Usage</p>
                    <p className="text-lg font-semibold text-gray-900">{stats?.systemHealth.cpuUsage}%</p>
                  </div>
                  
                  <div className="text-center">
                    <HardDrive className="h-8 w-8 text-purple-600 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">Memory</p>
                    <p className="text-lg font-semibold text-gray-900">{stats?.systemHealth.memoryUsage}%</p>
                  </div>
                  
                  <div className="text-center">
                    <Network className="h-8 w-8 text-orange-600 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">Disk Usage</p>
                    <p className="text-lg font-semibold text-gray-900">{stats?.systemHealth.diskUsage}%</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  {stats?.recentActivity.map((activity) => (
                    <div key={activity.id} className="flex items-start space-x-3">
                      <div className={`flex-shrink-0 ${getSeverityColor(activity.severity)}`}>
                        {getActivityIcon(activity.type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-900">{activity.description}</p>
                        <p className="text-xs text-gray-500">
                          {new Date(activity.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AdminPanel() {
  return (
    <ProtectedRoute requireAdmin>
      <AdminPanelContent />
    </ProtectedRoute>
  );
}