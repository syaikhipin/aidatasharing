'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useAuth } from '@/components/auth/AuthProvider';
import { useState, useCallback } from 'react';
import { datasetsAPI } from '@/lib/api';
import { useRouter } from 'next/navigation';

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
  const { user } = useAuth();
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [previewData, setPreviewData] = useState<any>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    sharing_level: 'private',
    department_id: '',
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
      handleFileSelect(droppedFiles[0]);
    }
  }, []);

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile);
    setFormData(prev => ({
      ...prev,
      name: prev.name || selectedFile.name.replace(/\.[^/.]+$/, '')
    }));
    
    // Generate preview
    generatePreview(selectedFile);
  };

  const generatePreview = async (file: File) => {
    try {
      const extension = file.name.split('.').pop()?.toLowerCase();
      
      let preview = null;
      if (extension === 'pdf') {
        preview = {
          type: 'pdf',
          totalRows: 'N/A (Document)',
          fileSize: file.size,
          structure: 'document'
        };
      } else {
        const text = await file.text();
        
        if (extension === 'csv') {
          const lines = text.split('\n').slice(0, 6); // Header + 5 rows
          const headers = lines[0]?.split(',') || [];
          const rows = lines.slice(1).map(line => line.split(','));
          
          preview = {
            type: 'csv',
            headers,
            rows: rows.filter(row => row.length === headers.length),
            totalRows: text.split('\n').length - 1,
            fileSize: file.size,
            columns: headers.length
          };
        } else if (extension === 'json') {
          const jsonData = JSON.parse(text);
          const isArray = Array.isArray(jsonData);
          const sample = isArray ? jsonData.slice(0, 5) : [jsonData];
          
          preview = {
            type: 'json',
            sample,
            totalRows: isArray ? jsonData.length : 1,
            fileSize: file.size,
            structure: isArray ? 'array' : 'object'
          };
        }
      }
      
      setPreviewData(preview);
    } catch (error) {
      console.error('Failed to generate preview:', error);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    
    try {
      setIsUploading(true);
      setUploadProgress(0);
      
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 200);
      
      await datasetsAPI.uploadDataset(file, {
        name: formData.name,
        description: formData.description,
        sharing_level: formData.sharing_level,
      });
      
      setUploadProgress(100);
      
      setTimeout(() => {
        router.push('/datasets');
      }, 1000);
      
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="py-6">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Upload Dataset</h1>
          <p className="mt-1 text-sm text-gray-600">
            Add a new dataset to your organization for AI model training.
          </p>
        </div>

        <div className="space-y-8">
          {/* File Upload Area */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Select File</h3>
            
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                isDragOver ? 'border-blue-400 bg-blue-50' : 'border-gray-300'
              }`}
            >
              {!file ? (
                <>
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <p className="mt-2 text-sm text-gray-600">
                    <span className="font-medium">Click to upload</span> or drag and drop
                  </p>
                  <p className="text-xs text-gray-500">CSV, JSON, Excel, or PDF files up to 50MB</p>
                  <input
                    type="file"
                    accept=".csv,.json,.xlsx,.xls,.pdf"
                    onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  />
                </>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-center space-x-3">
                    <svg className="h-8 w-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <div>
                      <p className="font-medium text-gray-900">{file.name}</p>
                      <p className="text-sm text-gray-500">{formatFileSize(file.size)}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setFile(null);
                      setPreviewData(null);
                    }}
                    className="text-sm text-red-600 hover:text-red-800"
                  >
                    Remove file
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* File Preview */}
          {previewData && (
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Data Preview</h3>
              
              <div className="mb-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Type:</span>
                  <span className="ml-2 text-gray-900">{previewData.type.toUpperCase()}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Rows:</span>
                  <span className="ml-2 text-gray-900">{previewData.totalRows?.toLocaleString()}</span>
                </div>
                {previewData.columns && (
                  <div>
                    <span className="font-medium text-gray-700">Columns:</span>
                    <span className="ml-2 text-gray-900">{previewData.columns}</span>
                  </div>
                )}
                <div>
                  <span className="font-medium text-gray-700">Size:</span>
                  <span className="ml-2 text-gray-900">{formatFileSize(previewData.fileSize)}</span>
                </div>
              </div>

              {previewData.type === 'csv' && (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        {previewData.headers.map((header: string, index: number) => (
                          <th key={index} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {previewData.rows.slice(0, 5).map((row: string[], index: number) => (
                        <tr key={index}>
                          {row.map((cell: string, cellIndex: number) => (
                            <td key={cellIndex} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {cell}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {previewData.totalRows > 5 && (
                    <p className="mt-2 text-sm text-gray-500">
                      ... and {previewData.totalRows - 5} more rows
                    </p>
                  )}
                </div>
              )}

              {previewData.type === 'pdf' && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center space-x-3">
                    <svg className="h-8 w-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                    </svg>
                    <div>
                      <h4 className="text-sm font-medium text-blue-900">PDF Document</h4>
                      <p className="text-sm text-blue-700">
                        PDF files can be used for document-based AI analysis and chat features.
                        The content will be processed for AI interactions.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Dataset Metadata */}
          {file && (
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Dataset Information</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Dataset Name
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    rows={3}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Describe what this dataset contains..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Sharing Level
                  </label>
                  <select
                    value={formData.sharing_level}
                    onChange={(e) => setFormData({...formData, sharing_level: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="private">Private - Only me</option>
                    <option value="organization">Organization - All members</option>
                    <option value="public">Public - Everyone</option>
                  </select>
                </div>
              </div>

              {/* Upload Progress */}
              {isUploading && (
                <div className="mt-6">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Uploading...</span>
                    <span className="text-sm text-gray-500">{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => router.back()}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpload}
                  disabled={!file || !formData.name || isUploading}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isUploading ? 'Uploading...' : 'Upload Dataset'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}