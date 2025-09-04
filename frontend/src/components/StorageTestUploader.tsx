'use client';

import { useState, useRef } from 'react';
import { Upload, File, CheckCircle, AlertTriangle, RefreshCw, Database, Cloud } from 'lucide-react';

interface UploadResult {
  filename: string;
  size: number;
  storage_backend: string;
  storage_strategy: string;
  storage_locations: string[];
  success: boolean;
  upload_time: number;
}

interface StorageTestUploaderProps {
  className?: string;
}

export default function StorageTestUploader({ className = "" }: StorageTestUploaderProps) {
  const [uploading, setUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState<UploadResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (files: FileList) => {
    setUploading(true);
    setError(null);
    
    const results: UploadResult[] = [];
    
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const startTime = Date.now();
      
      try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('name', file.name);
        formData.append('description', `Storage test upload - ${new Date().toLocaleString()}`);

        const response = await fetch('/api/datasets', {
          method: 'POST',
          body: formData,
          credentials: 'include',
        });

        const uploadTime = Date.now() - startTime;

        if (response.ok) {
          const data = await response.json();
          results.push({
            filename: file.name,
            size: file.size,
            storage_backend: data.storage_info?.backend || 'unknown',
            storage_strategy: data.storage_info?.storage_strategy || 'unknown',
            storage_locations: data.storage_info?.storage_locations || ['unknown'],
            success: true,
            upload_time: uploadTime,
          });
        } else {
          const error = await response.json();
          results.push({
            filename: file.name,
            size: file.size,
            storage_backend: 'failed',
            storage_strategy: 'failed',
            storage_locations: [],
            success: false,
            upload_time: uploadTime,
          });
        }
      } catch (error) {
        results.push({
          filename: file.name,
          size: file.size,
          storage_backend: 'error',
          storage_strategy: 'error',
          storage_locations: [],
          success: false,
          upload_time: Date.now() - startTime,
        });
      }
    }

    setUploadResults(prev => [...results, ...prev]);
    setUploading(false);
    
    // Clear file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStorageIcon = (locations: string[]) => {
    if (locations.includes('s3') && locations.includes('local')) {
      return <div className="flex items-center"><Database className="h-3 w-3 mr-1" /><Cloud className="h-3 w-3" /></div>;
    } else if (locations.includes('s3')) {
      return <Cloud className="h-4 w-4" />;
    } else {
      return <Database className="h-4 w-4" />;
    }
  };

  const getStrategyColor = (strategy: string, success: boolean) => {
    if (!success) return 'text-red-600 bg-red-50';
    
    switch (strategy) {
      case 'local_primary': return 'text-blue-600 bg-blue-50';
      case 's3_primary': return 'text-green-600 bg-green-50';
      case 'hybrid': return 'text-purple-600 bg-purple-50';
      case 'redundant': return 'text-orange-600 bg-orange-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <div className={`bg-white rounded-lg border p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900 flex items-center">
          <Upload className="h-5 w-5 mr-2 text-blue-600" />
          Storage Test Uploader
        </h3>
        <button
          onClick={() => setUploadResults([])}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          Clear Results
        </button>
      </div>

      {/* Upload Area */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors"
      >
        <div className="space-y-4">
          <div className="flex justify-center">
            <Upload className="h-12 w-12 text-gray-400" />
          </div>
          <div>
            <p className="text-lg font-medium text-gray-900">Test Storage Upload</p>
            <p className="text-sm text-gray-600">
              Drag and drop files here, or click to select files
            </p>
          </div>
          <div>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  handleFileUpload(e.target.files);
                }
              }}
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {uploading ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <File className="h-4 w-4 mr-2" />
                  Select Files
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="flex">
            <AlertTriangle className="h-5 w-5 text-red-600 mr-2" />
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Upload Results */}
      {uploadResults.length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Upload Results</h4>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {uploadResults.map((result, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg border ${result.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    {result.success ? (
                      <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    ) : (
                      <AlertTriangle className="h-4 w-4 text-red-600 mr-2" />
                    )}
                    <div>
                      <p className="text-sm font-medium text-gray-900">{result.filename}</p>
                      <p className="text-xs text-gray-600">{formatFileSize(result.size)}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {result.success && (
                      <>
                        <div className={`flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStrategyColor(result.storage_strategy, result.success)}`}>
                          {getStorageIcon(result.storage_locations)}
                          <span className="ml-1">{result.storage_strategy}</span>
                        </div>
                        <span className="text-xs text-gray-500">
                          {result.upload_time}ms
                        </span>
                      </>
                    )}
                  </div>
                </div>
                
                {result.success && result.storage_locations.length > 0 && (
                  <div className="mt-2 text-xs text-gray-600">
                    <span className="font-medium">Stored in:</span> {result.storage_locations.join(', ')}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
        <p className="text-sm text-blue-800">
          <strong>Test Instructions:</strong> Upload different file sizes to test your storage strategy. 
          Files will be stored according to your current configuration in <code>.env</code>
        </p>
      </div>
    </div>
  );
}