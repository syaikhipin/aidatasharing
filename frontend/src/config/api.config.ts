/**
 * API Configuration
 * Dynamically determines the API base URL and proxy paths
 */

// Get base URL from environment or detect from current location
const getApiBaseUrl = (): string => {
  // Check for environment variable first
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }

  // In browser context, use current location
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    
    // Default to port 8000 for local development
    // In production, use the same host without port (assuming reverse proxy)
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return `${protocol}//${hostname}:8000`;
    }
    
    // For production, use same host
    return `${protocol}//${hostname}`;
  }

  // Default fallback for SSR
  return 'http://localhost:8000';
};

// Get proxy base path
const getProxyBasePath = (): string => {
  return '/api/proxy';
};

// Configuration object
export const apiConfig = {
  baseUrl: getApiBaseUrl(),
  proxyPath: getProxyBasePath(),
  
  // Build full URLs for different services
  urls: {
    // Main API endpoints
    api: () => `${apiConfig.baseUrl}/api`,
    
    // Proxy endpoints for different connector types
    proxy: {
      mysql: (dbName: string, token: string) => 
        `${apiConfig.baseUrl}${apiConfig.proxyPath}/mysql/${encodeURIComponent(dbName)}?token=${token}`,
      
      postgresql: (dbName: string, token: string) => 
        `${apiConfig.baseUrl}${apiConfig.proxyPath}/postgresql/${encodeURIComponent(dbName)}?token=${token}`,
      
      api: (apiName: string, token: string) => {
        const url = `${apiConfig.baseUrl}${apiConfig.proxyPath}/api/${encodeURIComponent(apiName)}?token=${token}`;
        console.log('Generated API proxy URL:', url);
        return url;
      },
      
      clickhouse: (dbName: string, token: string) => 
        `${apiConfig.baseUrl}${apiConfig.proxyPath}/clickhouse/${encodeURIComponent(dbName)}?token=${token}`,
      
      mongodb: (dbName: string, token: string) => 
        `${apiConfig.baseUrl}${apiConfig.proxyPath}/mongodb/${encodeURIComponent(dbName)}?token=${token}`,
      
      s3: (bucketName: string, token: string) => 
        `${apiConfig.baseUrl}${apiConfig.proxyPath}/s3/${encodeURIComponent(bucketName)}?token=${token}`,
      
      // Generic proxy URL builder
      build: (type: string, name: string, token: string) => 
        `${apiConfig.baseUrl}${apiConfig.proxyPath}/${type}/${encodeURIComponent(name)}?token=${token}`
    },
    
    // Data sharing endpoints
    sharing: {
      public: (shareToken: string) => 
        `${apiConfig.baseUrl}/api/data-sharing/public/shared/${shareToken}`,
      
      download: (shareToken: string, password?: string) => 
        `${apiConfig.baseUrl}/api/data-sharing/public/shared/${shareToken}/download${password ? `?password=${password}` : ''}`,
      
      chat: (shareToken: string) => 
        `${apiConfig.baseUrl}/api/data-sharing/public/shared/${shareToken}/chat`
    }
  },
  
  // Helper functions
  helpers: {
    // Get the appropriate proxy URL based on connector type
    getProxyUrl: (connectorType: string, name: string, token: string): string => {
      switch (connectorType.toLowerCase()) {
        case 'mysql':
          return apiConfig.urls.proxy.mysql(name, token);
        case 'postgresql':
          return apiConfig.urls.proxy.postgresql(name, token);
        case 'api':
          return apiConfig.urls.proxy.api(name, token);
        case 'clickhouse':
          return apiConfig.urls.proxy.clickhouse(name, token);
        case 'mongodb':
          return apiConfig.urls.proxy.mongodb(name, token);
        case 's3':
          return apiConfig.urls.proxy.s3(name, token);
        default:
          return apiConfig.urls.proxy.build(connectorType, name, token);
      }
    },
    
    // Build a connection string for display
    getConnectionString: (connectorType: string, name: string, token: string): string => {
      const baseUrl = apiConfig.baseUrl.replace('http://', '').replace('https://', '');
      
      switch (connectorType.toLowerCase()) {
        case 'mysql':
          return `mysql://proxy_user:${token}@${baseUrl}/proxy/mysql/${encodeURIComponent(name)}`;
        case 'postgresql':
          return `postgresql://proxy_user:${token}@${baseUrl}/proxy/postgresql/${encodeURIComponent(name)}`;
        case 'mongodb':
          return `mongodb://proxy_user:${token}@${baseUrl}/proxy/mongodb/${encodeURIComponent(name)}`;
        case 's3':
          return `s3://${baseUrl}/proxy/s3/${encodeURIComponent(name)}?access_key=proxy_user&secret_key=${token}`;
        case 'api':
        default:
          const apiUrl = apiConfig.urls.proxy.api(name, token);
          console.log('Connection string for API type:', { connectorType, name, token: token.substring(0,8)+'...', result: apiUrl });
          return apiUrl;
      }
    }
  }
};

export default apiConfig;