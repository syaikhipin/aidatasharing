import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
    
    const response = await apiClient.post('/api/v1/auth/login', formData, {
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
    const response = await apiClient.post('/api/v1/auth/register', userData);
    return response.data;
  },
  
  getMe: async () => {
    const response = await apiClient.get('/api/v1/auth/me');
    return response.data;
  },
};

// Admin API
export const adminAPI = {
  getConfigurations: async () => {
    const response = await apiClient.get('/api/v1/admin/config');
    return response.data;
  },
  
  createConfiguration: async (config: { key: string; value?: string; description?: string }) => {
    const response = await apiClient.post('/api/v1/admin/config', config);
    return response.data;
  },
  
  updateConfiguration: async (key: string, config: { value?: string; description?: string }) => {
    const response = await apiClient.put(`/api/v1/admin/config/${key}`, config);
    return response.data;
  },
  
  deleteConfiguration: async (key: string) => {
    const response = await apiClient.delete(`/api/v1/admin/config/${key}`);
    return response.data;
  },
  
  setGoogleApiKey: async (apiKey: string) => {
    const response = await apiClient.post('/api/v1/admin/google-api-key', {
      api_key: apiKey,
    });
    return response.data;
  },
  
  getGoogleApiKeyStatus: async () => {
    const response = await apiClient.get('/api/v1/admin/google-api-key');
    return response.data;
  },
};

// Organizations API
export const organizationsAPI = {
  getOptions: async () => {
    const response = await apiClient.get('/api/v1/organizations/options');
    return response.data;
  },
  
  create: async (orgData: {
    name: string;
    description?: string;
    type?: string;
    website?: string;
    contact_email?: string;
  }) => {
    const response = await apiClient.post('/api/v1/organizations', orgData);
    return response.data;
  },
  
  getMy: async () => {
    const response = await apiClient.get('/api/v1/organizations/my');
    return response.data;
  },
  
  getMembers: async (organizationId: number) => {
    const response = await apiClient.get(`/api/v1/organizations/${organizationId}/members`);
    return response.data;
  },
  
  getDepartments: async (organizationId: number) => {
    const response = await apiClient.get(`/api/v1/organizations/${organizationId}/departments`);
    return response.data;
  },
  
  createDepartment: async (organizationId: number, deptData: {
    name: string;
    description?: string;
  }) => {
    const response = await apiClient.post(`/api/v1/organizations/${organizationId}/departments`, {
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
    const response = await apiClient.get('/api/v1/datasets', { params });
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
    const response = await apiClient.post('/api/v1/datasets', datasetData);
    return response.data;
  },
  
  getDataset: async (datasetId: number) => {
    const response = await apiClient.get(`/api/v1/datasets/${datasetId}`);
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
    const response = await apiClient.put(`/api/v1/datasets/${datasetId}`, updateData);
    return response.data;
  },
  
  deleteDataset: async (datasetId: number) => {
    const response = await apiClient.delete(`/api/v1/datasets/${datasetId}`);
    return response.data;
  },
  
  uploadDataset: async (file: File, metadata?: {
    name?: string;
    description?: string;
    sharing_level?: string;
  }) => {
    const formData = new FormData();
    formData.append('file', file);
    
    if (metadata?.name) formData.append('name', metadata.name);
    if (metadata?.description) formData.append('description', metadata.description);
    if (metadata?.sharing_level) formData.append('sharing_level', metadata.sharing_level);
    
    const response = await apiClient.post('/api/v1/datasets/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  
  downloadDataset: async (datasetId: number) => {
    const response = await apiClient.get(`/api/v1/datasets/${datasetId}/download`);
    return response.data;
  },
  
  getDatasetStats: async (datasetId: number) => {
    const response = await apiClient.get(`/api/v1/datasets/${datasetId}/stats`);
    return response.data;
  },
};

// MindsDB API
export const mindsdbAPI = {
  getStatus: async () => {
    const response = await apiClient.get('/api/v1/mindsdb/status');
    return response.data;
  },
  
  getModels: async () => {
    const response = await apiClient.get('/api/v1/mindsdb/models');
    return response.data;
  },
  
  createModel: async (modelData: { name: string; query: string; engine?: string }) => {
    const response = await apiClient.post('/api/v1/mindsdb/models', modelData);
    return response.data;
  },
  
  getModelInfo: async (modelName: string) => {
    const response = await apiClient.get(`/api/v1/mindsdb/models/${modelName}`);
    return response.data;
  },
  
  predict: async (modelName: string, data: Record<string, any>) => {
    const response = await apiClient.post(`/api/v1/mindsdb/models/${modelName}/predict`, data);
    return response.data;
  },
  
  deleteModel: async (modelName: string) => {
    const response = await apiClient.delete(`/api/v1/mindsdb/models/${modelName}`);
    return response.data;
  },
  
  getDatabases: async () => {
    const response = await apiClient.get('/api/v1/mindsdb/databases');
    return response.data;
  },
  
  createDatabase: async (dbData: { name: string; engine: string; parameters: Record<string, any> }) => {
    const response = await apiClient.post('/api/v1/mindsdb/databases', dbData);
    return response.data;
  },
  
  executeSQL: async (query: string) => {
    const response = await apiClient.post('/api/v1/mindsdb/sql', { query });
    return response.data;
  },
};

export default apiClient; 