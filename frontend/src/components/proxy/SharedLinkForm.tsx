'use client';

import React, { useState } from 'react';
import { Share2, Clock, Users, Lock, Globe, Calendar, Hash } from 'lucide-react';

interface SharedLinkFormProps {
  proxyConnectorId: number;
  proxyConnectorName: string;
  onSubmit: (data: SharedLinkData) => Promise<void>;
  onCancel: () => void;
  isSubmitting: boolean;
}

interface SharedLinkData {
  proxy_connector_id: number;
  name: string;
  description: string;
  is_public: boolean;
  requires_authentication: boolean;
  allowed_users: string[];
  max_uses: number | null;
}

export default function SharedLinkForm({ 
  proxyConnectorId, 
  proxyConnectorName, 
  onSubmit, 
  onCancel, 
  isSubmitting 
}: SharedLinkFormProps) {
  const [form, setForm] = useState<SharedLinkData>({
    proxy_connector_id: proxyConnectorId,
    name: '',
    description: '',
    is_public: false,
    requires_authentication: true,
    allowed_users: [],
    max_uses: null
  });

  const [userEmail, setUserEmail] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!form.name.trim()) {
      newErrors.name = 'Link name is required';
    }

    if (!form.description.trim()) {
      newErrors.description = 'Description is required';
    }

    if (!form.is_public && form.allowed_users.length === 0) {
      newErrors.allowed_users = 'Add at least one allowed user for private links';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      await onSubmit(form);
    } catch (error) {
      console.error('Failed to create shared link:', error);
    }
  };

  const addAllowedUser = () => {
    if (userEmail.trim() && !form.allowed_users.includes(userEmail.trim())) {
      setForm(prev => ({
        ...prev,
        allowed_users: [...prev.allowed_users, userEmail.trim()]
      }));
      setUserEmail('');
    }
  };

  const removeAllowedUser = (email: string) => {
    setForm(prev => ({
      ...prev,
      allowed_users: prev.allowed_users.filter(user => user !== email)
    }));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addAllowedUser();
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <div className="flex items-center justify-center mb-2">
          <Share2 className="w-6 h-6 text-green-600 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">Create Shared Link</h3>
        </div>
        <p className="text-sm text-gray-600">
          Create a secure shared link for: <span className="font-medium">{proxyConnectorName}</span>
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Link Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm(prev => ({ ...prev, name: e.target.value }))}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 ${
                errors.name ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder="Customer API Access"
            />
            {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description <span className="text-red-500">*</span>
            </label>
            <textarea
              value={form.description}
              onChange={(e) => setForm(prev => ({ ...prev, description: e.target.value }))}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 ${
                errors.description ? 'border-red-300' : 'border-gray-300'
              }`}
              rows={3}
              placeholder="Describe what this shared link provides access to..."
            />
            {errors.description && <p className="mt-1 text-sm text-red-600">{errors.description}</p>}
          </div>
        </div>

        {/* Access Control */}
        <div>
          <h4 className="text-md font-medium text-gray-900 mb-4 flex items-center">
            <Lock className="w-4 h-4 mr-2" />
            Access Control
          </h4>
          
          <div className="space-y-4">
            {/* Public/Private Toggle */}
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center space-x-3">
                {form.is_public ? (
                  <Globe className="w-5 h-5 text-green-600" />
                ) : (
                  <Lock className="w-5 h-5 text-blue-600" />
                )}
                <div>
                  <h5 className="font-medium text-gray-900">
                    {form.is_public ? 'Public Access' : 'Private Access'}
                  </h5>
                  <p className="text-sm text-gray-600">
                    {form.is_public 
                      ? 'Anyone with the link can access this resource'
                      : 'Only specified users can access this resource'
                    }
                  </p>
                </div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.is_public}
                  onChange={(e) => setForm(prev => ({ 
                    ...prev, 
                    is_public: e.target.checked,
                    allowed_users: e.target.checked ? [] : prev.allowed_users
                  }))}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
              </label>
            </div>

            {/* Authentication Requirement */}
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center space-x-3">
                <Users className="w-5 h-5 text-blue-600" />
                <div>
                  <h5 className="font-medium text-gray-900">Require Authentication</h5>
                  <p className="text-sm text-gray-600">
                    Users must be logged in to access this link
                  </p>
                </div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.requires_authentication}
                  onChange={(e) => setForm(prev => ({ ...prev, requires_authentication: e.target.checked }))}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            {/* Allowed Users (for private links) */}
            {!form.is_public && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Allowed Users <span className="text-red-500">*</span>
                </label>
                <div className="space-y-2">
                  <div className="flex space-x-2">
                    <input
                      type="email"
                      value={userEmail}
                      onChange={(e) => setUserEmail(e.target.value)}
                      onKeyPress={handleKeyPress}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                      placeholder="user@example.com"
                    />
                    <button
                      type="button"
                      onClick={addAllowedUser}
                      className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                    >
                      Add
                    </button>
                  </div>
                  
                  {form.allowed_users.length > 0 && (
                    <div className="space-y-1">
                      {form.allowed_users.map((email, index) => (
                        <div key={index} className="flex items-center justify-between bg-gray-50 px-3 py-2 rounded-md">
                          <span className="text-sm text-gray-700">{email}</span>
                          <button
                            type="button"
                            onClick={() => removeAllowedUser(email)}
                            className="text-red-600 hover:text-red-800 text-sm"
                          >
                            Remove
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {errors.allowed_users && <p className="text-sm text-red-600">{errors.allowed_users}</p>}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Expiration and Limits */}
        <div>
          <h4 className="text-md font-medium text-gray-900 mb-4 flex items-center">
            <Clock className="w-4 h-4 mr-2" />
            Expiration & Limits
          </h4>
          
          <div className="grid grid-cols-1 gap-4">

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Hash className="w-4 h-4 inline mr-1" />
                Maximum Uses
              </label>
              <input
                type="number"
                value={form.max_uses || ''}
                onChange={(e) => setForm(prev => ({ 
                  ...prev, 
                  max_uses: e.target.value ? parseInt(e.target.value) : null 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                placeholder="100"
                min="1"
              />
              <p className="mt-1 text-xs text-gray-500">Leave empty for unlimited uses</p>
            </div>
          </div>
        </div>

        {/* Preview */}
        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <h4 className="text-sm font-medium text-green-800 mb-2">Link Preview</h4>
          <div className="text-sm text-green-700 space-y-1">
            <p><strong>Name:</strong> {form.name || 'Untitled Link'}</p>
            <p><strong>Access:</strong> {form.is_public ? 'Public' : 'Private'}</p>
            <p><strong>Authentication:</strong> {form.requires_authentication ? 'Required' : 'Not Required'}</p>
            {!form.is_public && (
              <p><strong>Allowed Users:</strong> {form.allowed_users.length} user(s)</p>
            )}
            {form.max_uses && (
              <p><strong>Usage Limit:</strong> {form.max_uses} uses</p>
            )}
          </div>
        </div>

        {/* Form Actions */}
        <div className="flex justify-end space-x-3 pt-4">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
          >
            {isSubmitting ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Creating...
              </>
            ) : (
              <>
                <Share2 className="w-4 h-4 mr-1" />
                Create Shared Link
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}