'use client';

import { useState, useEffect } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { 
  Search, 
  Filter, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Eye, 
  Lock, 
  Users, 
  Calendar,
  MessageSquare,
  Send,
  Download,
  Shield,
  FileText,
  MoreHorizontal,
  User,
  Database,
  Share2,
  Bell,
  History
} from 'lucide-react';

interface AccessRequest {
  id: string;
  requesterId: string;
  requesterName: string;
  requesterEmail: string;
  requesterDepartment: string;
  datasetId: string;
  datasetName: string;
  datasetOwner: string;
  requestType: 'access' | 'download' | 'share';
  requestedLevel: 'read' | 'write' | 'admin';
  purpose: string;
  justification: string;
  requestDate: string;
  expiryDate?: string;
  status: 'pending' | 'approved' | 'rejected' | 'expired';
  approvedBy?: string;
  approvedDate?: string;
  rejectionReason?: string;
  urgency: 'low' | 'medium' | 'high';
  category: 'research' | 'analysis' | 'compliance' | 'reporting' | 'development';
}

interface Dataset {
  id: string;
  name: string;
  description: string;
  owner: string;
  ownerDepartment: string;
  sharingLevel: 'PRIVATE' | 'ORGANIZATION' | 'PUBLIC';
  size: number;
  lastUpdated: string;
  accessCount: number;
  hasAccess: boolean;
  canRequest: boolean;
  tags: string[];
}

interface AuditLog {
  id: string;
  action: string;
  userId: string;
  userName: string;
  datasetId: string;
  datasetName: string;
  timestamp: string;
  details: string;
  ipAddress: string;
  userAgent: string;
}

function DataAccessPageContent() {
  const [activeTab, setActiveTab] = useState<'browse' | 'requests' | 'audit'>('browse');
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [accessRequests, setAccessRequests] = useState<AccessRequest[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFilters, setSelectedFilters] = useState<{
    sharingLevel: string;
    department: string;
    status: string;
    urgency: string;
  }>({
    sharingLevel: 'all',
    department: 'all',
    status: 'all',
    urgency: 'all'
  });

  // Request modal state
  const [showRequestModal, setShowRequestModal] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [requestForm, setRequestForm] = useState({
    requestType: 'access' as const,
    requestedLevel: 'read' as const,
    purpose: '',
    justification: '',
    urgency: 'medium' as const,
    category: 'analysis' as const,
    expiryDate: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch real data from backend APIs
      const token = localStorage.getItem('token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };
      
      // Fetch datasets
      try {
        const datasetsResponse = await fetch('/api/data-access/datasets', { headers });
        if (datasetsResponse.ok) {
          const datasetsData = await datasetsResponse.json();
          setDatasets(datasetsData);
        } else {
          console.error('Failed to fetch datasets:', datasetsResponse.status);
          setDatasets([]);
        }
      } catch (error) {
        console.error('Error fetching datasets:', error);
        setDatasets([]);
      }
      
      // Fetch access requests
      try {
        const requestsResponse = await fetch('/api/data-access/requests', { headers });
        if (requestsResponse.ok) {
          const requestsData = await requestsResponse.json();
          setAccessRequests(requestsData);
        } else {
          console.error('Failed to fetch access requests:', requestsResponse.status);
          setAccessRequests([]);
        }
      } catch (error) {
        console.error('Error fetching access requests:', error);
        setAccessRequests([]);
      }
      
      // Fetch audit logs
      try {
        const auditResponse = await fetch('/api/data-access/audit-logs', { headers });
        if (auditResponse.ok) {
          const auditData = await auditResponse.json();
          setAuditLogs(auditData);
        } else {
          console.error('Failed to fetch audit logs:', auditResponse.status);
          setAuditLogs([]);
        }
      } catch (error) {
        console.error('Error fetching audit logs:', error);
        setAuditLogs([]);
      }
      
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRequestAccess = (dataset: Dataset) => {
    setSelectedDataset(dataset);
    setRequestForm({
      requestType: 'access',
      requestedLevel: 'read',
      purpose: '',
      justification: '',
      urgency: 'medium',
      category: 'analysis',
      expiryDate: ''
    });
    setShowRequestModal(true);
  };

  const submitAccessRequest = async () => {
    if (!selectedDataset) return;

    try {
      const token = localStorage.getItem('token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };
      
      const requestData = {
        dataset_id: selectedDataset.id,
        request_type: requestForm.requestType,
        requested_level: requestForm.requestedLevel,
        purpose: requestForm.purpose,
        justification: requestForm.justification,
        urgency: requestForm.urgency,
        category: requestForm.category,
        expiry_date: requestForm.expiryDate || null
      };
      
      const response = await fetch('/api/data-access/requests', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(requestData)
      });
      
      if (response.ok) {
        const result = await response.json();
        setShowRequestModal(false);
        alert('Access request submitted successfully!');
        // Refresh data to show new request
        fetchData();
      } else {
        const errorData = await response.json();
        console.error('Failed to submit access request:', errorData);
        alert(`Failed to submit access request: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error submitting request:', error);
      alert('Error submitting request. Please try again.');
    }
  };

  const handleApproveRequest = async (requestId: string) => {
    try {
      const token = localStorage.getItem('token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };
      
      const response = await fetch(`/api/data-access/requests/${requestId}/approve`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({ approved: true })
      });
      
      if (response.ok) {
        alert('Request approved successfully!');
        // Refresh data to show updated status
        fetchData();
      } else {
        const errorData = await response.json();
        console.error('Failed to approve request:', errorData);
        alert(`Failed to approve request: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error approving request:', error);
      alert('Error approving request. Please try again.');
    }
  };

  const handleRejectRequest = async (requestId: string, reason: string) => {
    try {
      const token = localStorage.getItem('token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };
      
      const response = await fetch(`/api/data-access/requests/${requestId}/approve`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({ approved: false, rejection_reason: reason })
      });
      
      if (response.ok) {
        alert('Request rejected successfully!');
        // Refresh data to show updated status
        fetchData();
      } else {
        const errorData = await response.json();
        console.error('Failed to reject request:', errorData);
        alert(`Failed to reject request: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error rejecting request:', error);
      alert('Error rejecting request. Please try again.');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return <Clock className="w-4 h-4 text-yellow-600" />;
      case 'approved': return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'rejected': return <XCircle className="w-4 h-4 text-red-600" />;
      case 'expired': return <AlertCircle className="w-4 h-4 text-gray-600" />;
      default: return <Clock className="w-4 h-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'approved': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      case 'expired': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getSharingLevelIcon = (level: string) => {
    switch (level) {
      case 'PRIVATE': return <Lock className="w-4 h-4 text-red-600" />;
      case 'ORGANIZATION': return <Users className="w-4 h-4 text-blue-600" />;
      case 'PUBLIC': return <Share2 className="w-4 h-4 text-green-600" />;
      default: return <Lock className="w-4 h-4 text-gray-600" />;
    }
  };

  const filteredDatasets = datasets.filter(dataset => {
    const matchesSearch = dataset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         dataset.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         dataset.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesLevel = selectedFilters.sharingLevel === 'all' || dataset.sharingLevel === selectedFilters.sharingLevel;
    const matchesDepartment = selectedFilters.department === 'all' || dataset.ownerDepartment === selectedFilters.department;
    
    return matchesSearch && matchesLevel && matchesDepartment;
  });

  const filteredRequests = accessRequests.filter(request => {
    const matchesStatus = selectedFilters.status === 'all' || request.status === selectedFilters.status;
    const matchesUrgency = selectedFilters.urgency === 'all' || request.urgency === selectedFilters.urgency;
    
    return matchesStatus && matchesUrgency;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-white p-6 rounded-lg shadow h-48"></div>
              ))}
            </div>
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
            <h1 className="text-3xl font-bold text-gray-900">Data Access Management</h1>
            <p className="text-gray-600 mt-2">Request access to datasets, manage approvals, and track data usage</p>
          </div>
          
          <div className="flex items-center space-x-4">
            <button className="flex items-center px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
              <Bell className="w-4 h-4 mr-2" />
              Notifications
            </button>
            <button className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              <Download className="w-4 h-4 mr-2" />
              Export Report
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {[
                { id: 'browse', label: 'Browse Datasets', icon: Database },
                { id: 'requests', label: 'Access Requests', icon: MessageSquare },
                { id: 'audit', label: 'Audit Trail', icon: History }
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
            {activeTab === 'browse' && (
              <div className="space-y-6">
                {/* Search and Filters */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="relative">
                      <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                      <input
                        type="text"
                        placeholder="Search datasets..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 w-80"
                      />
                    </div>
                    
                    <select
                      value={selectedFilters.sharingLevel}
                      onChange={(e) => setSelectedFilters(prev => ({ ...prev, sharingLevel: e.target.value }))}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="all">All Sharing Levels</option>
                      <option value="PRIVATE">Private</option>
                      <option value="ORGANIZATION">Organization</option>
                      <option value="PUBLIC">Public</option>
                    </select>
                    
                    <select
                      value={selectedFilters.department}
                      onChange={(e) => setSelectedFilters(prev => ({ ...prev, department: e.target.value }))}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="all">All Departments</option>
                      <option value="Analytics">Analytics</option>
                      <option value="Finance">Finance</option>
                      <option value="Marketing">Marketing</option>
                      <option value="Product">Product</option>
                    </select>
                  </div>
                  
                  <div className="flex items-center text-sm text-gray-600">
                    Showing {filteredDatasets.length} of {datasets.length} datasets
                  </div>
                </div>

                {/* Datasets Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                  {filteredDatasets.map((dataset) => (
                    <div key={dataset.id} className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center">
                          {getSharingLevelIcon(dataset.sharingLevel)}
                          <span className={`ml-2 px-2 py-1 text-xs rounded-full ${
                            dataset.sharingLevel === 'PRIVATE' ? 'bg-red-100 text-red-800' :
                            dataset.sharingLevel === 'ORGANIZATION' ? 'bg-blue-100 text-blue-800' :
                            dataset.sharingLevel === 'PUBLIC' ? 'bg-green-100 text-green-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {dataset.sharingLevel}
                          </span>
                        </div>
                        <button className="p-1 text-gray-400 hover:text-gray-600">
                          <MoreHorizontal className="w-4 h-4" />
                        </button>
                      </div>
                      
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">{dataset.name}</h3>
                      <p className="text-sm text-gray-600 mb-4 line-clamp-3">{dataset.description}</p>
                      
                      <div className="space-y-2 mb-4">
                        <div className="flex items-center text-sm text-gray-600">
                          <User className="w-4 h-4 mr-2" />
                          <span>{dataset.owner} • {dataset.ownerDepartment}</span>
                        </div>
                        <div className="flex items-center text-sm text-gray-600">
                          <Database className="w-4 h-4 mr-2" />
                          <span>{dataset.size} GB • {dataset.accessCount} accesses</span>
                        </div>
                        <div className="flex items-center text-sm text-gray-600">
                          <Calendar className="w-4 h-4 mr-2" />
                          <span>Updated {new Date(dataset.lastUpdated).toLocaleDateString()}</span>
                        </div>
                      </div>
                      
                      {/* Tags */}
                      <div className="flex flex-wrap gap-2 mb-4">
                        {dataset.tags.slice(0, 3).map((tag) => (
                          <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                            {tag}
                          </span>
                        ))}
                        {dataset.tags.length > 3 && (
                          <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                            +{dataset.tags.length - 3} more
                          </span>
                        )}
                      </div>
                      
                      {/* Actions */}
                      <div className="flex items-center space-x-2">
                        {dataset.hasAccess ? (
                          <button className="flex items-center px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm">
                            <Eye className="w-4 h-4 mr-2" />
                            View Dataset
                          </button>
                        ) : dataset.canRequest ? (
                          <button
                            onClick={() => handleRequestAccess(dataset)}
                            className="flex items-center px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                          >
                            <Send className="w-4 h-4 mr-2" />
                            Request Access
                          </button>
                        ) : (
                          <button disabled className="flex items-center px-3 py-2 bg-gray-300 text-gray-500 rounded-lg text-sm cursor-not-allowed">
                            <Shield className="w-4 h-4 mr-2" />
                            No Access
                          </button>
                        )}
                        <button className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                          <FileText className="w-4 h-4 text-gray-600" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'requests' && (
              <div className="space-y-6">
                {/* Request Filters */}
                <div className="flex items-center space-x-4">
                  <select
                    value={selectedFilters.status}
                    onChange={(e) => setSelectedFilters(prev => ({ ...prev, status: e.target.value }))}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All Statuses</option>
                    <option value="pending">Pending</option>
                    <option value="approved">Approved</option>
                    <option value="rejected">Rejected</option>
                    <option value="expired">Expired</option>
                  </select>
                  
                  <select
                    value={selectedFilters.urgency}
                    onChange={(e) => setSelectedFilters(prev => ({ ...prev, urgency: e.target.value }))}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All Urgency Levels</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>

                {/* Access Requests List */}
                <div className="space-y-4">
                  {filteredRequests.map((request) => (
                    <div key={request.id} className="bg-white border border-gray-200 rounded-lg p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <h3 className="text-lg font-semibold text-gray-900">{request.datasetName}</h3>
                            <div className={`flex items-center px-2 py-1 rounded-full text-sm font-medium ${getStatusColor(request.status)}`}>
                              {getStatusIcon(request.status)}
                              <span className="ml-1 capitalize">{request.status}</span>
                            </div>
                            <span className={`px-2 py-1 text-xs rounded-full ${getUrgencyColor(request.urgency)}`}>
                              {request.urgency.toUpperCase()}
                            </span>
                          </div>
                          
                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
                            <div className="space-y-2">
                              <div className="flex items-center text-sm text-gray-600">
                                <User className="w-4 h-4 mr-2" />
                                <span>{request.requesterName} • {request.requesterDepartment}</span>
                              </div>
                              <div className="flex items-center text-sm text-gray-600">
                                <Calendar className="w-4 h-4 mr-2" />
                                <span>Requested {new Date(request.requestDate).toLocaleDateString()}</span>
                              </div>
                              <div className="flex items-center text-sm text-gray-600">
                                <Shield className="w-4 h-4 mr-2" />
                                <span>{request.requestType} • {request.requestedLevel} access</span>
                              </div>
                            </div>
                            
                            <div className="space-y-2">
                              <div>
                                <p className="text-sm font-medium text-gray-700">Purpose:</p>
                                <p className="text-sm text-gray-600">{request.purpose}</p>
                              </div>
                              {request.status === 'approved' && request.approvedBy && (
                                <div className="text-sm text-green-600">
                                  Approved by {request.approvedBy} on {new Date(request.approvedDate!).toLocaleDateString()}
                                </div>
                              )}
                              {request.status === 'rejected' && request.rejectionReason && (
                                <div className="text-sm text-red-600">
                                  Rejected: {request.rejectionReason}
                                </div>
                              )}
                            </div>
                          </div>
                          
                          <div className="bg-gray-50 p-3 rounded-lg">
                            <p className="text-sm font-medium text-gray-700 mb-1">Justification:</p>
                            <p className="text-sm text-gray-600">{request.justification}</p>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-2 ml-6">
                          {request.status === 'pending' && (
                            <>
                              <button 
                                onClick={() => handleApproveRequest(request.id)}
                                className="px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
                              >
                                Approve
                              </button>
                              <button 
                                onClick={() => {
                                  const reason = prompt('Please provide a reason for rejection:');
                                  if (reason) handleRejectRequest(request.id, reason);
                                }}
                                className="px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm"
                              >
                                Reject
                              </button>
                            </>
                          )}
                          <button className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                            <MoreHorizontal className="w-4 h-4 text-gray-600" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'audit' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Audit Trail</h3>
                  <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                    Export Audit Log
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
                          Action
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          User
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Dataset
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Details
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          IP Address
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {auditLogs.map((log) => (
                        <tr key={log.id}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {new Date(log.timestamp).toLocaleString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              log.action.includes('GRANTED') || log.action.includes('ACCESSED') 
                                ? 'bg-green-100 text-green-800'
                                : log.action.includes('DENIED') || log.action.includes('REJECTED')
                                ? 'bg-red-100 text-red-800'
                                : 'bg-blue-100 text-blue-800'
                            }`}>
                              {log.action.replace('_', ' ')}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {log.userName}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                            {log.datasetName}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-600 max-w-md">
                            {log.details}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {log.ipAddress}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Access Request Modal */}
        {showRequestModal && selectedDataset && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Request Access to {selectedDataset.name}
                </h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Request Type
                    </label>
                    <select
                      value={requestForm.requestType}
                      onChange={(e) => setRequestForm(prev => ({ ...prev, requestType: e.target.value as any }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="access">View Access</option>
                      <option value="download">Download Access</option>
                      <option value="share">Share Access</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Access Level
                    </label>
                    <select
                      value={requestForm.requestedLevel}
                      onChange={(e) => setRequestForm(prev => ({ ...prev, requestedLevel: e.target.value as any }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="read">Read Only</option>
                      <option value="write">Read & Write</option>
                      <option value="admin">Full Admin</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Purpose
                    </label>
                    <input
                      type="text"
                      value={requestForm.purpose}
                      onChange={(e) => setRequestForm(prev => ({ ...prev, purpose: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Brief description of purpose"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Justification
                    </label>
                    <textarea
                      value={requestForm.justification}
                      onChange={(e) => setRequestForm(prev => ({ ...prev, justification: e.target.value }))}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Detailed justification for access request"
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Urgency
                      </label>
                      <select
                        value={requestForm.urgency}
                        onChange={(e) => setRequestForm(prev => ({ ...prev, urgency: e.target.value as any }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Category
                      </label>
                      <select
                        value={requestForm.category}
                        onChange={(e) => setRequestForm(prev => ({ ...prev, category: e.target.value as any }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="research">Research</option>
                        <option value="analysis">Analysis</option>
                        <option value="compliance">Compliance</option>
                        <option value="reporting">Reporting</option>
                        <option value="development">Development</option>
                      </select>
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Expiry Date (Optional)
                    </label>
                    <input
                      type="date"
                      value={requestForm.expiryDate}
                      onChange={(e) => setRequestForm(prev => ({ ...prev, expiryDate: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
                
                <div className="flex items-center justify-end space-x-3 mt-6">
                  <button
                    onClick={() => setShowRequestModal(false)}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={submitAccessRequest}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Submit Request
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function DataAccessPage() {
  return (
    <ProtectedRoute>
      <DataAccessPageContent />
    </ProtectedRoute>
  );
}