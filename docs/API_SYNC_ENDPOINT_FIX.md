# API Sync Endpoint Fix

## Problem Identified
The frontend was experiencing a 400 Bad Request error when trying to sync connectors with MindsDB:
```
AxiosError: Request failed with status code 400
src/lib/api.ts (933:22) @ async Object.syncWithMindsDB
```

## Root Cause Analysis
The issue was caused by **duplicate API endpoints** in the backend:

### Conflicting Routes
Both endpoints used the same route path `/{connector_id}/sync`:

1. **Line 284**: `sync_connector_data` - Real-time data sync endpoint
2. **Line 621**: `sync_with_mindsdb` - MindsDB integration sync endpoint

### The Problem
The first endpoint (`sync_connector_data`) was being called instead of the intended MindsDB sync endpoint. This endpoint has validation that throws a 400 error:

```python
# Check if real-time sync is supported
if not getattr(connector, 'supports_real_time', False) and not force:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Real-time sync not supported for this connector. Use force=true to override."
    )
```

Since most connectors don't have `supports_real_time=True`, this was causing the 400 error.

## Solution Applied

### 1. Backend Route Change
Changed the MindsDB sync endpoint route to avoid conflict:
```python
# Before (conflicting)
@router.post("/{connector_id}/sync")
async def sync_with_mindsdb(

# After (unique route)
@router.post("/{connector_id}/sync-mindsdb")
async def sync_with_mindsdb(
```

### 2. Frontend API Client Update
Updated the frontend to use the new endpoint:
```typescript
// Before
syncWithMindsDB: async (connectorId: number) => {
  const response = await apiClient.post(`/api/connectors/${connectorId}/sync`);
  return response.data;
},

// After
syncWithMindsDB: async (connectorId: number) => {
  const response = await apiClient.post(`/api/connectors/${connectorId}/sync-mindsdb`);
  return response.data;
},
```

## Expected Results
✅ **400 Error Eliminated**: No more "Real-time sync not supported" errors  
✅ **Correct Endpoint Called**: MindsDB sync endpoint now properly accessed  
✅ **Route Conflict Resolved**: Both sync endpoints can coexist  
✅ **Functional Sync**: MindsDB integration should work as intended  

## API Endpoint Summary
- **Data Sync**: `POST /api/connectors/{id}/sync` - For real-time data synchronization
- **MindsDB Sync**: `POST /api/connectors/{id}/sync-mindsdb` - For MindsDB integration

## Files Modified
- `backend/app/api/data_connectors.py` - Changed MindsDB sync route
- `frontend/src/lib/api.ts` - Updated API client endpoint URL

## Testing
To verify the fix:
1. Navigate to the datasets sharing page
2. Click "Sync" button on a connector
3. Should no longer see 400 error
4. Check browser Network tab for successful API call to `/sync-mindsdb`
## Syntax Error Fix

### Problem Identified
After fixing the duplicate API routes, a syntax error was introduced:
```
IndentationError: unexpected indent
File "backend/app/api/data_connectors.py", line 622
    connector_id: int,
```

### Root Cause
The function definition line `async def sync_with_mindsdb(` was accidentally removed during the route path fix, leaving only the parameter list which caused an indentation error.

### Solution Applied
Properly restored the function definition:
```python
# Before (broken syntax)
@router.post("/{connector_id}/sync-mindsdb")
    connector_id: int,
    background_tasks: BackgroundTasks,
    ...

# After (correct syntax)
@router.post("/{connector_id}/sync-mindsdb")
async def sync_with_mindsdb(
    connector_id: int,
    background_tasks: BackgroundTasks,
    ...
```

### Verification
✅ **Python Compilation**: File compiles without syntax errors  
✅ **Function Definition**: `sync_with_mindsdb` properly defined  
✅ **Backend Import**: Module imports successfully  
✅ **Server Startup**: Backend can start without crashing  