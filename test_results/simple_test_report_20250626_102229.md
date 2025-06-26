
# AI Share Platform - Test Report
Generated: 2025-06-26 10:22:29

## Summary
- **Total Tests**: 17
- **Passed**: 6
- **Failed**: 11
- **Success Rate**: 35.3%

**Status**: 🔴 CRITICAL ISSUES

## Frontend Connectivity
**Tests**: 6/8 passed

- ✅ **Frontend Server Responding**: Status: 200
- ❌ **Page /auth/login Accessible**: Status: 404
- ❌ **Page /auth/register Accessible**: Status: 404
- ✅ **Protected Page /dashboard Handles Auth**: Status: 200
- ✅ **Protected Page /datasets Handles Auth**: Status: 200
- ✅ **Protected Page /models Handles Auth**: Status: 200
- ✅ **Protected Page /sql Handles Auth**: Status: 200
- ✅ **Protected Page /analytics Handles Auth**: Status: 200

## Backend Api
**Tests**: 0/5 passed

- ❌ **Backend Health Check**: Error: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /health (Caused by ConnectTimeoutError(<urllib3.connection.HTTPConnection object at 0x104796cc0>, 'Connection to localhost timed out. (connect timeout=10)'))
- ❌ **API Documentation**: Error: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /docs (Caused by ConnectTimeoutError(<urllib3.connection.HTTPConnection object at 0x104796ae0>, 'Connection to localhost timed out. (connect timeout=10)'))
- ❌ **OpenAPI Schema**: Error: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /openapi.json (Caused by ConnectTimeoutError(<urllib3.connection.HTTPConnection object at 0x104797260>, 'Connection to localhost timed out. (connect timeout=10)'))
- ❌ **CORS Headers Present**: Error: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /auth/login (Caused by ConnectTimeoutError(<urllib3.connection.HTTPConnection object at 0x104795d90>, 'Connection to localhost timed out. (connect timeout=10)'))
- ❌ **Authentication Required**: Error: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /auth/me (Caused by ConnectTimeoutError(<urllib3.connection.HTTPConnection object at 0x104796390>, 'Connection to localhost timed out. (connect timeout=10)'))

## Registration Flow
**Tests**: 0/1 passed

- ❌ **Registration Endpoint Functional**: Error: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /auth/register (Caused by ConnectTimeoutError(<urllib3.connection.HTTPConnection object at 0x104797c20>, 'Connection to localhost timed out. (connect timeout=10)'))

## Database Connectivity
**Tests**: 0/3 passed

- ❌ **Organizations List Endpoint Responds**: Error: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /organizations/ (Caused by ConnectTimeoutError(<urllib3.connection.HTTPConnection object at 0x1047bc5c0>, 'Connection to localhost timed out. (connect timeout=10)'))
- ❌ **Datasets List Endpoint Responds**: Error: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /datasets/ (Caused by ConnectTimeoutError(<urllib3.connection.HTTPConnection object at 0x1047bcef0>, 'Connection to localhost timed out. (connect timeout=10)'))
- ❌ **Models List Endpoint Responds**: Error: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /models/ (Caused by ConnectTimeoutError(<urllib3.connection.HTTPConnection object at 0x104797d70>, 'Connection to localhost timed out. (connect timeout=10)'))

## Recommendations

🚨 Critical issues detected. Check server configuration.
