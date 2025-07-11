'use client';

import { useState, useEffect } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { dataConnectorsAPI } from '@/lib/api';
import { 
  Database, 
  Plus, 
  TestTube, 
  CheckCircle, 
  XCircle, 
  Clock,
  Settings,
  Trash2,
  Wifi,
  WifiOff,
  RefreshCw,
  AlertCircle,
  Eye,
  EyeOff
} from 'lucide-react';

interface DatabaseConnector {
  id: number;
  name: string;
  connector_type: string;
  description?: string;
  is_active: boolean;
  test_status: 'untested' | 'success' | 'failed';
  last_tested_at?: string;
  created_at: string;
  mindsdb_database_name?: string;
  organization_id: number;
  datasets?: Array<{
    id: number;
    name: string;
    type: string;
    sharing_level: string;
    public_share_enabled?: boolean;
  }>;
}

interface ConnectorForm {
  name: string;
  connector_type: string;
  description: string;
  connection_config: Record<string, any>;
  credentials: Record<string, any>;
}

const initialForm: ConnectorForm = {
  name: '',
  connector_type: 'mysql',
  description: '',
  connection_config: {},
  credentials: {}
};

const CONNECTOR_TYPES = [
  { value: 'mysql', label: 'MySQL', icon: '🐬' },
  { value: 'postgresql', label: 'PostgreSQL', icon: '🐘' },
  { value: 's3', label: 'Amazon S3', icon: '☁️' },
  { value: 'mongodb', label: 'MongoDB', icon: '🍃' },
  { value: 'clickhouse', label: 'ClickHouse', icon: '⚡' },
  { value: 'api', label: 'REST API', icon: '🔗' },
];

function ConnectionsPageContent() {
  const [connectors, setConnectors] = useState<DatabaseConnector[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [form, setForm] = useState<ConnectorForm>(initialForm);
  const [creating, setCreating] = useState(false);
  const [testing, setTesting] = useState<Record<number, boolean>>({});
  const [syncing, setSyncing] = useState<Record<number, boolean>>({});
  const [showCredentials, setShowCredentials] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    fetchConnectors();
  }, []);

  const fetchConnectors = async () => {
    try {
      const response = await dataConnectorsAPI.getConnectors({ include_datasets: true });
      setConnectors(response);
    } catch (error) {
      console.error('Failed to fetch connectors:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateConnector = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setErrors({});

    try {
      await dataConnectorsAPI.createConnector(form);
      setShowCreateModal(false);
      setForm(initialForm);
      fetchConnectors();
    } catch (error: any) {
      setErrors({ general: error.response?.data?.detail || 'Failed to create connector' });
    } finally {
      setCreating(false);
    }
  };

  const handleTestConnection = async (connectorId: number) => {
    setTesting(prev => ({ ...prev, [connectorId]: true }));
    
    try {
      await dataConnectorsAPI.testConnector(connectorId);
      fetchConnectors(); // Refresh to get updated status
    } catch (error) {
      console.error('Test failed:', error);
    } finally {
      setTesting(prev => ({ ...prev, [connectorId]: false }));
    }
  };

  const handleSyncWithMindsDB = async (connectorId: number) => {
    setSyncing(prev => ({ ...prev, [connectorId]: true }));
    
    try {
      await dataConnectorsAPI.syncWithMindsDB(connectorId);
      // Show success message or refresh data
    } catch (error) {
      console.error('Sync failed:', error);
    } finally {
      setSyncing(prev => ({ ...prev, [connectorId]: false }));
    }
  };

  const handleDeleteConnector = async (connectorId: number) => {
    if (!confirm('Are you sure you want to delete this connector?')) return;
    
    try {
      await dataConnectorsAPI.deleteConnector(connectorId);
      fetchConnectors();
    } catch (error) {
      console.error('Delete failed:', error);
    }
  };

  const renderConnectionForm = () => {
    const selectedType = CONNECTOR_TYPES.find(t => t.value === form.connector_type);
    
    return (
      <form onSubmit={handleCreateConnector} className="space-y-6">
        {errors.general && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-red-600 text-sm">{errors.general}</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Connection Name
            </label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm(prev => ({ ...prev, name: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="My Database Connection"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Connection Type
            </label>
            <select
              value={form.connector_type}
              onChange={(e) => setForm(prev => ({ 
                ...prev, 
                connector_type: e.target.value,
                connection_config: {},
                credentials: {}
              }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {CONNECTOR_TYPES.map(type => (
                <option key={type.value} value={type.value}>
                  {type.icon} {type.label}
                </option>
              ))}
            </select>
          </div>
        </div>

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

        {/* Dynamic connection configuration based on type */}
        {renderTypeSpecificFields()}

        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => setShowCreateModal(false)}
            className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={creating}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {creating ? 'Creating...' : 'Create Connection'}
          </button>
        </div>
      </form>
    );
  };

  const renderTypeSpecificFields = () => {
    switch (form.connector_type) {
      case 'mysql':
      case 'postgresql':
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Host
              </label>
              <input
                type="text"
                value={form.connection_config.host || ''}
                onChange={(e) => setForm(prev => ({
                  ...prev,
                  connection_config: { ...prev.connection_config, host: e.target.value }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="localhost"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Port
              </label>
              <input
                type="number"
                value={form.connection_config.port || ''}
                onChange={(e) => setForm(prev => ({
                  ...prev,
                  connection_config: { ...prev.connection_config, port: parseInt(e.target.value) }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={form.connector_type === 'mysql' ? '3306' : '5432'}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Database
              </label>
              <input
                type="text"
                value={form.connection_config.database || ''}
                onChange={(e) => setForm(prev => ({
                  ...prev,
                  connection_config: { ...prev.connection_config, database: e.target.value }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="database_name"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Username
              </label>
              <input
                type="text"
                value={form.credentials.user || ''}
                onChange={(e) => setForm(prev => ({
                  ...prev,
                  credentials: { ...prev.credentials, user: e.target.value }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="username"
                required
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <input
                type="password"
                value={form.credentials.password || ''}
                onChange={(e) => setForm(prev => ({
                  ...prev,
                  credentials: { ...prev.credentials, password: e.target.value }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="password"
                required
              />
            </div>
          </div>
        );

      case 's3':
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Bucket Name
              </label>
              <input
                type="text"
                value={form.connection_config.bucket || ''}
                onChange={(e) => setForm(prev => ({
                  ...prev,
                  connection_config: { ...prev.connection_config, bucket: e.target.value }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="my-bucket"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Region
              </label>
              <input
                type="text"
                value={form.connection_config.region || ''}
                onChange={(e) => setForm(prev => ({
                  ...prev,
                  connection_config: { ...prev.connection_config, region: e.target.value }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="us-east-1"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                AWS Access Key ID
              </label>
              <input
                type="text"
                value={form.credentials.aws_access_key_id || ''}
                onChange={(e) => setForm(prev => ({
                  ...prev,
                  credentials: { ...prev.credentials, aws_access_key_id: e.target.value }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="AKIA..."
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                AWS Secret Access Key
              </label>
              <input
                type="password"
                value={form.credentials.aws_secret_access_key || ''}
                onChange={(e) => setForm(prev => ({
                  ...prev,
                  credentials: { ...prev.credentials, aws_secret_access_key: e.target.value }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Secret key"
                required
              />
            </div>
          </div>
        );

      case 'mongodb':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Connection URI
              </label>
              <input
                type="text"
                value={form.connection_config.uri || ''}
                onChange={(e) => setForm(prev => ({
                  ...prev,
                  connection_config: { ...prev.connection_config, uri: e.target.value }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="mongodb://username:password@host:port/database"
                required
              />
            </div>
          </div>
        );

      default:
        return (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Configuration (JSON)
            </label>
            <textarea
              value={JSON.stringify(form.connection_config, null, 2)}
              onChange={(e) => {
                try {
                  const config = JSON.parse(e.target.value);
                  setForm(prev => ({ ...prev, connection_config: config }));
                } catch {
                  // Invalid JSON, ignore
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
              rows={6}
              placeholder="{}"
            />
          </div>
        );
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const getTypeIcon = (type: string) => {
    const connectorType = CONNECTOR_TYPES.find(t => t.value === type);
    return connectorType ? connectorType.icon : '🔗';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="md:flex md:items-center md:justify-between mb-8">
          <div className="flex-1 min-w-0">
            <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
              <Database className="inline h-8 w-8 mr-2" />
              Data Connections
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              Manage database connections and external data sources
            </p>
          </div>
          <div className="mt-4 flex md:mt-0 md:ml-4">
            <button
              onClick={() => setShowCreateModal(true)}
              className="ml-3 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Connection
            </button>
          </div>
        </div>

        {/* Connections Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {connectors.map((connector) => (
            <div key={connector.id} className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
              <div className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-center">
                    <span className="text-2xl mr-3">{getTypeIcon(connector.connector_type)}</span>
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">{connector.name}</h3>
                      <p className="text-sm text-gray-500 capitalize">{connector.connector_type}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {connector.is_active ? (
                      <Wifi className="h-5 w-5 text-green-500" />
                    ) : (
                      <WifiOff className="h-5 w-5 text-gray-400" />
                    )}
                    {getStatusIcon(connector.test_status)}
                  </div>
                </div>

                {connector.description && (
                  <p className="mt-2 text-sm text-gray-600">{connector.description}</p>
                )}

                <div className="mt-4">
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>Status: {connector.test_status}</span>
                    {connector.last_tested_at && (
                      <span>Tested: {new Date(connector.last_tested_at).toLocaleDateString()}</span>
                    )}
                  </div>
                  {connector.mindsdb_database_name && (
                    <div className="mt-1 text-xs text-blue-600">
                      MindsDB: {connector.mindsdb_database_name}
                    </div>
                  )}
                  
                  {/* Associated Datasets */}
                  {connector.datasets && connector.datasets.length > 0 && (
                    <div className="mt-3 border-t border-gray-100 pt-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-medium text-gray-500">Associated Datasets ({connector.datasets.length})</span>
                      </div>
                      <div className="space-y-1 max-h-20 overflow-y-auto">
                        {connector.datasets.map((dataset) => (
                          <div key={dataset.id} className="flex items-center justify-between text-xs">
                            <div className="flex items-center space-x-1">
                              <span className="w-2 h-2 bg-blue-400 rounded-full"></span>
                              <span className="text-gray-700 truncate" title={dataset.name}>
                                {dataset.name}
                              </span>
                            </div>
                            <div className="flex items-center space-x-1">
                              <span className="text-gray-500">{dataset.type}</span>
                              {dataset.public_share_enabled && (
                                <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                  Shared
                                </span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="mt-6 flex items-center justify-between">
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleTestConnection(connector.id)}
                      disabled={testing[connector.id]}
                      className="flex items-center px-3 py-1 text-xs font-medium text-blue-600 bg-blue-50 rounded-full hover:bg-blue-100 disabled:opacity-50"
                    >
                      {testing[connector.id] ? (
                        <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                      ) : (
                        <TestTube className="h-3 w-3 mr-1" />
                      )}
                      Test
                    </button>
                    <button
                      onClick={() => handleSyncWithMindsDB(connector.id)}
                      disabled={syncing[connector.id]}
                      className="flex items-center px-3 py-1 text-xs font-medium text-green-600 bg-green-50 rounded-full hover:bg-green-100 disabled:opacity-50"
                    >
                      {syncing[connector.id] ? (
                        <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                      ) : (
                        <Database className="h-3 w-3 mr-1" />
                      )}
                      Sync
                    </button>
                  </div>
                  <button
                    onClick={() => handleDeleteConnector(connector.id)}
                    className="text-red-600 hover:text-red-800"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {connectors.length === 0 && (
          <div className="text-center py-12">
            <Database className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No connections</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by creating your first database connection.
            </p>
            <div className="mt-6">
              <button
                onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Connection
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Create Connection Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Add New Connection</h3>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="h-6 w-6" />
                </button>
              </div>
              {renderConnectionForm()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ConnectionsPage() {
  return (
    <ProtectedRoute>
      <ConnectionsPageContent />
    </ProtectedRoute>
  );
} 