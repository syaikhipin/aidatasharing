'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useAuth } from '@/components/auth/AuthProvider';
import { useState, useEffect } from 'react';
import { dataAccessAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface AccessRequest {
  id: number;
  dataset_id: number;
  dataset_name: string;
  requester_name: string;
  requester_email: string;
  request_type: string;
  requested_level: string;
  purpose: string;
  justification: string;
  urgency: string;
  category: string;
  status: string;
  created_at: string;
  expiry_date?: string;
}

export default function AdminAccessRequestsPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <AdminAccessRequestsContent />
      </DashboardLayout>
    </ProtectedRoute>
  );
}

function AdminAccessRequestsContent() {
  const { user } = useAuth();
  const [accessRequests, setAccessRequests] = useState<AccessRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('pending');
  const [selectedRequest, setSelectedRequest] = useState<AccessRequest | null>(null);
  const [approvalModal, setApprovalModal] = useState<{
    isOpen: boolean;
    requestId: number;
    action: 'approve' | 'reject';
  }>({
    isOpen: false,
    requestId: 0,
    action: 'approve'
  });

  useEffect(() => {
    fetchAccessRequests();
  }, []);

  const fetchAccessRequests = async () => {
    try {
      setLoading(true);
      const requests = await dataAccessAPI.getAccessRequests({ 
        my_requests: false // Get all requests for admin
      });
      setAccessRequests(requests || []);
    } catch (error) {
      console.error('Error fetching access requests:', error);
      setAccessRequests([]);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveRequest = async (requestId: number, reason?: string) => {
    try {
      await dataAccessAPI.approveAccessRequest(requestId, {
        approved: true,
        reason: reason || 'Request approved by administrator'
      });
      
      // Refresh the requests
      fetchAccessRequests();
      
      alert('Access request approved successfully!');
    } catch (error) {
      console.error('Error approving request:', error);
      alert('Failed to approve request. Please try again.');
    }
  };

  const handleRejectRequest = async (requestId: number, reason: string) => {
    try {
      await dataAccessAPI.approveAccessRequest(requestId, {
        approved: false,
        reason: reason
      });
      
      // Refresh the requests
      fetchAccessRequests();
      
      alert('Access request rejected.');
    } catch (error) {
      console.error('Error rejecting request:', error);
      alert('Failed to reject request. Please try again.');
    }
  };

  const openApprovalModal = (requestId: number, action: 'approve' | 'reject') => {
    setApprovalModal({
      isOpen: true,
      requestId,
      action
    });
  };

  const handleApprovalSubmit = (reason: string) => {
    if (approvalModal.action === 'approve') {
      handleApproveRequest(approvalModal.requestId, reason);
    } else {
      handleRejectRequest(approvalModal.requestId, reason);
    }
    setApprovalModal(prev => ({ ...prev, isOpen: false }));
  };

  const filteredRequests = accessRequests.filter(request => {
    if (filter === 'all') return true;
    return request.status === filter;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center space-y-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"></div>
          <p className="text-gray-600">Loading access requests...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Access Request Management</h1>
          <p className="text-gray-600 mt-2">
            Review and manage data access requests from organization members
          </p>
        </div>

        {/* Filter Tabs */}
        <div className="mb-6">
          <div className="flex space-x-1 bg-gray-100 rounded-lg p-1 w-fit">
            {[
              { key: 'pending', label: 'Pending', count: accessRequests.filter(r => r.status === 'pending').length },
              { key: 'all', label: 'All', count: accessRequests.length },
              { key: 'approved', label: 'Approved', count: accessRequests.filter(r => r.status === 'approved').length },
              { key: 'rejected', label: 'Rejected', count: accessRequests.filter(r => r.status === 'rejected').length }
            ].map(({ key, label, count }) => (
              <button
                key={key}
                onClick={() => setFilter(key as any)}
                className={`px-4 py-2 text-sm rounded-md transition-colors ${
                  filter === key
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {label} ({count})
              </button>
            ))}
          </div>
        </div>

        {/* Requests List */}
        {filteredRequests.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <div className="w-24 h-24 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                <span className="text-4xl">📋</span>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No access requests</h3>
              <p className="text-gray-600">
                {filter === 'pending' 
                  ? "No pending access requests at the moment."
                  : `No ${filter} access requests found.`
                }
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredRequests.map((request) => (
              <Card key={request.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-3">
                        <h3 className="text-lg font-semibold text-gray-900">
                          {request.dataset_name}
                        </h3>
                        <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(request.status)}`}>
                          {request.status}
                        </span>
                        <span className={`px-2 py-1 text-xs rounded-full ${getUrgencyColor(request.urgency)}`}>
                          {request.urgency} priority
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div>
                          <p className="text-sm text-gray-600">
                            <strong>Requester:</strong> {request.requester_name} ({request.requester_email})
                          </p>
                          <p className="text-sm text-gray-600">
                            <strong>Access Level:</strong> {request.requested_level}
                          </p>
                          <p className="text-sm text-gray-600">
                            <strong>Category:</strong> {request.category}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">
                            <strong>Request Type:</strong> {request.request_type}
                          </p>
                          <p className="text-sm text-gray-600">
                            <strong>Requested:</strong> {new Date(request.created_at).toLocaleDateString()}
                          </p>
                          {request.expiry_date && (
                            <p className="text-sm text-gray-600">
                              <strong>Expires:</strong> {new Date(request.expiry_date).toLocaleDateString()}
                            </p>
                          )}
                        </div>
                      </div>
                      
                      <div className="mb-4">
                        <p className="text-sm text-gray-600 mb-2">
                          <strong>Purpose:</strong>
                        </p>
                        <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
                          {request.purpose}
                        </p>
                      </div>
                      
                      <div className="mb-4">
                        <p className="text-sm text-gray-600 mb-2">
                          <strong>Justification:</strong>
                        </p>
                        <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
                          {request.justification}
                        </p>
                      </div>
                    </div>
                    
                    {request.status === 'pending' && (
                      <div className="flex flex-col space-y-2 ml-6">
                        <Button
                          onClick={() => openApprovalModal(request.id, 'approve')}
                          className="bg-green-600 hover:bg-green-700"
                          size="sm"
                        >
                          Approve
                        </Button>
                        <Button
                          onClick={() => openApprovalModal(request.id, 'reject')}
                          variant="outline"
                          className="border-red-300 text-red-600 hover:bg-red-50"
                          size="sm"
                        >
                          Reject
                        </Button>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Approval Modal */}
      {approvalModal.isOpen && (
        <ApprovalModal
          isOpen={approvalModal.isOpen}
          action={approvalModal.action}
          onClose={() => setApprovalModal(prev => ({ ...prev, isOpen: false }))}
          onSubmit={handleApprovalSubmit}
        />
      )}
    </div>
  );
}

interface ApprovalModalProps {
  isOpen: boolean;
  action: 'approve' | 'reject';
  onClose: () => void;
  onSubmit: (reason: string) => void;
}

function ApprovalModal({ isOpen, action, onClose, onSubmit }: ApprovalModalProps) {
  const [reason, setReason] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (action === 'reject' && !reason.trim()) {
      alert('Please provide a reason for rejection.');
      return;
    }
    onSubmit(reason);
    setReason('');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-md w-full">
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">
            {action === 'approve' ? 'Approve Access Request' : 'Reject Access Request'}
          </h3>
          
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label htmlFor="reason" className="block text-sm font-medium text-gray-700 mb-2">
                {action === 'approve' ? 'Approval Note (Optional)' : 'Rejection Reason (Required)'}
              </label>
              <textarea
                id="reason"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder={
                  action === 'approve' 
                    ? 'Optional note about the approval...'
                    : 'Please provide a reason for rejecting this request...'
                }
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required={action === 'reject'}
              />
            </div>
            
            <div className="flex space-x-3">
              <Button
                type="submit"
                className={action === 'approve' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}
              >
                {action === 'approve' ? 'Approve Request' : 'Reject Request'}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
              >
                Cancel
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}