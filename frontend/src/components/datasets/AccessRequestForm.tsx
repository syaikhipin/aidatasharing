'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { dataAccessAPI } from '@/lib/api';

interface AccessRequestFormProps {
  datasetId: number;
  datasetName: string;
  onSuccess: () => void;
  onCancel: () => void;
}

interface AccessRequestFormData {
  purpose: string;
  justification: string;
  urgency: 'low' | 'medium' | 'high';
  category: 'research' | 'analysis' | 'compliance' | 'reporting' | 'development';
  requested_level: 'read' | 'write' | 'admin';
  expiry_date?: string;
}

export function AccessRequestForm({ datasetId, datasetName, onSuccess, onCancel }: AccessRequestFormProps) {
  const [formData, setFormData] = useState<AccessRequestFormData>({
    purpose: '',
    justification: '',
    urgency: 'medium',
    category: 'analysis',
    requested_level: 'read',
    expiry_date: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.purpose.trim()) {
      newErrors.purpose = 'Purpose is required';
    } else if (formData.purpose.trim().length < 10) {
      newErrors.purpose = 'Purpose must be at least 10 characters';
    }

    if (!formData.justification.trim()) {
      newErrors.justification = 'Justification is required';
    } else if (formData.justification.trim().length < 20) {
      newErrors.justification = 'Justification must be at least 20 characters';
    }

    if (formData.expiry_date) {
      const expiryDate = new Date(formData.expiry_date);
      const today = new Date();
      if (expiryDate <= today) {
        newErrors.expiry_date = 'Expiry date must be in the future';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    try {
      await dataAccessAPI.createAccessRequest({
        dataset_id: datasetId,
        request_type: 'access',
        ...formData,
        expiry_date: formData.expiry_date || undefined
      });

      onSuccess();
    } catch (error) {
      console.error('Error submitting access request:', error);
      setErrors({ submit: 'Failed to submit access request. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (field: keyof AccessRequestFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Request Access to Dataset</CardTitle>
        <CardDescription>
          Submit a request to access "{datasetName}". Please provide detailed information about your intended use.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Purpose */}
          <div>
            <label htmlFor="purpose" className="block text-sm font-medium text-gray-700 mb-2">
              Purpose <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="purpose"
              value={formData.purpose}
              onChange={(e) => handleInputChange('purpose', e.target.value)}
              placeholder="Brief description of what you plan to do with this dataset"
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.purpose ? 'border-red-500' : 'border-gray-300'
              }`}
              disabled={isSubmitting}
            />
            {errors.purpose && <p className="text-red-500 text-sm mt-1">{errors.purpose}</p>}
          </div>

          {/* Justification */}
          <div>
            <label htmlFor="justification" className="block text-sm font-medium text-gray-700 mb-2">
              Justification <span className="text-red-500">*</span>
            </label>
            <textarea
              id="justification"
              value={formData.justification}
              onChange={(e) => handleInputChange('justification', e.target.value)}
              placeholder="Detailed explanation of why you need access to this dataset, including how it will be used and any relevant background information"
              rows={4}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.justification ? 'border-red-500' : 'border-gray-300'
              }`}
              disabled={isSubmitting}
            />
            {errors.justification && <p className="text-red-500 text-sm mt-1">{errors.justification}</p>}
          </div>

          {/* Access Level */}
          <div>
            <label htmlFor="requested_level" className="block text-sm font-medium text-gray-700 mb-2">
              Requested Access Level
            </label>
            <select
              id="requested_level"
              value={formData.requested_level}
              onChange={(e) => handleInputChange('requested_level', e.target.value as 'read' | 'write' | 'admin')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isSubmitting}
            >
              <option value="read">Read Only - View and download data</option>
              <option value="write">Read/Write - View, download, and modify data</option>
              <option value="admin">Admin - Full access including sharing permissions</option>
            </select>
          </div>

          {/* Category */}
          <div>
            <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-2">
              Request Category
            </label>
            <select
              id="category"
              value={formData.category}
              onChange={(e) => handleInputChange('category', e.target.value as any)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isSubmitting}
            >
              <option value="research">Research - Academic or scientific research</option>
              <option value="analysis">Analysis - Data analysis and insights</option>
              <option value="compliance">Compliance - Regulatory or compliance requirements</option>
              <option value="reporting">Reporting - Business reporting and dashboards</option>
              <option value="development">Development - Software or model development</option>
            </select>
          </div>

          {/* Urgency */}
          <div>
            <label htmlFor="urgency" className="block text-sm font-medium text-gray-700 mb-2">
              Urgency Level
            </label>
            <select
              id="urgency"
              value={formData.urgency}
              onChange={(e) => handleInputChange('urgency', e.target.value as 'low' | 'medium' | 'high')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isSubmitting}
            >
              <option value="low">Low - No specific deadline</option>
              <option value="medium">Medium - Needed within a few weeks</option>
              <option value="high">High - Urgent, needed ASAP</option>
            </select>
          </div>

          {/* Expiry Date (Optional) */}
          <div>
            <label htmlFor="expiry_date" className="block text-sm font-medium text-gray-700 mb-2">
              Access Expiry Date (Optional)
            </label>
            <input
              type="date"
              id="expiry_date"
              value={formData.expiry_date}
              onChange={(e) => handleInputChange('expiry_date', e.target.value)}
              min={new Date().toISOString().split('T')[0]}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.expiry_date ? 'border-red-500' : 'border-gray-300'
              }`}
              disabled={isSubmitting}
            />
            {errors.expiry_date && <p className="text-red-500 text-sm mt-1">{errors.expiry_date}</p>}
            <p className="text-sm text-gray-500 mt-1">
              Leave empty for permanent access (subject to approval)
            </p>
          </div>

          {/* Submit Error */}
          {errors.submit && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <p className="text-red-700 text-sm">{errors.submit}</p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex space-x-3 pt-4">
            <Button
              type="submit"
              disabled={isSubmitting}
              className="flex-1"
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Submitting...
                </>
              ) : (
                'Submit Request'
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={isSubmitting}
              className="flex-1"
            >
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

interface AccessRequestModalProps {
  isOpen: boolean;
  datasetId: number;
  datasetName: string;
  onClose: () => void;
  onSuccess: () => void;
}

export function AccessRequestModal({ isOpen, datasetId, datasetName, onClose, onSuccess }: AccessRequestModalProps) {
  if (!isOpen) return null;

  const handleSuccess = () => {
    onSuccess();
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <AccessRequestForm
          datasetId={datasetId}
          datasetName={datasetName}
          onSuccess={handleSuccess}
          onCancel={onClose}
        />
      </div>
    </div>
  );
}