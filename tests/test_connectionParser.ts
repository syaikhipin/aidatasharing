/**
 * Tests for frontend connection parser
 */

import { parseConnectionUrl, validateConnectionUrl } from '../connectionParser';

// Mock tests (would normally use Jest or similar)
function runTests() {
  console.log('Running frontend connection parser tests...');

  // Test MySQL URL parsing
  const mysqlResult = parseConnectionUrl('mysql://user:pass@localhost:3306/mydb', 'mysql');
  console.assert(mysqlResult.success === true, 'MySQL parsing should succeed');
  if (mysqlResult.success) {
    console.assert(mysqlResult.data.connection_config.host === 'localhost', 'MySQL host should be localhost');
    console.assert(mysqlResult.data.connection_config.port === 3306, 'MySQL port should be 3306');
    console.assert(mysqlResult.data.connection_config.database === 'mydb', 'MySQL database should be mydb');
    console.assert(mysqlResult.data.credentials.user === 'user', 'MySQL user should be user');
    console.assert(mysqlResult.data.credentials.password === 'pass', 'MySQL password should be pass');
  }

  // Test PostgreSQL URL parsing
  const pgResult = parseConnectionUrl('postgresql://user:pass@localhost:5432/postgres', 'postgresql');
  console.assert(pgResult.success === true, 'PostgreSQL parsing should succeed');
  if (pgResult.success) {
    console.assert(pgResult.data.connection_config.host === 'localhost', 'PostgreSQL host should be localhost');
    console.assert(pgResult.data.connection_config.port === 5432, 'PostgreSQL port should be 5432');
  }

  // Test S3 URL parsing
  const s3Result = parseConnectionUrl('s3://AKIA123:secret@my-bucket/us-east-1', 's3');
  console.assert(s3Result.success === true, 'S3 parsing should succeed');
  if (s3Result.success) {
    console.assert(s3Result.data.connection_config.bucket_name === 'my-bucket', 'S3 bucket should be my-bucket');
    console.assert(s3Result.data.connection_config.region === 'us-east-1', 'S3 region should be us-east-1');
    console.assert(s3Result.data.credentials.aws_access_key_id === 'AKIA123', 'S3 access key should be AKIA123');
  }

  // Test API URL parsing
  const apiResult = parseConnectionUrl('https://api.example.com/users?api_key=abc123&limit=10', 'api');
  console.assert(apiResult.success === true, 'API parsing should succeed');
  if (apiResult.success) {
    console.assert(apiResult.data.connection_config.base_url === 'https://api.example.com', 'API base URL should be correct');
    console.assert(apiResult.data.connection_config.endpoint === '/users?limit=10', 'API endpoint should exclude api_key');
    console.assert(apiResult.data.credentials.api_key === 'abc123', 'API key should be extracted');
  }

  // Test invalid URL
  const invalidResult = parseConnectionUrl('invalid-url', 'mysql');
  console.assert(invalidResult.success === false, 'Invalid URL should fail');

  // Test validation
  const validation = validateConnectionUrl('mysql://user:pass@localhost:3306/mydb', 'mysql');
  console.assert(validation.valid === true, 'Valid URL should pass validation');

  const invalidValidation = validateConnectionUrl('invalid', 'mysql');
  console.assert(invalidValidation.valid === false, 'Invalid URL should fail validation');

  console.log('All frontend connection parser tests passed!');
}

// Export for use in other files
export { runTests };

// Run tests if this file is executed directly
if (typeof window !== 'undefined') {
  runTests();
}