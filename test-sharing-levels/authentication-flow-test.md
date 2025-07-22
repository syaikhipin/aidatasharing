# Authentication Flow Test for Three-Level Sharing

## Overview
This document outlines the complete authentication flow for the three-level sharing system.

## Authentication Levels

### 1. Private Level
```
Dataset Sharing Level: "private"
Share Link Generation: ❌ No share links created
Access Requirements: Full authentication + ownership
API Endpoints Used: Standard authenticated endpoints only
```

**Flow:**
1. User must be logged in
2. User must be the dataset owner
3. No share tokens are generated
4. Access only through main application

### 2. Organization Level
```
Dataset Sharing Level: "organization"
Share Link Generation: ✅ Share links created
Access Requirements: Full authentication + organization membership
API Endpoints Used: Authenticated endpoints with org verification
```

**Flow:**
1. Share link is generated with token
2. User clicks share link
3. System checks if user is logged in
4. If not logged in → redirect to login
5. If logged in → verify organization membership
6. If same organization → grant access
7. If different organization → deny access

### 3. Public Level
```
Dataset Sharing Level: "public"
Share Link Generation: ✅ Share links created
Access Requirements: Share token only (no authentication)
API Endpoints Used: Public endpoints (no auth headers)
```

**Flow:**
1. Share link is generated with token
2. User clicks share link (can be anonymous)
3. System tries public endpoint first
4. If public access succeeds → grant immediate access
5. Optional password protection can be added
6. No login required at any point

## Implementation Details

### Frontend Logic
```javascript
// Shared dataset access flow
async function fetchSharedDataset(token) {
  try {
    // Step 1: Try public access first (no auth)
    const response = await dataSharingAPI.getPublicSharedDataset(token);
    return response; // Success - public dataset
  } catch (publicError) {
    if (publicError.status === 401 || publicError.status === 403) {
      // Step 2: Try authenticated access (organization level)
      try {
        const response = await dataSharingAPI.getSharedDataset(token);
        return response; // Success - organization dataset
      } catch (authError) {
        if (authError.status === 401) {
          // User needs to login for organization access
          throw new Error('Login required');
        }
        throw authError;
      }
    }
    throw publicError;
  }
}
```

### Backend API Endpoints

#### Public Endpoints (No Authentication)
```
GET /api/data-sharing/public/shared/{token}
GET /api/data-sharing/public/shared/{token}/info
POST /api/data-sharing/public/shared/{token}/access
POST /api/data-sharing/public/shared/{token}/chat
```

#### Authenticated Endpoints
```
GET /api/data-sharing/shared/{token}
POST /api/data-sharing/shared/{token}/access
GET /api/data-sharing/my-shared-datasets
DELETE /api/data-sharing/shared/{dataset_id}/disable
```

## Testing Scenarios

### Scenario 1: Public Dataset Access
```
1. Create public dataset
2. Generate share link
3. Open share link in incognito browser
4. Expected: Immediate access without login
5. Test chat functionality
6. Test download functionality
```

### Scenario 2: Organization Dataset Access
```
1. Create organization dataset
2. Generate share link
3. Share with organization member
4. Member clicks link while logged in
5. Expected: Access granted
6. Share with external user
7. Expected: Access denied or login prompt
```

### Scenario 3: Private Dataset
```
1. Create private dataset
2. Verify no share link is generated
3. Only owner can access through main app
4. Other users cannot access even if logged in
```

## Error Handling

### Common Error Responses
```
401 Unauthorized: Login required
403 Forbidden: Access denied (wrong organization)
404 Not Found: Invalid share token
410 Gone: Share link expired
```

### User-Friendly Messages
```
Public Access: "Loading dataset..."
Organization Access: "Verifying access permissions..."
Login Required: "This dataset requires you to be logged in"
Access Denied: "You don't have permission to access this dataset"
Expired Link: "This share link has expired"
```

## Security Considerations

1. **Public datasets**: No sensitive data should be marked as public
2. **Organization datasets**: Verify organization membership on every request
3. **Private datasets**: No share tokens generated, owner-only access
4. **Session management**: Anonymous sessions for public access tracking
5. **Rate limiting**: Prevent abuse of public endpoints