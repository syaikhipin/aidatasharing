"""
Frontend Dataset Detail Page Enhancement Example
This shows how the enhanced preview functionality integrates with the frontend
"""

import React, { useState, useEffect } from 'react';

// Example of enhanced preview data structure from API
const EXAMPLE_PREVIEW_RESPONSES = {
  csv_tabular: {
    dataset_id: 25,
    dataset_name: "Employee Data CSV",
    preview: {
      type: "tabular",
      format: "csv",
      headers: ["employee_id", "name", "department", "salary", "hire_date", "performance_score"],
      rows: [
        {"employee_id": 1001, "name": "Alice Johnson", "department": "Engineering", "salary": 85000, "hire_date": "2022-01-15", "performance_score": 4.8},
        {"employee_id": 1002, "name": "Bob Smith", "department": "Marketing", "salary": 65000, "hire_date": "2021-03-20", "performance_score": 4.2},
        {"employee_id": 1003, "name": "Carol Brown", "department": "Sales", "salary": 70000, "hire_date": "2020-07-10", "performance_score": 4.6}
      ],
      total_rows_in_preview: 3,
      estimated_total_rows: 10,
      column_types: {
        "employee_id": "int64",
        "name": "object", 
        "department": "object",
        "salary": "int64",
        "hire_date": "object",
        "performance_score": "float64"
      },
      basic_stats: {
        row_count: 10,
        column_count: 6,
        numeric_columns: ["employee_id", "salary", "performance_score"],
        text_columns: ["name", "department", "hire_date"]
      },
      file_size_bytes: 1248,
      generated_at: "2025-08-15T11:27:16.244924",
      source: "file_analysis"
    },
    request_params: {
      rows_requested: 20,
      include_stats: true
    }
  },

  json_structured: {
    dataset_id: 26,
    dataset_name: "Company Structure JSON",
    preview: {
      type: "json",
      format: "json",
      items: [
        {
          "company": "TechCorp Solutions",
          "departments": [
            {"id": 1, "name": "Engineering", "budget": 2500000},
            {"id": 2, "name": "Marketing", "budget": 800000}
          ]
        }
      ],
      total_items: 1,
      common_fields: ["company", "departments", "metrics"],
      structure_analysis: {
        "company": "string",
        "departments": "array",
        "metrics": "object"
      },
      file_size_bytes: 1859,
      generated_at: "2025-08-15T11:30:00.000000",
      source: "json_parser"
    },
    request_params: {
      rows_requested: 20,
      include_stats: true
    }
  },

  excel_workbook: {
    dataset_id: 27,
    dataset_name: "Financial Report Excel",
    preview: {
      type: "excel",
      format: "xlsx",
      sheet_count: 3,
      sheets: {
        "Q1_Summary": {
          headers: ["Month", "Revenue", "Expenses", "Profit"],
          rows: [
            {"Month": "January", "Revenue": 150000, "Expenses": 120000, "Profit": 30000},
            {"Month": "February", "Revenue": 165000, "Expenses": 125000, "Profit": 40000},
            {"Month": "March", "Revenue": 180000, "Expenses": 130000, "Profit": 50000}
          ],
          row_count: 3,
          column_count: 4
        },
        "Detailed_Breakdown": {
          headers: ["Date", "Category", "Amount", "Description"],
          rows: [
            {"Date": "2024-01-01", "Category": "Sales", "Amount": 50000, "Description": "Product Sales"},
            {"Date": "2024-01-02", "Category": "Marketing", "Amount": -15000, "Description": "Ad Campaign"}
          ],
          row_count: 45,
          column_count: 4
        }
      },
      file_size_bytes: 24576,
      generated_at: "2025-08-15T11:35:00.000000",
      source: "excel_parser"
    },
    request_params: {
      rows_requested: 20,
      include_stats: true
    }
  }
};

// Enhanced Preview Component for React Frontend
const EnhancedDatasetPreview = ({ previewData, isLoading }) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading preview...</span>
      </div>
    );
  }

  if (!previewData || !previewData.preview) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">Preview not available</p>
      </div>
    );
  }

  const { preview } = previewData;

  return (
    <div className="space-y-6">
      {/* Preview Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">Dataset Preview</h3>
        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            {preview.format?.toUpperCase() || 'Unknown'}
          </span>
          <span className="text-xs text-gray-500">
            {preview.source || 'Unknown source'}
          </span>
        </div>
      </div>

      {/* CSV/Tabular Preview */}
      {preview.type === 'tabular' && (
        <TabularPreview preview={preview} />
      )}

      {/* JSON Preview */}
      {preview.type === 'json' && (
        <JsonPreview preview={preview} />
      )}

      {/* Excel Preview */}
      {preview.type === 'excel' && (
        <ExcelPreview preview={preview} />
      )}

      {/* File Statistics */}
      {(preview.basic_stats || preview.file_size_bytes) && (
        <FileStatistics preview={preview} />
      )}
    </div>
  );
};

// Tabular data preview component
const TabularPreview = ({ preview }) => (
  <div>
    <h4 className="text-md font-medium text-gray-900 mb-3 flex items-center">
      📊 Data Preview ({preview.total_rows_in_preview} of {preview.estimated_total_rows} rows)
    </h4>
    
    <div className="bg-gray-50 rounded-md border overflow-hidden">
      <div className="overflow-x-auto max-h-64">
        <table className="w-full text-xs">
          <thead className="bg-gray-100">
            <tr>
              {preview.headers?.map((header) => (
                <th key={header} className="px-3 py-2 text-left font-medium text-gray-900 border-b">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {preview.rows?.slice(0, 10).map((row, index) => (
              <tr key={index} className="border-b border-gray-200 hover:bg-gray-50">
                {preview.headers?.map((header) => (
                  <td key={header} className="px-3 py-2 text-gray-700 truncate max-w-32">
                    {String(row[header] || '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>

    {/* Column Types */}
    {preview.column_types && (
      <div className="mt-3">
        <h5 className="text-sm font-medium text-gray-900 mb-2">Column Types</h5>
        <div className="flex flex-wrap gap-2">
          {Object.entries(preview.column_types).map(([col, type]) => (
            <span key={col} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              {col}: {type}
            </span>
          ))}
        </div>
      </div>
    )}
  </div>
);

// JSON preview component
const JsonPreview = ({ preview }) => (
  <div>
    <h4 className="text-md font-medium text-gray-900 mb-3 flex items-center">
      📄 JSON Data Preview
    </h4>
    
    {preview.items && (
      <div className="bg-gray-50 rounded-md p-4 max-h-64 overflow-y-auto">
        <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
          {JSON.stringify(preview.items.slice(0, 3), null, 2)}
        </pre>
        {preview.items.length > 3 && (
          <p className="text-xs text-gray-500 mt-2">
            ... and {preview.items.length - 3} more items
          </p>
        )}
      </div>
    )}

    {preview.common_fields && (
      <div className="mt-3">
        <h5 className="text-sm font-medium text-gray-900 mb-2">Common Fields</h5>
        <div className="flex flex-wrap gap-2">
          {preview.common_fields.map((field) => (
            <span key={field} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
              {field}
            </span>
          ))}
        </div>
      </div>
    )}
  </div>
);

// Excel preview component
const ExcelPreview = ({ preview }) => (
  <div>
    <h4 className="text-md font-medium text-gray-900 mb-3 flex items-center">
      📈 Excel Preview ({preview.sheet_count} sheets)
    </h4>
    
    {Object.entries(preview.sheets || {}).map(([sheetName, sheetData]) => (
      <div key={sheetName} className="mb-4">
        <h5 className="text-sm font-medium text-gray-900 mb-2">Sheet: {sheetName}</h5>
        <div className="bg-gray-50 rounded-md border overflow-hidden">
          <div className="overflow-x-auto max-h-48">
            <table className="w-full text-xs">
              <thead className="bg-gray-100">
                <tr>
                  {sheetData.headers?.map((header) => (
                    <th key={header} className="px-3 py-2 text-left font-medium text-gray-900 border-b">
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sheetData.rows?.slice(0, 5).map((row, index) => (
                  <tr key={index} className="border-b border-gray-200 hover:bg-gray-50">
                    {sheetData.headers?.map((header) => (
                      <td key={header} className="px-3 py-2 text-gray-700 truncate max-w-32">
                        {String(row[header] || '')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          {sheetData.row_count} rows × {sheetData.column_count} columns
        </p>
      </div>
    ))}
  </div>
);

// File statistics component
const FileStatistics = ({ preview }) => (
  <div>
    <h4 className="text-md font-medium text-gray-900 mb-3">Statistics</h4>
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {preview.basic_stats?.row_count && (
        <div className="bg-blue-50 rounded-md p-3">
          <span className="text-sm font-medium text-blue-700">Rows</span>
          <p className="text-sm text-blue-900 mt-1">{preview.basic_stats.row_count.toLocaleString()}</p>
        </div>
      )}
      {preview.basic_stats?.column_count && (
        <div className="bg-blue-50 rounded-md p-3">
          <span className="text-sm font-medium text-blue-700">Columns</span>
          <p className="text-sm text-blue-900 mt-1">{preview.basic_stats.column_count}</p>
        </div>
      )}
      {preview.file_size_bytes && (
        <div className="bg-blue-50 rounded-md p-3">
          <span className="text-sm font-medium text-blue-700">File Size</span>
          <p className="text-sm text-blue-900 mt-1">{formatFileSize(preview.file_size_bytes)}</p>
        </div>
      )}
      {preview.format && (
        <div className="bg-blue-50 rounded-md p-3">
          <span className="text-sm font-medium text-blue-700">Format</span>
          <p className="text-sm text-blue-900 mt-1">{preview.format.toUpperCase()}</p>
        </div>
      )}
    </div>
  </div>
);

// Utility function for file size formatting
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Download functionality integration
const DownloadButton = ({ datasetId, datasetName }) => {
  const [isDownloading, setIsDownloading] = useState(false);
  
  const handleDownload = async (format = 'original') => {
    try {
      setIsDownloading(true);
      
      // Call the enhanced download API
      const response = await fetch(`/api/datasets/${datasetId}/download`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({ format })
      });
      
      if (response.ok) {
        const downloadInfo = await response.json();
        
        if (downloadInfo.download_url) {
          // Direct download
          window.open(downloadInfo.download_url, '_blank');
        } else if (downloadInfo.download_token) {
          // Polling for download completion
          alert('Download initiated. Please wait...');
        }
      } else {
        throw new Error('Download failed');
      }
    } catch (error) {
      console.error('Download error:', error);
      alert('Failed to download dataset');
    } finally {
      setIsDownloading(false);
    }
  };
  
  return (
    <div className="flex space-x-2">
      <button
        onClick={() => handleDownload('csv')}
        disabled={isDownloading}
        className="flex items-center px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-md disabled:opacity-50"
      >
        {isDownloading ? '⏳' : '📥'} CSV
      </button>
      <button
        onClick={() => handleDownload('json')}
        disabled={isDownloading}
        className="flex items-center px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md disabled:opacity-50"
      >
        {isDownloading ? '⏳' : '📥'} JSON
      </button>
      <button
        onClick={() => handleDownload('original')}
        disabled={isDownloading}
        className="flex items-center px-3 py-1.5 bg-gray-600 hover:bg-gray-700 text-white text-sm font-medium rounded-md disabled:opacity-50"
      >
        {isDownloading ? '⏳' : '📥'} Original
      </button>
    </div>
  );
};

export {
  EnhancedDatasetPreview,
  DownloadButton,
  EXAMPLE_PREVIEW_RESPONSES,
  formatFileSize
};