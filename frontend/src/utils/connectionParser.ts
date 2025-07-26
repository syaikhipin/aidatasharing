/**
 * URL Parser for Simplified Connectors
 * Converts connection URLs/strings into MindsDB-compatible configuration
 */

export interface ParsedConnection {
  connection_config: Record<string, any>;
  credentials: Record<string, any>;
}

export interface ConnectionParseError {
  success: false;
  error: string;
}

export interface ConnectionParseSuccess {
  success: true;
  data: ParsedConnection;
}

export type ConnectionParseResult = ConnectionParseSuccess | ConnectionParseError;

/**
 * Parse a connection URL/string into connection_config and credentials
 */
export function parseConnectionUrl(url: string, connectorType: string): ConnectionParseResult {
  try {
    switch (connectorType) {
      case 'mysql':
        return parseMySQLUrl(url);
      case 'postgresql':
        return parsePostgreSQLUrl(url);
      case 's3':
        return parseS3Url(url);
      case 'mongodb':
        return parseMongoDBUrl(url);
      case 'clickhouse':
        return parseClickHouseUrl(url);
      case 'api':
        return parseAPIUrl(url);
      default:
        return {
          success: false,
          error: `Unsupported connector type: ${connectorType}`
        };
    }
  } catch (error) {
    return {
      success: false,
      error: `Failed to parse connection URL: ${error instanceof Error ? error.message : 'Unknown error'}`
    };
  }
}

/**
 * Parse MySQL connection URL
 * Format: mysql://username:password@host:port/database?options
 */
function parseMySQLUrl(url: string): ConnectionParseResult {
  try {
    const parsed = new URL(url);
    
    if (parsed.protocol !== 'mysql:') {
      return { success: false, error: 'URL must start with mysql://' };
    }

    const host = parsed.hostname;
    const port = parsed.port ? parseInt(parsed.port) : 3306;
    const database = parsed.pathname.slice(1); // Remove leading slash
    const username = parsed.username;
    const password = parsed.password;

    if (!host || !database || !username) {
      return { 
        success: false, 
        error: 'MySQL URL must include host, database, and username' 
      };
    }

    return {
      success: true,
      data: {
        connection_config: {
          host,
          port,
          database
        },
        credentials: {
          user: username,
          password: password || ''
        }
      }
    };
  } catch (error) {
    return { 
      success: false, 
      error: 'Invalid MySQL URL format. Use: mysql://username:password@host:port/database' 
    };
  }
}

/**
 * Parse PostgreSQL connection URL
 * Format: postgresql://username:password@host:port/database?options
 */
function parsePostgreSQLUrl(url: string): ConnectionParseResult {
  try {
    const parsed = new URL(url);
    
    if (!['postgresql:', 'postgres:'].includes(parsed.protocol)) {
      return { success: false, error: 'URL must start with postgresql:// or postgres://' };
    }

    const host = parsed.hostname;
    const port = parsed.port ? parseInt(parsed.port) : 5432;
    const database = parsed.pathname.slice(1); // Remove leading slash
    const username = parsed.username;
    const password = parsed.password;

    if (!host || !database || !username) {
      return { 
        success: false, 
        error: 'PostgreSQL URL must include host, database, and username' 
      };
    }

    return {
      success: true,
      data: {
        connection_config: {
          host,
          port,
          database
        },
        credentials: {
          user: username,
          password: password || ''
        }
      }
    };
  } catch (error) {
    return { 
      success: false, 
      error: 'Invalid PostgreSQL URL format. Use: postgresql://username:password@host:port/database' 
    };
  }
}

/**
 * Parse S3 connection URL
 * Format: s3://access_key:secret_key@bucket_name/region
 */
function parseS3Url(url: string): ConnectionParseResult {
  try {
    const parsed = new URL(url);
    
    if (parsed.protocol !== 's3:') {
      return { success: false, error: 'URL must start with s3://' };
    }

    const bucketName = parsed.hostname;
    const region = parsed.pathname.slice(1) || 'us-east-1'; // Remove leading slash, default to us-east-1
    const accessKey = parsed.username;
    const secretKey = parsed.password;

    if (!bucketName || !accessKey || !secretKey) {
      return { 
        success: false, 
        error: 'S3 URL must include bucket name, access key, and secret key' 
      };
    }

    return {
      success: true,
      data: {
        connection_config: {
          bucket_name: bucketName,
          region
        },
        credentials: {
          aws_access_key_id: accessKey,
          aws_secret_access_key: secretKey
        }
      }
    };
  } catch (error) {
    return { 
      success: false, 
      error: 'Invalid S3 URL format. Use: s3://access_key:secret_key@bucket_name/region' 
    };
  }
}

/**
 * Parse MongoDB connection URL
 * Format: mongodb://username:password@host:port/database?options
 */
function parseMongoDBUrl(url: string): ConnectionParseResult {
  try {
    const parsed = new URL(url);
    
    if (parsed.protocol !== 'mongodb:') {
      return { success: false, error: 'URL must start with mongodb://' };
    }

    const host = parsed.hostname;
    const port = parsed.port ? parseInt(parsed.port) : 27017;
    const database = parsed.pathname.slice(1); // Remove leading slash
    const username = parsed.username;
    const password = parsed.password;

    if (!host || !database) {
      return { 
        success: false, 
        error: 'MongoDB URL must include host and database' 
      };
    }

    return {
      success: true,
      data: {
        connection_config: {
          host,
          port,
          database
        },
        credentials: {
          username: username || '',
          password: password || ''
        }
      }
    };
  } catch (error) {
    return { 
      success: false, 
      error: 'Invalid MongoDB URL format. Use: mongodb://username:password@host:port/database' 
    };
  }
}

/**
 * Parse ClickHouse connection URL
 * Format: clickhouse://username:password@host:port/database?options
 */
function parseClickHouseUrl(url: string): ConnectionParseResult {
  try {
    const parsed = new URL(url);
    
    if (parsed.protocol !== 'clickhouse:') {
      return { success: false, error: 'URL must start with clickhouse://' };
    }

    const host = parsed.hostname;
    const port = parsed.port ? parseInt(parsed.port) : 9000;
    const database = parsed.pathname.slice(1) || 'default'; // Remove leading slash, default to 'default'
    const username = parsed.username || 'default';
    const password = parsed.password;

    if (!host) {
      return { 
        success: false, 
        error: 'ClickHouse URL must include host' 
      };
    }

    return {
      success: true,
      data: {
        connection_config: {
          host,
          port,
          database
        },
        credentials: {
          user: username,
          password: password || ''
        }
      }
    };
  } catch (error) {
    return { 
      success: false, 
      error: 'Invalid ClickHouse URL format. Use: clickhouse://username:password@host:port/database' 
    };
  }
}

/**
 * Parse API connection URL
 * Format: https://api.example.com/endpoint?api_key=key&param=value
 */
function parseAPIUrl(url: string): ConnectionParseResult {
  try {
    const parsed = new URL(url);
    
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      return { success: false, error: 'API URL must start with http:// or https://' };
    }

    const baseUrl = `${parsed.protocol}//${parsed.host}`;
    const endpoint = parsed.pathname;
    const searchParams = new URLSearchParams(parsed.search);
    
    // Extract common API authentication parameters
    const apiKey = searchParams.get('api_key') || searchParams.get('apikey') || searchParams.get('key');
    const token = searchParams.get('token') || searchParams.get('access_token');
    const authHeader = searchParams.get('auth_header') || 'Authorization';

    // Remove auth params from the endpoint URL to keep it clean
    if (apiKey) {
      searchParams.delete('api_key');
      searchParams.delete('apikey');
      searchParams.delete('key');
    }
    if (token) {
      searchParams.delete('token');
      searchParams.delete('access_token');
    }

    const cleanEndpoint = endpoint + (searchParams.toString() ? `?${searchParams.toString()}` : '');

    return {
      success: true,
      data: {
        connection_config: {
          base_url: baseUrl,
          endpoint: cleanEndpoint,
          method: 'GET'
        },
        credentials: {
          api_key: apiKey || token || '',
          auth_header: authHeader
        }
      }
    };
  } catch (error) {
    return { 
      success: false, 
      error: 'Invalid API URL format. Use: https://api.example.com/endpoint?api_key=your_key' 
    };
  }
}

/**
 * Generate example URLs for each connector type
 */
export const CONNECTION_EXAMPLES = {
  mysql: 'mysql://user:password@localhost:3306/mydb',
  postgresql: 'postgresql://user:password@localhost:5432/postgres',
  s3: 's3://AKIA...:secret@my-bucket/us-east-1',
  mongodb: 'mongodb://user:password@localhost:27017/mydb',
  clickhouse: 'clickhouse://default:password@localhost:9000/default',
  api: 'https://api.example.com/users?api_key=abc123'
};

/**
 * Validate a connection URL format without parsing
 */
export function validateConnectionUrl(url: string, connectorType: string): { valid: boolean; error?: string } {
  const result = parseConnectionUrl(url, connectorType);
  return {
    valid: result.success,
    error: result.success ? undefined : result.error
  };
}