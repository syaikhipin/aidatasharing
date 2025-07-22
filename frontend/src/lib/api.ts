import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle auth errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (email: string, password: string) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await apiClient.post('/api/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },
  
  register: async (userData: {
    email: string;
    password: string;
    full_name: string;
    organization_id?: number;
    create_organization?: boolean;
    organization_name?: string;
  }) => {
    const response = await apiClient.post('/api/auth/register', userData);
    return response.data;
  },
  
  getMe: async () => {
    const response = await apiClient.get('/api/auth/me');
    return response.data;
  },
};

// Admin API
export const adminAPI = {
  getConfigurations: async () => {
    const response = await apiClient.get('/api/admin/config');
    return response.data;
  },
  
  createConfiguration: async (config: { key: string; value?: string; description?: string }) => {
    const response = await apiClient.post('/api/admin/config', config);
    return response.data;
  },
  
  updateConfiguration: async (key: string, config: { value?: string; description?: string }) => {
    const response = await apiClient.put(`/api/admin/config/${key}`, config);
    return response.data;
  },
  
  deleteConfiguration: async (key: string) => {
    const response = await apiClient.delete(`/api/admin/config/${key}`);
    return response.data;
  },
  
  setGoogleApiKey: async (apiKey: string) => {
    const response = await apiClient.post('/api/admin/google-api-key', {
      api_key: apiKey,
    });
    return response.data;
  },
  
  getGoogleApiKeyStatus: async () => {
    const response = await apiClient.get('/api/admin/google-api-key');
    return response.data;
  },
};

// Organizations API
export const organizationsAPI = {
  getOptions: async () => {
    const response = await apiClient.get('/api/organizations/options');
    return response.data;
  },
  
  create: async (orgData: {
    name: string;
    description?: string;
    type?: string;
    website?: string;
    contact_email?: string;
  }) => {
    const response = await apiClient.post('/api/organizations', orgData);
    return response.data;
  },
  
  getMy: async () => {
    const response = await apiClient.get('/api/organizations/my');
    return response.data;
  },
  
  getMembers: async (organizationId: number) => {
    const response = await apiClient.get(`/api/organizations/${organizationId}/members`);
    return response.data;
  },
  
  getDepartments: async (organizationId: number) => {
    const response = await apiClient.get(`/api/organizations/${organizationId}/departments`);
    return response.data;
  },
  
  createDepartment: async (organizationId: number, deptData: {
    name: string;
    description?: string;
  }) => {
    const response = await apiClient.post(`/api/organizations/${organizationId}/departments`, {
      ...deptData,
      organization_id: organizationId
    });
    return response.data;
  },
};

// Datasets API
export const datasetsAPI = {
  getDatasets: async (params?: {
    skip?: number;
    limit?: number;
    sharing_level?: string;
    dataset_type?: string;
  }) => {
    const response = await apiClient.get('/api/datasets', { params });
    return response.data;
  },
  
  createDataset: async (datasetData: {
    name: string;
    description?: string;
    type: string;
    sharing_level?: string;
    department_id?: number;
    source_url?: string;
    connection_params?: Record<string, any>;
    schema_info?: Record<string, any>;
    allow_download?: boolean;
    allow_api_access?: boolean;
  }) => {
    const response = await apiClient.post('/api/datasets', datasetData);
    return response.data;
  },
  
  getDataset: async (datasetId: number) => {
    const response = await apiClient.get(`/api/datasets/${datasetId}`);
    return response.data;
  },
  
  updateDataset: async (datasetId: number, updateData: {
    name?: string;
    description?: string;
    sharing_level?: string;
    department_id?: number;
    allow_download?: boolean;
    allow_api_access?: boolean;
    schema_info?: Record<string, any>;
  }) => {
    const response = await apiClient.put(`/api/datasets/${datasetId}`, updateData);
    return response.data;
  },
  
  deleteDataset: async (datasetId: number) => {
    const response = await apiClient.delete(`/api/datasets/${datasetId}`);
    return response.data;
  },
  
  uploadFile: async (file: File, metadata: {
    name: string;
    description?: string;
    sharing_level?: string;
    department_id?: number;
  }) => {
    const formData = new FormData();
    formData.append('file', file);
    Object.entries(metadata).forEach(([key, value]) => {
      if (value !== undefined) {
        formData.append(key, value.toString());
      }
    });

    const response = await apiClient.post('/api/datasets/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Alias for uploadFile to match frontend expectations
  uploadDataset: async (file: File, metadata: {
    name: string;
    description?: string;
    sharing_level?: string;
    department_id?: number;
  }) => {
    const formData = new FormData();
    formData.append('file', file);
    Object.entries(metadata).forEach(([key, value]) => {
      if (value !== undefined) {
        formData.append(key, value.toString());
      }
    });

    const response = await apiClient.post('/api/datasets/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  chatWithDataset: async (datasetId: number, message: string) => {
    const response = await apiClient.post(`/api/datasets/${datasetId}/chat`, {
      message
    });
    return response.data;
  },

  getDatasetModels: async (datasetId: number) => {
    const response = await apiClient.get(`/api/datasets/${datasetId}/models`);
    return response.data;
  },

  recreateDatasetModels: async (datasetId: number) => {
    const response = await apiClient.post(`/api/datasets/${datasetId}/recreate-models`);
    return response.data;
  },

  // Download functionality
  initiateDownload: async (datasetId: number, fileFormat: string = 'original', compression?: string) => {
    const params: any = { file_format: fileFormat };
    if (compression) {
      params.compression = compression;
    }
    const response = await apiClient.get(`/api/datasets/${datasetId}/download`, { params });
    return response.data;
  },

  getDownloadProgress: async (downloadToken: string) => {
    const response = await apiClient.get(`/api/datasets/download/${downloadToken}/progress`);
    return response.data;
  },

  retryDownload: async (downloadToken: string) => {
    const response = await apiClient.post(`/api/datasets/download/${downloadToken}/retry`);
    return response.data;
  },

  // Ownership transfer functionality
  transferOwnership: async (datasetId: number, newOwnerId: number) => {
    const response = await apiClient.post(`/api/datasets/${datasetId}/transfer-ownership`, {
      new_owner_id: newOwnerId
    });
    return response.data;
  },

  getDatasetStats: async (datasetId: number, includeDownloads: boolean = true, includeAccessLogs: boolean = false) => {
    const params = {
      include_downloads: includeDownloads,
      include_access_logs: includeAccessLogs
    };
    const response = await apiClient.get(`/api/datasets/${datasetId}/stats`, { params });
    return response.data;
  },
};

// Data Sharing API
export const dataSharingAPI = {
  createShareLink: async (data: {
    dataset_id: number;
    expires_in_hours?: number;
    password?: string;
    enable_chat?: boolean;
  }) => {
    const response = await apiClient.post('/api/data-sharing/create-share-link', data);
    return response.data;
  },

  getSharedDataset: async (shareToken: string, password?: string) => {
    const params = password ? { password } : {};
    const response = await apiClient.get(`/api/data-sharing/shared/${shareToken}`, { params });
    return response.data;
  },

  accessSharedDatasetWithPassword: async (shareToken: string, password: string) => {
    const response = await apiClient.post(`/api/data-sharing/shared/${shareToken}/access`, {
      password
    });
    return response.data;
  },

  getMySharedDatasets: async () => {
    const response = await apiClient.get('/api/data-sharing/my-shared-datasets');
    return response.data;
  },

  disableSharing: async (datasetId: number) => {
    const response = await apiClient.delete(`/api/data-sharing/shared/${datasetId}/disable`);
    return response.data;
  },

  getDatasetAnalytics: async (datasetId: number) => {
    const response = await apiClient.get(`/api/data-sharing/analytics/${datasetId}`);
    return response.data;
  },

  // Public endpoints (no auth required)
  getSharedDatasetInfo: async (shareToken: string) => {
    const response = await apiClient.get(`/api/data-sharing/public/shared/${shareToken}/info`);
    return response.data;
  },

  getPublicSharedDataset: async (shareToken: string, password?: string) => {
    const params = password ? { password } : {};
    const response = await apiClient.get(`/api/data-sharing/public/shared/${shareToken}`, { params });
    return response.data;
  },

  accessPublicSharedDatasetWithPassword: async (shareToken: string, password: string) => {
    const response = await apiClient.get(`/api/data-sharing/public/shared/${shareToken}`, {
      params: { password }
    });
    return response.data;
  },
};

// Chat API
export const chatAPI = {
  createChatSession: async (shareToken: string) => {
    const response = await apiClient.post('/api/data-sharing/chat/create-session', {
      share_token: shareToken
    });
    return response.data;
  },

  sendMessage: async (sessionToken: string, message: string) => {
    const response = await apiClient.post('/api/data-sharing/chat/message', {
      session_token: sessionToken,
      message
    });
    return response.data;
  },

  getChatHistory: async (sessionToken: string) => {
    const response = await apiClient.get(`/api/data-sharing/chat/${sessionToken}/history`);
    return response.data;
  },

  endChatSession: async (sessionToken: string) => {
    const response = await apiClient.delete(`/api/data-sharing/chat/${sessionToken}`);
    return response.data;
  },
};

// MindsDB API
export const mindsdbAPI = {
  getStatus: async () => {
    const response = await apiClient.get('/api/mindsdb/status');
    return response.data;
  },
  
  getModels: async () => {
    const response = await apiClient.get('/api/mindsdb/models');
    return response.data;
  },
  
  createModel: async (modelData: { name: string; query: string; engine?: string }) => {
    const response = await apiClient.post('/api/mindsdb/models', modelData);
    return response.data;
  },
  
  getModelInfo: async (modelName: string) => {
    const response = await apiClient.get(`/api/mindsdb/models/${modelName}`);
    return response.data;
  },
  
  predict: async (modelName: string, data: Record<string, any>) => {
    const response = await apiClient.post(`/api/mindsdb/models/${modelName}/predict`, data);
    return response.data;
  },
  
  deleteModel: async (modelName: string) => {
    const response = await apiClient.delete(`/api/mindsdb/models/${modelName}`);
    return response.data;
  },
  
  getDatabases: async () => {
    const response = await apiClient.get('/api/mindsdb/databases');
    return response.data;
  },
  
  createDatabase: async (dbData: { name: string; engine: string; parameters: Record<string, any> }) => {
    const response = await apiClient.post('/api/mindsdb/databases', dbData);
    return response.data;
  },
  
  executeSQL: async (query: string) => {
    const response = await apiClient.post('/api/mindsdb/sql', { query });
    return response.data;
  },

  // Gemini Flash 2 Integration
  initializeGemini: async () => {
    const response = await apiClient.post('/api/mindsdb/gemini/initialize');
    return response.data;
  },

  geminiChat: async (prompt: string) => {
    const response = await apiClient.post('/api/mindsdb/gemini/chat', { prompt });
    return response.data;
  },

  naturalLanguageToSQL: async (query: string, context?: string) => {
    const response = await apiClient.post('/api/mindsdb/gemini/nl-to-sql', { query, context });
    return response.data;
  },

  createGeminiModel: async (modelData: {
    name: string;
    model_type?: string;
    prompt_template?: string;
    mode?: string;
  }) => {
    const response = await apiClient.post('/api/mindsdb/gemini/models', modelData);
    return response.data;
  },

  queryGeminiModel: async (modelName: string, inputData: Record<string, any>) => {
    const response = await apiClient.post(`/api/mindsdb/gemini/models/${modelName}/query`, { input_data: inputData });
    return response.data;
  },

  getGeminiEngineStatus: async () => {
    const response = await apiClient.get('/api/mindsdb/gemini/engine/status');
    return response.data;
  },

  createGeminiVisionModel: async (modelData: {
    name: string;
    img_url_column?: string;
    context_column?: string;
  }) => {
    const response = await apiClient.post('/api/mindsdb/gemini/vision/model', modelData);
    return response.data;
  },

  createGeminiEmbeddingModel: async (modelData: {
    name: string;
    question_column?: string;
    context_column?: string;
  }) => {
    const response = await apiClient.post('/api/mindsdb/gemini/embedding/model', modelData);
    return response.data;
  },
};

// Models API
export const modelsAPI = {
  getModels: async (params?: {
    skip?: number;
    limit?: number;
    status?: string;
  }) => {
    const response = await apiClient.get('/api/models', { params });
    return response.data;
  },

  createModel: async (modelData: {
    name: string;
    dataset_id: number;
    target_column: string;
    feature_columns?: string[];
    model_type: string;
    engine?: string;
    model_params?: Record<string, any>;
  }) => {
    const response = await apiClient.post('/api/models', modelData);
    return response.data;
  },

  getModel: async (modelId: number) => {
    const response = await apiClient.get(`/api/models/${modelId}`);
    return response.data;
  },

  deleteModel: async (modelId: number) => {
    const response = await apiClient.delete(`/api/models/${modelId}`);
    return response.data;
  },

  predict: async (modelId: number, data: Record<string, any>) => {
    const response = await apiClient.post(`/api/models/${modelId}/predict`, data);
    return response.data;
  },

  retrainModel: async (modelId: number) => {
    const response = await apiClient.post(`/api/models/${modelId}/retrain`);
    return response.data;
  },
};

// Data Access API
export const dataAccessAPI = {
  getAccessibleDatasets: async (params?: {
    search?: string;
    sharing_level?: string;
    department?: string;
  }) => {
    const response = await apiClient.get('/api/data-access/datasets', { params });
    return response.data;
  },

  createAccessRequest: async (requestData: {
    dataset_id: number;
    request_type: 'access' | 'download' | 'share';
    requested_level: 'read' | 'write' | 'admin';
    purpose: string;
    justification: string;
    urgency?: 'low' | 'medium' | 'high';
    category?: 'research' | 'analysis' | 'compliance' | 'reporting' | 'development';
    expiry_date?: string;
  }) => {
    const response = await apiClient.post('/api/data-access/requests', requestData);
    return response.data;
  },

  getAccessRequests: async (params?: {
    status?: string;
    urgency?: string;
    my_requests?: boolean;
  }) => {
    const response = await apiClient.get('/api/data-access/requests', { params });
    return response.data;
  },

  approveAccessRequest: async (requestId: number, approvalData: {
    decision: 'approve' | 'reject';
    reason?: string;
    expiry_date?: string;
  }) => {
    const response = await apiClient.put(`/api/data-access/requests/${requestId}/approve`, approvalData);
    return response.data;
  },

  getAccessRequestDetails: async (requestId: number) => {
    const response = await apiClient.get(`/api/data-access/requests/${requestId}`);
    return response.data;
  },

  cancelAccessRequest: async (requestId: number) => {
    const response = await apiClient.delete(`/api/data-access/requests/${requestId}`);
    return response.data;
  },

  getAuditTrail: async (params?: {
    start_date?: string;
    end_date?: string;
    action?: string;
    dataset_id?: number;
  }) => {
    const response = await apiClient.get('/api/data-access/audit', { params });
    return response.data;
  },

  sendNotification: async (data: {
    recipient_email: string;
    subject: string;
    message: string;
    notification_type?: string;
  }) => {
    const response = await apiClient.post('/api/data-access/notify', data);
    return response.data;
  },
};

// Analytics API
export const analyticsAPI = {
  getOrganizationAnalytics: async () => {
    const response = await apiClient.get('/api/analytics/organization');
    return response.data;
  },

  getUserActivity: async (params?: {
    start_date?: string;
    end_date?: string;
    user_id?: number;
  }) => {
    const response = await apiClient.get('/api/analytics/user-activity', { params });
    return response.data;
  },

  getDatasetUsage: async (params?: {
    start_date?: string;
    end_date?: string;
    dataset_id?: number;
  }) => {
    const response = await apiClient.get('/api/analytics/dataset-usage', { params });
    return response.data;
  },

  getModelPerformance: async (params?: {
    start_date?: string;
    end_date?: string;
    model_id?: number;
  }) => {
    const response = await apiClient.get('/api/analytics/model-performance', { params });
    return response.data;
  },
};

// Data Connectors API
export const dataConnectorsAPI = {
  getConnectors: async (params?: {
    connector_type?: string;
    active_only?: boolean;
    include_datasets?: boolean;
  }) => {
    const response = await apiClient.get('/api/connectors', { params });
    return response.data;
  },

  createConnector: async (connectorData: {
    name: string;
    connector_type: string;
    description?: string;
    connection_config: Record<string, any>;
    credentials?: Record<string, any>;
  }) => {
    const response = await apiClient.post('/api/connectors', connectorData);
    return response.data;
  },

  getConnector: async (connectorId: number) => {
    const response = await apiClient.get(`/api/connectors/${connectorId}`);
    return response.data;
  },

  updateConnector: async (connectorId: number, updateData: {
    name?: string;
    description?: string;
    connection_config?: Record<string, any>;
    credentials?: Record<string, any>;
    is_active?: boolean;
  }) => {
    const response = await apiClient.put(`/api/connectors/${connectorId}`, updateData);
    return response.data;
  },

  deleteConnector: async (connectorId: number) => {
    const response = await apiClient.delete(`/api/connectors/${connectorId}`);
    return response.data;
  },

  testConnector: async (connectorId: number) => {
    const response = await apiClient.post(`/api/connectors/${connectorId}/test`);
    return response.data;
  },

  syncWithMindsDB: async (connectorId: number) => {
    const response = await apiClient.post(`/api/connectors/${connectorId}/sync`);
    return response.data;
  },

  createDatasetFromConnector: async (connectorId: number, datasetData: {
    dataset_name: string;
    description?: string;
    table_or_endpoint?: string;
    sharing_level?: string;
  }) => {
    const response = await apiClient.post(`/api/connectors/${connectorId}/create-dataset`, datasetData);
    return response.data;
  },
};

export default apiClient;