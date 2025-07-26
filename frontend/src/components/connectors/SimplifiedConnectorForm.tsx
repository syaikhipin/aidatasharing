'use client';

import React, { useState } from 'react';
import { Plus, Database, Cloud, Globe, Server } from 'lucide-react';

interface SimplifiedConnectorFormProps {
  onSubmit: (data: SimplifiedConnectorData) => Promise<void>;
  onCancel: () => void;
  isSubmitting: boolean;
}

interface SimplifiedConnectorData {
  name: string;
  description: string;
  connector_type: string;
  connection_url: string;
}

const CONNECTOR_TYPES = [
  { 
    value: 'mysql', 
    label: 'MySQL', 
    icon: <Database className="w-4 h-4" />,
    placeholder: 'mysql://username:password@host:3306/database',
    example: 'mysql://user:pass@localhost:3306/mydb'
  },
  { 
    value: 'postgresql', 
    label: 'PostgreSQL', 
    icon: <Database className="w-4 h-4" />,
    placeholder: 'postgresql://username:password@host:5432/database',
    example: 'postgresql://user:pass@localhost:5432/postgres'
  },
  { 
    value: 's3', 
    label: 'Amazon S3', 
    icon: <Cloud className="w-4 h-4" />,
    placeholder: 's3://access_key:secret_key@bucket_name/region',
    example: 's3://AKIA...:secret@my-bucket/us-east-1'
  },
  { 
    value: 'mongodb', 
    label: 'MongoDB', 
    icon: <Database className="w-4 h-4" />,
    placeholder: 'mongodb://username:password@host:27017/database',
    example: 'mongodb://user:pass@localhost:27017/mydb'
  },
  { 
    value: 'clickhouse', 
    label: 'ClickHouse', 
    icon: <Server className="w-4 h-4" />,
    placeholder: 'clickhouse://username:password@host:9000/database',
    example: 'clickhouse://default:pass@localhost:9000/default'
  },
  { 
    value: 'api', 
    label: 'REST API', 
    icon: <Globe className="w-4 h-4" />,
    placeholder: 'https://api.example.com/data?api_key=your_key',
    example: 'https://api.example.com/users?api_key=abc123'
  }
];

export default function SimplifiedConnectorForm({ onSubmit, onCancel, isSubmitting }: SimplifiedConnectorFormProps) {
  const [form, setForm] = useState<SimplifiedConnectorData>({
    name: '',
    description: '',
    connector_type: 'mysql',
    connection_url: ''
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const selectedConnector = CONNECTOR_TYPES.find(type => type.value === form.connector_type);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!form.name.trim()) {
      newErrors.name = 'Connection name is required';
    }

    if (!form.connection_url.trim()) {
      newErrors.connection_url = 'Connection URL is required';
    } else {
      // Basic URL validation
      try {
        new URL(form.connection_url);
      } catch {
        // For database URLs that might not be valid HTTP URLs, do basic format checking
        if (!form.connection_url.includes('://')) {
          newErrors.connection_url = 'Invalid URL format. Must include protocol (e.g., mysql://, https://)';
        }
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
      console.error('Failed to create connector:', error);
    }
  };

  const handleConnectorTypeChange = (connectorType: string) => {
    setForm(prev => ({
      ...prev,
      connector_type: connectorType,
      connection_url: '' // Clear URL when type changes
    }));
    setErrors({}); // Clear errors when type changes
  };

  return (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Create New Connection</h3>
        <p className="text-sm text-gray-600">
          Simply paste your connection URL or connection string - we'll handle the rest!
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Connection Type Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Connection Type
          </label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {CONNECTOR_TYPES.map((type) => (
              <button
                key={type.value}
                type="button"
                onClick={() => handleConnectorTypeChange(type.value)}
                className={`p-3 border rounded-lg text-left transition-colors ${
                  form.connector_type === type.value
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  {type.icon}
                  <span className="font-medium text-sm">{type.label}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Connection Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Connection Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={form.name}
            onChange={(e) => setForm(prev => ({ ...prev, name: e.target.value }))}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.name ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder="My Database Connection"
          />
          {errors.name && (
            <p className="mt-1 text-sm text-red-600">{errors.name}</p>
          )}
        </div>

        {/* Connection URL */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Connection URL <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={form.connection_url}
            onChange={(e) => setForm(prev => ({ ...prev, connection_url: e.target.value }))}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm ${
              errors.connection_url ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder={selectedConnector?.placeholder}
          />
          {errors.connection_url && (
            <p className="mt-1 text-sm text-red-600">{errors.connection_url}</p>
          )}
          {selectedConnector && (
            <div className="mt-2 p-3 bg-gray-50 rounded-md">
              <p className="text-xs text-gray-600 mb-1">Example:</p>
              <code className="text-xs text-gray-800 font-mono">{selectedConnector.example}</code>
            </div>
          )}
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Description
          </label>
          <textarea
            value={form.description}
            onChange={(e) => setForm(prev => ({ ...prev, description: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={3}
            placeholder="Description of this connection..."
          />
        </div>

        {/* Security Notice */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">Security Notice</h3>
              <div className="mt-2 text-sm text-yellow-700">
                <p>Your connection credentials are encrypted and stored securely. Only you and your organization members can access this connection.</p>
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
                <Plus className="w-4 h-4 mr-1" />
                Create Connection
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}