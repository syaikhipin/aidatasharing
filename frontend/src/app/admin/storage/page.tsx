'use client';

import { useState, useEffect } from 'react';
import StorageTestUploader from '@/components/StorageTestUploader';
import { 
  Cloud, 
  HardDrive, 
  RefreshCw, 
  Database, 
  Upload, 
  Download, 
  AlertTriangle,
  CheckCircle,
  Settings,
  BarChart3,
  FileText,
  Zap,
  Shield,
  Info
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

interface StorageRecommendations {
  analysis: {
    total_datasets: number;
    total_size_mb: number;
    large_files_count: number;
    small_files_count: number;
    multi_file_datasets: number;
    single_file_datasets: number;
    recommendations: Array<{
      strategy: string;
      reason: string;
      priority: string;
    }>;
  };
}

interface MigrationResult {
  message: string;
  result?: {
    target_backend: string;
    datasets_processed: any[];
    datasets_failed: any[];
    total_datasets: number;
    total_files: number;
    success_files: number;
    failed_files: number;
  };
}

export default function StorageManagementPage() {
  const [storageStatus, setStorageStatus] = useState<StorageStatus | null>(null);
  const [recommendations, setRecommendations] = useState<StorageRecommendations | null>(null);
  const [loading, setLoading] = useState(true);
  const [migrating, setMigrating] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [migrationResult, setMigrationResult] = useState<MigrationResult | null>(null);
  const [verificationResult, setVerificationResult] = useState<any>(null);
  const [selectedMigrationTarget, setSelectedMigrationTarget] = useState<'local' | 's3'>('s3');
  const [error, setError] = useState<string | null>(null);

  const fetchStorageStatus = async () => {
    try {
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
    }
  };

  const fetchRecommendations = async () => {
    try {
      const response = await fetch('/api/admin/storage/recommendations', {
        credentials: 'include',
      });
      
      if (response.ok) {
        const data = await response.json();
        setRecommendations(data);
      } else {
        console.error('Failed to fetch recommendations');
      }
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    }
  };

  const handleMigration = async () => {
    setMigrating(true);
    setMigrationResult(null);
    try {
      const response = await fetch('/api/admin/storage/migrate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          target_backend: selectedMigrationTarget,
        }),
      });
      
      if (response.ok) {
        const data = await response.json();
        setMigrationResult(data);
        // Refresh storage status after migration
        await fetchStorageStatus();
      } else {
        throw new Error('Migration failed');
      }
    } catch (error) {
      console.error('Migration error:', error);
      setError('Migration failed');
    } finally {
      setMigrating(false);
    }
  };

  const handleVerification = async () => {
    setVerifying(true);
    setVerificationResult(null);
    try {
      const response = await fetch('/api/admin/storage/verify', {
        method: 'POST',
        credentials: 'include',
      });
      
      if (response.ok) {
        const data = await response.json();
        setVerificationResult(data.result);
      } else {
        throw new Error('Verification failed');
      }
    } catch (error) {
      console.error('Verification error:', error);
      setError('Storage verification failed');
    } finally {
      setVerifying(false);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchStorageStatus(),
        fetchRecommendations(),
      ]);
      setLoading(false);
    };
    
    loadData();
  }, []);

  const getStrategyIcon = (strategy: string) => {
    switch (strategy) {
      case 'local_primary': return <HardDrive className="h-5 w-5" />;
      case 's3_primary': return <Cloud className="h-5 w-5" />;
      case 'hybrid': return <Zap className="h-5 w-5" />;
      case 'redundant': return <Shield className="h-5 w-5" />;
      default: return <Database className="h-5 w-5" />;
    }
  };

  const getStrategyColor = (strategy: string) => {
    switch (strategy) {
      case 'local_primary': return 'text-blue-600 bg-blue-50';
      case 's3_primary': return 'text-green-600 bg-green-50';
      case 'hybrid': return 'text-purple-600 bg-purple-50';
      case 'redundant': return 'text-orange-600 bg-orange-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-50 border-red-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-green-600 bg-green-50 border-green-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading storage management...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <Settings className="h-8 w-8 mr-3 text-blue-600" />
          Storage Management & Testing
        </h1>
        <p className="mt-2 text-gray-600">
          Manage and test your dual storage system (Local + S3) configuration
        </p>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <AlertTriangle className="h-5 w-5 text-red-600 mr-2" />
            <p className="text-red-800">{error}</p>
          </div>
        </div>
      )}

      {/* Storage Status Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center mb-4">
            <Database className="h-6 w-6 text-blue-600 mr-2" />
            <h2 className="text-xl font-semibold">Current Storage Configuration</h2>
          </div>
          
          {storageStatus && (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="font-medium">Storage Strategy:</span>
                <div className={`flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStrategyColor(storageStatus.storage_strategy)}`}>
                  {getStrategyIcon(storageStatus.storage_strategy)}
                  <span className="ml-2 capitalize">{storageStatus.storage_strategy.replace('_', ' ')}</span>
                </div>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="font-medium">Backend Type:</span>
                <span className="text-gray-700 font-medium">{storageStatus.backend_info.backend_type}</span>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 border rounded-lg">
                  <HardDrive className={`h-8 w-8 mx-auto mb-2 ${storageStatus.local_backend_available ? 'text-green-600' : 'text-gray-400'}`} />
                  <p className="text-sm font-medium">Local Storage</p>
                  <p className={`text-xs ${storageStatus.local_backend_available ? 'text-green-600' : 'text-gray-500'}`}>
                    {storageStatus.local_backend_available ? 'Available' : 'Unavailable'}
                  </p>
                </div>
                
                <div className="text-center p-3 border rounded-lg">
                  <Cloud className={`h-8 w-8 mx-auto mb-2 ${storageStatus.s3_backend_available ? 'text-green-600' : 'text-gray-400'}`} />
                  <p className="text-sm font-medium">S3 Storage</p>
                  <p className={`text-xs ${storageStatus.s3_backend_available ? 'text-green-600' : 'text-gray-500'}`}>
                    {storageStatus.s3_backend_available ? 'Available' : 'Unavailable'}
                  </p>
                </div>
              </div>

              {storageStatus.backend_info.bucket_name && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-sm"><strong>S3 Bucket:</strong> {storageStatus.backend_info.bucket_name}</p>
                  {storageStatus.backend_info.region && (
                    <p className="text-sm"><strong>Region:</strong> {storageStatus.backend_info.region}</p>
                  )}
                </div>
              )}

              {storageStatus.backend_info.local_storage_dir && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm"><strong>Local Directory:</strong> {storageStatus.backend_info.local_storage_dir}</p>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center mb-4">
            <BarChart3 className="h-6 w-6 text-green-600 mr-2" />
            <h2 className="text-xl font-semibold">Storage Analytics</h2>
          </div>
          
          {recommendations && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <p className="text-2xl font-bold text-blue-600">{recommendations.analysis.total_datasets}</p>
                  <p className="text-sm text-gray-600">Total Datasets</p>
                </div>
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <p className="text-2xl font-bold text-green-600">{recommendations.analysis.total_size_mb.toFixed(1)} MB</p>
                  <p className="text-sm text-gray-600">Total Size</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-purple-50 rounded-lg">
                  <p className="text-xl font-bold text-purple-600">{recommendations.analysis.large_files_count}</p>
                  <p className="text-sm text-gray-600">Large Files (>10MB)</p>
                </div>
                <div className="text-center p-3 bg-orange-50 rounded-lg">
                  <p className="text-xl font-bold text-orange-600">{recommendations.analysis.small_files_count}</p>
                  <p className="text-sm text-gray-600">Small Files (<10MB)</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Storage Recommendations */}
      {recommendations && recommendations.analysis.recommendations.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <div className="flex items-center mb-4">
            <Info className="h-6 w-6 text-blue-600 mr-2" />
            <h2 className="text-xl font-semibold">Storage Strategy Recommendations</h2>
          </div>
          
          <div className="space-y-3">
            {recommendations.analysis.recommendations.map((rec, index) => (
              <div key={index} className={`p-4 border rounded-lg ${getPriorityColor(rec.priority)}`}>
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center mb-2">
                      {getStrategyIcon(rec.strategy)}
                      <h3 className="font-semibold ml-2 capitalize">{rec.strategy.replace('_', ' ')}</h3>
                      <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium uppercase ${getPriorityColor(rec.priority)}`}>
                        {rec.priority}
                      </span>
                    </div>
                    <p className="text-sm">{rec.reason}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Storage Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center mb-4">
            <RefreshCw className="h-6 w-6 text-purple-600 mr-2" />
            <h2 className="text-xl font-semibold">Storage Migration</h2>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Migration Target:
              </label>
              <select
                value={selectedMigrationTarget}
                onChange={(e) => setSelectedMigrationTarget(e.target.value as 'local' | 's3')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="s3">Migrate to S3 Storage</option>
                <option value="local">Migrate to Local Storage</option>
              </select>
            </div>
            
            <button
              onClick={handleMigration}
              disabled={migrating}
              className="w-full flex items-center justify-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
            >
              {migrating ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Migrating All Datasets...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Migrate All Datasets to {selectedMigrationTarget.toUpperCase()}
                </>
              )}
            </button>
          </div>

          {migrationResult && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-start">
                <CheckCircle className="h-5 w-5 text-green-600 mr-2 mt-0.5" />
                <div>
                  <p className="text-green-800 font-medium">{migrationResult.message}</p>
                  {migrationResult.result && (
                    <div className="mt-2 text-sm text-green-700">
                      <p>Datasets processed: {migrationResult.result.datasets_processed.length}</p>
                      <p>Files migrated: {migrationResult.result.success_files}</p>
                      {migrationResult.result.failed_files > 0 && (
                        <p className="text-red-600">Failed files: {migrationResult.result.failed_files}</p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center mb-4">
            <Shield className="h-6 w-6 text-orange-600 mr-2" />
            <h2 className="text-xl font-semibold">Storage Verification</h2>
          </div>
          
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Verify that all database file references have corresponding physical files and clean up orphaned files.
            </p>
            
            <button
              onClick={handleVerification}
              disabled={verifying}
              className="w-full flex items-center justify-center px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-orange-500 disabled:opacity-50"
            >
              {verifying ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Verifying Storage...
                </>
              ) : (
                <>
                  <Shield className="h-4 w-4 mr-2" />
                  Verify Storage Integrity
                </>
              )}
            </button>
          </div>

          {verificationResult && (
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="space-y-2 text-sm">
                <p><strong>Datasets checked:</strong> {verificationResult.datasets_checked}</p>
                <p><strong>Files checked:</strong> {verificationResult.files_checked}</p>
                <p><strong>Integrity issues:</strong> {verificationResult.integrity_issues}</p>
                <p><strong>Orphaned files cleaned:</strong> {verificationResult.orphaned_files?.length || 0}</p>
                
                {verificationResult.missing_files && verificationResult.missing_files.length > 0 && (
                  <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded">
                    <p className="font-medium text-red-800">Missing Files:</p>
                    <ul className="mt-1 text-red-700">
                      {verificationResult.missing_files.slice(0, 5).map((file: any, index: number) => (
                        <li key={index}>• {file.dataset_name}: {file.file_path}</li>
                      ))}
                      {verificationResult.missing_files.length > 5 && (
                        <li>... and {verificationResult.missing_files.length - 5} more</li>
                      )}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Testing Section */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center mb-4">
          <FileText className="h-6 w-6 text-indigo-600 mr-2" />
          <h2 className="text-xl font-semibold">S3 Storage Testing</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-lg text-center">
            <Upload className="h-8 w-8 text-indigo-600 mx-auto mb-2" />
            <h3 className="font-medium text-indigo-900">Upload Test</h3>
            <p className="text-sm text-indigo-700 mb-3">Test file uploads with current strategy</p>
            <button 
              onClick={() => window.location.href = '/datasets/upload'}
              className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 text-sm"
            >
              Go to Upload
            </button>
          </div>

          <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-center">
            <Download className="h-8 w-8 text-green-600 mx-auto mb-2" />
            <h3 className="font-medium text-green-900">Download Test</h3>
            <p className="text-sm text-green-700 mb-3">Test shared dataset downloads</p>
            <button 
              onClick={() => window.location.href = '/datasets'}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
            >
              View Datasets
            </button>
          </div>

          <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg text-center">
            <Settings className="h-8 w-8 text-purple-600 mx-auto mb-2" />
            <h3 className="font-medium text-purple-900">Configuration Test</h3>
            <p className="text-sm text-purple-700 mb-3">Test different storage strategies</p>
            <button 
              onClick={() => fetchStorageStatus()}
              className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 text-sm"
            >
              Refresh Status
            </button>
          </div>
        </div>
      </div>

      {/* Storage Test Uploader */}
      <StorageTestUploader className="mb-8" />
    </div>
  );
}