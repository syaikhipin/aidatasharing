'use client';

import React, { useState } from 'react';
import { Shield, Database, Globe, Link, Eye, EyeOff, Plus, AlertTriangle } from 'lucide-react';

interface ProxyConnectorFormProps {
  onSubmit: (data: ProxyConnectorData) => Promise<void>;
  onCancel: () => void;
  isSubmitting: boolean;
}

interface ProxyConnectorData {
  name: string;
  connector_type: string;
  description: string;
  real_connection_config: Record<string, any>;
  real_credentials: Record<string, any>;
  is_public: boolean;
  allowed_operations: string[];
}

const CONNECTOR_TYPES = [
  {
    value: 'api',
    label: 'API Proxy',
    icon: <Globe className="w-5 h-5" />,
    description: 'Hide API endpoints and credentials from users',
    operations: ['GET', 'POST', 'PUT', 'DELETE']
  },
  {
    value: 'database',
    label: 'Database Proxy',
    icon: <Database className="w-5 h-5" />,
    description: 'Secure database access with hidden connection details',
    operations: ['SELECT', 'INSERT', 'UPDATE', 'DELETE']
  },
  {
    value: 'shared_link',
    label: 'Shared Link Proxy',
    icon: <Link className="w-5 h-5" />,
    description: 'Create secure proxy links for external resources',
    operations: ['access', 'download']
  }
];

const OPERATION_TEMPLATES = {
  api: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
  database: ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP'],
  shared_link: ['access', 'download', 'view']
};

export default function ProxyConnectorForm({ onSubmit, onCancel, isSubmitting }: ProxyConnectorFormProps) {
  const [form, setForm] = useState<ProxyConnectorData>({
    name: '',
    connector_type: 'api',
    description: '',
    real_connection_config: {},
    real_credentials: {},
    is_public: false,
    allowed_operations: []
  });

  const [showCredentials, setShowCredentials] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const selectedConnector = CONNECTOR_TYPES.find(type => type.value === form.connector_type);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!form.name.trim()) {
      newErrors.name = 'Proxy name is required';
    }

    if (!form.description.trim()) {
      newErrors.description = 'Description is required';
    }

    // Validate based on connector type
    if (form.connector_type === 'api') {
      if (!form.real_connection_config.base_url) {
        newErrors.base_url = 'Base URL is required for API proxy';
      }
    } else if (form.connector_type === 'database') {
      if (!form.real_connection_config.host) {
        newErrors.host = 'Host is required for database proxy';
      }
      if (!form.real_connection_config.database) {
        newErrors.database = 'Database name is required';
      }
    } else if (form.connector_type === 'shared_link') {
      if (!form.real_connection_config.target_url) {
        newErrors.target_url = 'Target URL is required for shared link proxy';
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

    try {
      await onSubmit(form);
    } catch (error) {
      console.error('Failed to create proxy connector:', error);
    }
  };

  const handleConnectorTypeChange = (connectorType: string) => {
    setForm(prev => ({
      ...prev,
      connector_type: connectorType,
      real_connection_config: {},
      real_credentials: {},
      allowed_operations: OPERATION_TEMPLATES[connectorType as keyof typeof OPERATION_TEMPLATES] || []
    }));
    setErrors({});
  };

  const handleOperationToggle = (operation: string) => {
    setForm(prev => ({
      ...prev,
      allowed_operations: prev.allowed_operations.includes(operation)
        ? prev.allowed_operations.filter(op => op !== operation)
        : [...prev.allowed_operations, operation]
    }));
  };

  const renderConfigFields = () => {
    switch (form.connector_type) {
      case 'api':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Base URL <span className="text-red-500">*</span>
              </label>
              <input
                type="url"
                value={form.real_connection_config.base_url || ''}
                onChange={(e) => setForm(prev => ({
                  ...prev,
                  real_connection_config: { ...prev.real_connection_config, base_url: e.target.value }
                }))}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.base_url ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="https://api.example.com"
              />
              {errors.base_url && <p className="mt-1 text-sm text-red-600">{errors.base_url}</p>}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Default Endpoint
              </label>
              <input
                type="text"
                value={form.real_connection_config.endpoint || ''}
                onChange={(e) => setForm(prev => ({
                  ...prev,
                  real_connection_config: { ...prev.real_connection_config, endpoint: e.target.value }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="/api/v1"
              />
            </div>
          </div>
        );

      case 'database':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Host <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.real_connection_config.host || ''}
                  onChange={(e) => setForm(prev => ({
                    ...prev,
                    real_connection_config: { ...prev.real_connection_config, host: e.target.value }
                  }))}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.host ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="localhost"
                />
                {errors.host && <p className="mt-1 text-sm text-red-600">{errors.host}</p>}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Port
                </label>
                <input
                  type="number"
                  value={form.real_connection_config.port || ''}
                  onChange={(e) => setForm(prev => ({
                    ...prev,
                    real_connection_config: { ...prev.real_connection_config, port: parseInt(e.target.value) }
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="5432"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Database Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={form.real_connection_config.database || ''}
                onChange={(e) => setForm(prev => ({
                  ...prev,
                  real_connection_config: { ...prev.real_connection_config, database: e.target.value }
                }))}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.database ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="mydb"
              />
              {errors.database && <p className="mt-1 text-sm text-red-600">{errors.database}</p>}
            </div>
          </div>
        );

      case 'shared_link':
        return (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target URL <span className="text-red-500">*</span>
            </label>
            <input
              type="url"
              value={form.real_connection_config.target_url || ''}
              onChange={(e) => setForm(prev => ({
                ...prev,
                real_connection_config: { ...prev.real_connection_config, target_url: e.target.value }
              }))}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.target_url ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder="https://example.com/resource"
            />
            {errors.target_url && <p className="mt-1 text-sm text-red-600">{errors.target_url}</p>}
          </div>
        );

      default:
        return null;
    }
  };

  const renderCredentialFields = () => {
    switch (form.connector_type) {
      case 'api':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                API Key
              </label>
              <div className="relative">
                <input
                  type={showCredentials ? 'text' : 'password'}
                  value={form.real_credentials.api_key || ''}
                  onChange={(e) => setForm(prev => ({
                    ...prev,
                    real_credentials: { ...prev.real_credentials, api_key: e.target.value }
                  }))}
                  className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="your-api-key"
                />
                <button
                  type="button"
                  onClick={() => setShowCredentials(!showCredentials)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  {showCredentials ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Auth Header Name
              </label>
              <input
                type="text"
                value={form.real_credentials.auth_header || 'Authorization'}
                onChange={(e) => setForm(prev => ({
                  ...prev,
                  real_credentials: { ...prev.real_credentials, auth_header: e.target.value }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Authorization"
              />
            </div>
          </div>
        );

      case 'database':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Username
              </label>
              <input
                type="text"
                value={form.real_credentials.username || ''}
                onChange={(e) => setForm(prev => ({
                  ...prev,
                  real_credentials: { ...prev.real_credentials, username: e.target.value }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="username"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  type={showCredentials ? 'text' : 'password'}
                  value={form.real_credentials.password || ''}
                  onChange={(e) => setForm(prev => ({
                    ...prev,
                    real_credentials: { ...prev.real_credentials, password: e.target.value }
                  }))}
                  className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="password"
                />
                <button
                  type="button"
                  onClick={() => setShowCredentials(!showCredentials)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  {showCredentials ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <div className="flex items-center justify-center mb-2">
          <Shield className="w-6 h-6 text-blue-600 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">Create Secure Proxy</h3>
        </div>
        <p className="text-sm text-gray-600">
          Hide real URLs and credentials while providing secure access to your resources
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Connector Type Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Proxy Type
          </label>
          <div className="grid grid-cols-1 gap-3">
            {CONNECTOR_TYPES.map((type) => (
              <button
                key={type.value}
                type="button"
                onClick={() => handleConnectorTypeChange(type.value)}
                className={`p-4 border rounded-lg text-left transition-colors ${
                  form.connector_type === type.value
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-start space-x-3">
                  <div className={`mt-1 ${form.connector_type === type.value ? 'text-blue-600' : 'text-gray-500'}`}>
                    {type.icon}
                  </div>
                  <div>
                    <h4 className={`font-medium ${form.connector_type === type.value ? 'text-blue-900' : 'text-gray-900'}`}>
                      {type.label}
                    </h4>
                    <p className={`text-sm ${form.connector_type === type.value ? 'text-blue-700' : 'text-gray-600'}`}>
                      {type.description}
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Basic Information */}
        <div className="grid grid-cols-1 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Proxy Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm(prev => ({ ...prev, name: e.target.value }))}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.name ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder="My Secure API Proxy"
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
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.description ? 'border-red-300' : 'border-gray-300'
              }`}
              rows={3}
              placeholder="Describe what this proxy provides access to..."
            />
            {errors.description && <p className="mt-1 text-sm text-red-600">{errors.description}</p>}
          </div>
        </div>

        {/* Connection Configuration */}
        <div>
          <h4 className="text-md font-medium text-gray-900 mb-4">Connection Configuration</h4>
          {renderConfigFields()}
        </div>

        {/* Credentials */}
        <div>
          <h4 className="text-md font-medium text-gray-900 mb-4">Credentials (Hidden from Users)</h4>
          {renderCredentialFields()}
        </div>

        {/* Allowed Operations */}
        <div>
          <h4 className="text-md font-medium text-gray-900 mb-4">Allowed Operations</h4>
          <div className="flex flex-wrap gap-2">
            {OPERATION_TEMPLATES[form.connector_type as keyof typeof OPERATION_TEMPLATES]?.map((operation) => (
              <button
                key={operation}
                type="button"
                onClick={() => handleOperationToggle(operation)}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                  form.allowed_operations.includes(operation)
                    ? 'bg-blue-100 text-blue-800 border border-blue-200'
                    : 'bg-gray-100 text-gray-700 border border-gray-200 hover:bg-gray-200'
                }`}
              >
                {operation}
              </button>
            ))}
          </div>
        </div>

        {/* Access Control */}
        <div>
          <h4 className="text-md font-medium text-gray-900 mb-4">Access Control</h4>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={form.is_public}
              onChange={(e) => setForm(prev => ({ ...prev, is_public: e.target.checked }))}
              className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
            />
            <span className="ml-2 text-sm text-gray-700">
              Make this proxy publicly accessible (no authentication required)
            </span>
          </label>
        </div>

        {/* Security Notice */}
        <div className="bg-amber-50 border border-amber-200 rounded-md p-4">
          <div className="flex">
            <AlertTriangle className="w-5 h-5 text-amber-400 mt-0.5" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-amber-800">Security Notice</h3>
              <div className="mt-2 text-sm text-amber-700">
                <p>
                  This proxy will hide your real connection details and credentials from users. 
                  Only the proxy URL will be visible, ensuring your sensitive information remains secure.
                </p>
              </div>
            </div>
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
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
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
                <Shield className="w-4 h-4 mr-1" />
                Create Secure Proxy
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}