'use client';

import { useState, useEffect } from 'react';
import { 
  Cloud, 
  HardDrive, 
  RefreshCw, 
  Database, 
  AlertTriangle,
  CheckCircle,
  Settings,
  Zap,
  Shield
} from 'lucide-react';

interface StorageStatus {
  current_backend: string;
  storage_strategy: string;
  local_backend_available: boolean;
  s3_backend_available: boolean;
  backend_info: {
    backend_type: string;
    storage_type: string;
    bucket_name?: string;
    region?: string;
    local_storage_dir?: string;
    supports_presigned_urls?: boolean;
  };
}

interface StorageStatusWidgetProps {
  showDetails?: boolean;
  className?: string;
}

export default function StorageStatusWidget({ showDetails = true, className = "" }: StorageStatusWidgetProps) {
  const [storageStatus, setStorageStatus] = useState<StorageStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStorageStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/admin/storage/status', {
        credentials: 'include',
      });
      
      if (response.ok) {
        const data = await response.json();
        setStorageStatus(data);
        setError(null);
      } else {
        throw new Error('Failed to fetch storage status');
      }
    } catch (error) {
      console.error('Error fetching storage status:', error);
      setError('Failed to load storage status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStorageStatus();
  }, []);

  const getStrategyIcon = (strategy: string) => {
    switch (strategy) {
      case 'local_primary': return <HardDrive className="h-4 w-4" />;
      case 's3_primary': return <Cloud className="h-4 w-4" />;
      case 'hybrid': return <Zap className="h-4 w-4" />;
      case 'redundant': return <Shield className="h-4 w-4" />;
      default: return <Database className="h-4 w-4" />;
    }
  };

  const getStrategyColor = (strategy: string) => {
    switch (strategy) {
      case 'local_primary': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 's3_primary': return 'text-green-600 bg-green-50 border-green-200';
      case 'hybrid': return 'text-purple-600 bg-purple-50 border-purple-200';
      case 'redundant': return 'text-orange-600 bg-orange-50 border-orange-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg border p-4 ${className}`}>
        <div className="flex items-center">
          <RefreshCw className="h-4 w-4 animate-spin text-gray-400 mr-2" />
          <span className="text-sm text-gray-500">Loading storage status...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
        <div className="flex items-center">
          <AlertTriangle className="h-4 w-4 text-red-600 mr-2" />
          <span className="text-sm text-red-800">{error}</span>
          <button
            onClick={fetchStorageStatus}
            className="ml-auto text-red-600 hover:text-red-800"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>
    );
  }

  if (!storageStatus) {
    return null;
  }

  return (
    <div className={`bg-white rounded-lg border p-4 ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-900 flex items-center">
          <Database className="h-4 w-4 mr-2 text-gray-600" />
          Storage Status
        </h3>
        <div className="flex items-center space-x-2">
          <button
            onClick={fetchStorageStatus}
            className="text-gray-400 hover:text-gray-600"
            title="Refresh status"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
          <a
            href="/admin/storage"
            className="text-blue-600 hover:text-blue-800"
            title="Manage storage"
          >
            <Settings className="h-4 w-4" />
          </a>
        </div>
      </div>

      <div className={`flex items-center px-3 py-2 rounded-lg border text-sm font-medium ${getStrategyColor(storageStatus.storage_strategy)}`}>
        {getStrategyIcon(storageStatus.storage_strategy)}
        <span className="ml-2 capitalize">
          {storageStatus.storage_strategy.replace('_', ' ')} Strategy
        </span>
      </div>

      {showDetails && (
        <div className="mt-3 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center">
              <HardDrive className={`h-3 w-3 mr-1 ${storageStatus.local_backend_available ? 'text-green-600' : 'text-gray-400'}`} />
              <span className={storageStatus.local_backend_available ? 'text-green-600' : 'text-gray-500'}>
                Local
              </span>
            </div>
            <div className="flex items-center">
              <Cloud className={`h-3 w-3 mr-1 ${storageStatus.s3_backend_available ? 'text-green-600' : 'text-gray-400'}`} />
              <span className={storageStatus.s3_backend_available ? 'text-green-600' : 'text-gray-500'}>
                S3
              </span>
            </div>
          </div>

          {storageStatus.backend_info.bucket_name && (
            <div className="text-xs text-gray-600 bg-gray-50 px-2 py-1 rounded">
              Bucket: {storageStatus.backend_info.bucket_name}
            </div>
          )}

          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>Backend: {storageStatus.backend_info.backend_type}</span>
            {storageStatus.backend_info.supports_presigned_urls && (
              <CheckCircle className="h-3 w-3 text-green-600" title="Supports presigned URLs" />
            )}
          </div>
        </div>
      )}
    </div>
  );
}