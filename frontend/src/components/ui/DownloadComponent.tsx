import React, { useState, useEffect } from 'react';
import { Download, FileType, FileSpreadsheet, FileJson, FileArchive, RefreshCw, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { datasetsAPI } from '@/lib/api';

interface DownloadComponentProps {
  dataset: any;
  onDownloadStart?: (downloadId: string) => void;
  onDownloadComplete?: () => void;
  onError?: (error: any) => void;
}

interface DownloadProgress {
  status: string;
  progress_percentage: number;
  bytes_transferred?: number;
  file_size_bytes?: number;
  transfer_rate_mbps?: string;
  estimated_time_remaining_seconds?: number;
  error_message?: string;
  is_resumable?: boolean;
  retry_url?: string;
}

const DownloadComponent: React.FC<DownloadComponentProps> = ({
  dataset,
  onDownloadStart,
  onDownloadComplete,
  onError
}) => {
  const [selectedFormat, setSelectedFormat] = useState<string>('original');
  const [compression, setCompression] = useState<string>('none');
  const [isDownloading, setIsDownloading] = useState<boolean>(false);
  const [downloadToken, setDownloadToken] = useState<string>('');
  const [downloadProgress, setDownloadProgress] = useState<DownloadProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progressInterval, setProgressInterval] = useState<NodeJS.Timeout | null>(null);

  // Clean up interval on unmount
  useEffect(() => {
    return () => {
      if (progressInterval) {
        clearInterval(progressInterval);
      }
    };
  }, [progressInterval]);

  // Format file size
  const formatFileSize = (bytes?: number): string => {
    if (bytes === undefined || bytes === null) return 'Unknown size';
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Format time remaining
  const formatTimeRemaining = (seconds?: number): string => {
    if (!seconds) return 'Calculating...';
    
    if (seconds < 60) {
      return `${Math.round(seconds)} seconds`;
    } else if (seconds < 3600) {
      return `${Math.floor(seconds / 60)} minutes ${Math.round(seconds % 60)} seconds`;
    } else {
      return `${Math.floor(seconds / 3600)} hours ${Math.floor((seconds % 3600) / 60)} minutes`;
    }
  };

  // Start download
  const startDownload = async () => {
    try {
      setIsDownloading(true);
      setError(null);
      setDownloadProgress(null);
      
      // Use the API client to initiate download
      const downloadData = await datasetsAPI.initiateDownload(
        dataset.id,
        selectedFormat,
        compression
      );
      
      const token = downloadData.download_token;
      setDownloadToken(token);
      
      if (onDownloadStart) {
        onDownloadStart(downloadData.download_id);
      }
      
      // Start progress tracking
      const interval = setInterval(() => {
        trackDownloadProgress(token);
      }, 1000);
      
      setProgressInterval(interval);
      
      // Start actual download
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      window.location.href = `${API_BASE_URL}/api/datasets/download/${token}`;
      
    } catch (err: any) {
      console.error('Download error:', err);
      
      // Handle structured error responses
      let errorMessage = 'Failed to start download';
      if (err.response?.data?.detail) {
        const errorDetail = err.response.data.detail;
        errorMessage = errorDetail.message || errorDetail;
        
        // Show recovery suggestions if available
        if (errorDetail.recovery_suggestions && errorDetail.recovery_suggestions.length > 0) {
          errorMessage += ': ' + errorDetail.recovery_suggestions[0];
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
      setIsDownloading(false);
      
      if (onError) {
        onError(err);
      }
    }
  };

  // Track download progress
  const trackDownloadProgress = async (token: string) => {
    try {
      const progressData = await datasetsAPI.getDownloadProgress(token);
      setDownloadProgress(progressData);
      
      // Check if download is complete or failed
      if (['completed', 'failed', 'expired'].includes(progressData.status)) {
        if (progressInterval) {
          clearInterval(progressInterval);
          setProgressInterval(null);
        }
        
        if (progressData.status === 'completed') {
          if (onDownloadComplete) {
            onDownloadComplete();
          }
        } else if (progressData.status === 'failed') {
          setError(progressData.error_message || 'Download failed');
          if (onError) {
            onError(progressData.error_message);
          }
        }
      }
      
    } catch (err) {
      console.error('Error tracking download progress:', err);
    }
  };

  // Retry download
  const retryDownload = async () => {
    if (!downloadToken) return;
    
    try {
      setError(null);
      
      // Use the API client to retry download
      const retryData = await datasetsAPI.retryDownload(downloadToken);
      
      if (retryData.can_retry) {
        // Restart progress tracking
        const interval = setInterval(() => {
          trackDownloadProgress(downloadToken);
        }, 1000);
        
        setProgressInterval(interval);
        
        // Start actual download
        window.location.href = `/api/datasets/download/${downloadToken}`;
      } else {
        throw new Error('Download cannot be retried');
      }
      
    } catch (err: any) {
      console.error('Retry error:', err);
      
      // Handle structured error responses
      let errorMessage = 'Failed to retry download';
      if (err.response?.data?.detail) {
        const errorDetail = err.response.data.detail;
        errorMessage = errorDetail.message || errorDetail;
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
      
      if (onError) {
        onError(err);
      }
    }
  };

  // Cancel download
  const cancelDownload = () => {
    if (progressInterval) {
      clearInterval(progressInterval);
      setProgressInterval(null);
    }
    
    setIsDownloading(false);
    setDownloadToken('');
    setDownloadProgress(null);
  };

  // Determine available formats based on dataset type
  const getAvailableFormats = () => {
    const formats = [{ value: 'original', label: 'Original Format' }];
    
    // Add format options based on dataset type
    if (dataset.type?.toLowerCase() === 'csv') {
      formats.push(
        { value: 'csv', label: 'CSV' },
        { value: 'json', label: 'JSON' },
        { value: 'excel', label: 'Excel' }
      );
    } else if (dataset.type?.toLowerCase() === 'json') {
      formats.push(
        { value: 'json', label: 'JSON' },
        { value: 'csv', label: 'CSV' }
      );
    } else if (dataset.type?.toLowerCase() === 'excel' || dataset.type?.toLowerCase() === 'xlsx') {
      formats.push(
        { value: 'excel', label: 'Excel' },
        { value: 'csv', label: 'CSV' }
      );
    } else if (dataset.type?.toLowerCase() === 'pdf') {
      formats.push(
        { value: 'pdf', label: 'PDF' },
        { value: 'txt', label: 'Text (Extracted)' },
        { value: 'json', label: 'JSON (Structured)' }
      );
    }
    
    return formats;
  };

  // Render download options
  const renderDownloadOptions = () => {
    return (
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Download Format
          </label>
          <select
            value={selectedFormat}
            onChange={(e) => setSelectedFormat(e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            disabled={isDownloading}
          >
            {getAvailableFormats().map((format) => (
              <option key={format.value} value={format.value}>
                {format.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Compression
          </label>
          <select
            value={compression}
            onChange={(e) => setCompression(e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            disabled={isDownloading}
          >
            <option value="none">None</option>
            <option value="zip">ZIP</option>
            <option value="gzip">GZIP</option>
          </select>
        </div>

        <div className="pt-2">
          <button
            onClick={startDownload}
            disabled={isDownloading}
            className="w-full flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300"
          >
            <Download className="w-4 h-4 mr-2" />
            {isDownloading ? 'Preparing Download...' : 'Download Dataset'}
          </button>
        </div>

        {dataset.size_bytes && (
          <div className="text-xs text-gray-500 text-center">
            File size: {formatFileSize(dataset.size_bytes)}
          </div>
        )}
      </div>
    );
  };

  // Render download progress
  const renderDownloadProgress = () => {
    if (!downloadProgress) {
      return (
        <div className="flex items-center justify-center py-6">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-sm text-gray-600">Initializing download...</span>
        </div>
      );
    }

    const progress = downloadProgress.progress_percentage || 0;
    
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium">
            {downloadProgress.status === 'completed' ? 'Download Complete' : 
             downloadProgress.status === 'failed' ? 'Download Failed' :
             downloadProgress.status === 'interrupted' ? 'Download Interrupted' :
             'Downloading...'}
          </span>
          <span className="font-medium">{progress}%</span>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div 
            className={`h-2.5 rounded-full ${
              downloadProgress.status === 'failed' ? 'bg-red-500' :
              downloadProgress.status === 'completed' ? 'bg-green-500' : 'bg-blue-500'
            }`} 
            style={{ width: `${progress}%` }}
          ></div>
        </div>
        
        <div className="grid grid-cols-2 gap-2 text-xs text-gray-500">
          {downloadProgress.bytes_transferred !== undefined && downloadProgress.file_size_bytes && (
            <div>
              <span className="block font-medium">Transferred</span>
              <span>{formatFileSize(downloadProgress.bytes_transferred)} of {formatFileSize(downloadProgress.file_size_bytes)}</span>
            </div>
          )}
          
          {downloadProgress.transfer_rate_mbps && (
            <div>
              <span className="block font-medium">Speed</span>
              <span>{downloadProgress.transfer_rate_mbps} Mbps</span>
            </div>
          )}
          
          {downloadProgress.estimated_time_remaining_seconds !== undefined && downloadProgress.status === 'in_progress' && (
            <div className="col-span-2">
              <span className="block font-medium">Estimated time remaining</span>
              <span>{formatTimeRemaining(downloadProgress.estimated_time_remaining_seconds)}</span>
            </div>
          )}
        </div>
        
        {/* Error message */}
        {(downloadProgress.status === 'failed' || error) && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3 mt-3">
            <div className="flex">
              <AlertCircle className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Download failed</h3>
                <div className="mt-1 text-xs text-red-700">
                  {downloadProgress.error_message || error || 'An error occurred during download'}
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Interrupted download */}
        {downloadProgress.status === 'interrupted' && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 mt-3">
            <div className="flex">
              <Clock className="h-5 w-5 text-yellow-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">Download interrupted</h3>
                <div className="mt-1 text-xs text-yellow-700">
                  Your download was interrupted. You can resume from where you left off.
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Completed download */}
        {downloadProgress.status === 'completed' && (
          <div className="bg-green-50 border border-green-200 rounded-md p-3 mt-3">
            <div className="flex">
              <CheckCircle className="h-5 w-5 text-green-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800">Download complete</h3>
                <div className="mt-1 text-xs text-green-700">
                  Your file has been downloaded successfully.
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Action buttons */}
        <div className="flex space-x-3 pt-2">
          {downloadProgress.status === 'completed' && (
            <button
              onClick={cancelDownload}
              className="flex-1 flex items-center justify-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              Download Another Format
            </button>
          )}
          
          {downloadProgress.status === 'failed' && (
            <button
              onClick={startDownload}
              className="flex-1 flex items-center justify-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
            </button>
          )}
          
          {downloadProgress.status === 'interrupted' && downloadProgress.is_resumable && (
            <button
              onClick={retryDownload}
              className="flex-1 flex items-center justify-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              Resume Download
            </button>
          )}
          
          {['in_progress', 'interrupted', 'failed'].includes(downloadProgress.status) && (
            <button
              onClick={cancelDownload}
              className="flex-1 flex items-center justify-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              Cancel
            </button>
          )}
        </div>
      </div>
    );
  };

  // Format icon based on file type
  const getFormatIcon = () => {
    const type = dataset.type?.toLowerCase() || 'unknown';
    
    switch (type) {
      case 'csv':
        return <FileSpreadsheet className="w-8 h-8 text-green-500" />;
      case 'json':
        return <FileJson className="w-8 h-8 text-yellow-500" />;
      case 'excel':
      case 'xlsx':
      case 'xls':
        return <FileSpreadsheet className="w-8 h-8 text-blue-500" />;
      default:
        return <FileType className="w-8 h-8 text-gray-500" />;
    }
  };

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Download Dataset</h3>
      </div>
      
      <div className="p-4">
        <div className="flex items-center mb-4">
          {getFormatIcon()}
          <div className="ml-3">
            <h4 className="text-sm font-medium text-gray-900">{dataset.name}</h4>
            <p className="text-xs text-gray-500">
              {dataset.type?.toUpperCase() || 'Unknown'} • {formatFileSize(dataset.size_bytes)}
            </p>
          </div>
        </div>
        
        {isDownloading ? renderDownloadProgress() : renderDownloadOptions()}
      </div>
    </div>
  );
};

export default DownloadComponent;