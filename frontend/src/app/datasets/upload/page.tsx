'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useState, useCallback } from 'react';
import { datasetsAPI } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { Upload, AlertCircle, X, Database } from 'lucide-react';

export default function UploadDatasetPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <UploadDatasetContent />
      </DashboardLayout>
    </ProtectedRoute>
  );
}

function UploadDatasetContent() {
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isMultiFileMode, setIsMultiFileMode] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    sharing_level: 'private',
  });

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    if (droppedFiles.length > 0) {
      if (isMultiFileMode) {
        handleMultipleFileSelect(droppedFiles);
      } else {
        handleSingleFileSelect(droppedFiles[0]);
      }
    }
  }, [isMultiFileMode]);

  const handleSingleFileSelect = (selectedFile: File) => {
    // Reset error state
    setError(null);
    
    if (!validateFile(selectedFile)) return;
    
    setFiles([selectedFile]);
    setFormData(prev => ({
      ...prev,
      name: prev.name || selectedFile.name.replace(/\.[^/.]+$/, '')
    }));
  };
  
  const handleMultipleFileSelect = (selectedFiles: File[]) => {
    // Reset error state
    setError(null);
    
    // Validate all files
    const validFiles: File[] = [];
    const errors: string[] = [];
    
    for (const file of selectedFiles) {
      if (validateFile(file, false)) {
        validFiles.push(file);
      } else {
        errors.push(`${file.name}: Invalid file`);
      }
    }
    
    if (errors.length > 0) {
      setError(`Some files were rejected: ${errors.join(', ')}`);
    }
    
    if (validFiles.length > 0) {
      setFiles(validFiles);
      setFormData(prev => ({
        ...prev,
        name: prev.name || `Multi-file dataset (${validFiles.length} files)`
      }));
    }
  };
  
  const validateFile = (file: File, showError: boolean = true): boolean => {
    // Check file size (50MB limit per file)
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
      if (showError) setError(`File ${file.name} exceeds 50MB limit`);
      return false;
    }
    
    // Check file type
    const extension = file.name.split('.').pop()?.toLowerCase();
    const supportedTypes = ['csv', 'json', 'xlsx', 'xls', 'pdf', 'txt', 'docx', 'doc', 'rtf', 'odt', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'];
    
    if (!extension || !supportedTypes.includes(extension)) {
      if (showError) setError(`Unsupported file type in ${file.name}. Supported formats: ${supportedTypes.join(', ')}`);
      return false;
    }
    
    return true;
  };
  
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };
  
  const getFileTypeIcon = (filename: string) => {
    const extension = filename.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'csv':
      case 'xlsx':
      case 'xls':
        return '📊';
      case 'json':
        return '📋';
      case 'pdf':
        return '📄';
      case 'txt':
      case 'docx':
        return '📝';
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
      case 'bmp':
      case 'webp':
        return '🖼️';
      default:
        return '📁';
    }
  };
  
  const getFileTypeLabel = (filename: string) => {
    const extension = filename.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'csv':
        return 'CSV Spreadsheet';
      case 'xlsx':
      case 'xls':
        return 'Excel Spreadsheet';
      case 'json':
        return 'JSON Data';
      case 'pdf':
        return 'PDF Document';
      case 'txt':
        return 'Text Document';
      case 'docx':
        return 'Word Document';
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
      case 'bmp':
      case 'webp':
        return 'Image File';
      case 'doc':
      case 'rtf':
      case 'odt':
        return 'Document File';
      default:
        return 'Data File';
    }
  };
  
  const handleUpload = async () => {
    if (files.length === 0 || !formData.name.trim()) {
      setError('Please select file(s) and provide a name');
      return;
    }
    
    try {
      setIsUploading(true);
      setError(null);
      setUploadProgress(0);
      
      const response = files.length === 1 
        ? await datasetsAPI.uploadDataset(files[0], {
            name: formData.name,
            description: formData.description,
            sharing_level: formData.sharing_level
          })
        : await datasetsAPI.uploadMultipleDatasets(files, {
            name: formData.name,
            description: formData.description,
            sharing_level: formData.sharing_level
          });
      
      // Check if response contains validation error objects
      if (response && typeof response === 'object' && ('type' in response || 'loc' in response || 'msg' in response)) {
        console.error('Received validation error as upload response:', response);
        setError('Upload failed due to validation error. Please check your file and try again.');
        return;
      }
      
      // Check if response has the expected structure (dataset nested inside)
      const datasetId = response?.dataset?.id || response?.id;
      if (!response || !datasetId) {
        console.error('Upload response missing dataset ID:', response);
        setError('Upload completed but response was invalid. Please check the datasets page.');
        return;
      }
      
      // Success - redirect to dataset page
      router.push(`/datasets/${datasetId}`);
      
    } catch (error: any) {
      console.error('Upload failed:', error);
      setError(error.response?.data?.detail || error.message || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };
  
  const clearFiles = () => {
    setFiles([]);
    setError(null);
    setUploadProgress(0);
  };
  
  const removeFile = (index: number) => {
    const updatedFiles = files.filter((_, i) => i !== index);
    setFiles(updatedFiles);
    
    if (updatedFiles.length === 0) {
      setFormData(prev => ({ ...prev, name: '' }));
    } else if (updatedFiles.length === 1) {
      setFormData(prev => ({
        ...prev,
        name: prev.name.includes('Multi-file') ? updatedFiles[0].name.replace(/\.[^/.]+$/, '') : prev.name
      }));
    }
  };

  return (
    <div className="py-6">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <Upload className="h-6 w-6 mr-2 text-blue-600" />
            Upload Dataset
          </h1>
          <p className="text-gray-600 mt-1">
            Upload your data files and make them available for AI analysis and sharing
          </p>
        </div>

        <div className="bg-white shadow rounded-lg">
          <div className="p-6">
            {/* Upload Mode Toggle */}
            <div className="mb-6 flex items-center justify-center space-x-4">
              <button
                type="button"
                onClick={() => { setIsMultiFileMode(false); clearFiles(); }}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  !isMultiFileMode 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                📁 Single File
              </button>
              <button
                type="button"
                onClick={() => { setIsMultiFileMode(true); clearFiles(); }}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  isMultiFileMode 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                📁 Multiple Files
              </button>
            </div>

            {/* File Upload Area */}
            {files.length === 0 ? (
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  isDragOver 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-300 hover:border-gray-400'
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {isMultiFileMode ? 'Drag and drop your files here' : 'Drag and drop your file here'}
                </h3>
                <p className="text-gray-600 mb-4">
                  {isMultiFileMode 
                    ? 'or click to browse and select multiple files'
                    : 'or click to browse and select a file'
                  }
                </p>
                <input
                  type="file"
                  onChange={(e) => {
                    const selectedFiles = Array.from(e.target.files || []);
                    if (selectedFiles.length > 0) {
                      if (isMultiFileMode) {
                        handleMultipleFileSelect(selectedFiles);
                      } else {
                        handleSingleFileSelect(selectedFiles[0]);
                      }
                    }
                  }}
                  className="hidden"
                  id="file-upload"
                  accept=".csv,.json,.xlsx,.xls,.pdf,.txt,.docx,.doc,.rtf,.odt,.jpg,.jpeg,.png,.gif,.bmp,.webp"
                  multiple={isMultiFileMode}
                />
                <label
                  htmlFor="file-upload"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 cursor-pointer"
                >
                  Select File
                </label>
                <p className="text-xs text-gray-500 mt-4">
                  Supported formats: CSV, JSON, Excel, PDF, Text, Word, Images, and more<br/>
                  {isMultiFileMode ? 'Each file max 50MB • Multiple files will be grouped as one dataset' : 'Max file size: 50MB'}
                </p>
              </div>
            ) : (
              /* Files Selected */
              <div className="space-y-6">
                {/* Files Info */}
                <div className="space-y-3">
                  {files.map((file, index) => (
                    <div key={`${file.name}-${index}`} className="flex items-start justify-between p-4 border border-gray-200 rounded-lg bg-gray-50">
                      <div className="flex items-start space-x-3">
                        <div className="text-2xl">
                          {getFileTypeIcon(file.name)}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <h3 className="text-sm font-medium text-gray-900">{file.name}</h3>
                            {index === 0 && files.length > 1 && (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                Primary
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-600">{getFileTypeLabel(file.name)}</p>
                          <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                        </div>
                      </div>
                      <button
                        onClick={() => removeFile(index)}
                        className="text-gray-400 hover:text-gray-600"
                        disabled={isUploading}
                        title={`Remove ${file.name}`}
                      >
                        <X className="h-5 w-5" />
                      </button>
                    </div>
                  ))}
                  
                  {/* Multi-file Summary */}
                  {files.length > 1 && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                      <div className="flex items-center space-x-2 text-sm text-blue-800">
                        <span className="font-medium">📊 Dataset Summary:</span>
                        <span>{files.length} files</span>
                        <span>•</span>
                        <span>{formatFileSize(files.reduce((total, file) => total + file.size, 0))}</span>
                      </div>
                      <p className="text-xs text-blue-600 mt-1">
                        The first file will be used as the primary file for previews and AI analysis
                      </p>
                    </div>
                  )}
                </div>

                {/* Form Fields */}
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Dataset Name *
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Enter a name for your dataset"
                      disabled={isUploading}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Description
                    </label>
                    <textarea
                      value={formData.description}
                      onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                      rows={3}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Describe your dataset (optional)"
                      disabled={isUploading}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Sharing Level
                    </label>
                    <select
                      value={formData.sharing_level}
                      onChange={(e) => setFormData(prev => ({ ...prev, sharing_level: e.target.value }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      disabled={isUploading}
                    >
                      <option value="private">Private (Only you)</option>
                      <option value="organization">Organization (Your team)</option>
                      <option value="public">Public (Anyone with link)</option>
                    </select>
                  </div>
                </div>

                {/* Error Display */}
                {error && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                    <div className="flex">
                      <AlertCircle className="h-5 w-5 text-red-400 mr-2 flex-shrink-0" />
                      <p className="text-sm text-red-800">{error}</p>
                    </div>
                  </div>
                )}

                {/* Upload Progress */}
                {isUploading && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Uploading...</span>
                      <span className="text-gray-600">{uploadProgress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex justify-between pt-4">
                  <button
                    onClick={clearFiles}
                    disabled={isUploading}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
                  >
                    {files.length > 1 ? 'Clear All Files' : 'Choose Different File'}
                  </button>
                  <button
                    onClick={handleUpload}
                    disabled={isUploading || !formData.name.trim()}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                  >
                    {isUploading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                        Uploading...
                      </>
                    ) : (
                      <>
                        <Upload className="h-4 w-4 mr-2" />
                        Upload {files.length > 1 ? `${files.length} Files` : 'Dataset'}
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
        
        {/* Help Section */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-blue-900 mb-3 flex items-center">
            <Database className="h-5 w-5 mr-2" />
            What happens after upload?
          </h3>
          <div className="grid md:grid-cols-3 gap-4 text-sm text-blue-800">
            <div>
              <div className="font-medium mb-1">1. Processing</div>
              <p>Your file is automatically analyzed and processed for optimal AI performance</p>
            </div>
            <div>
              <div className="font-medium mb-1">2. Preview Generation</div>
              <p>We create rich previews and metadata to help you understand your data</p>
            </div>
            <div>
              <div className="font-medium mb-1">3. AI-Ready</div>
              <p>Your dataset becomes immediately available for chat, analysis, and sharing</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}