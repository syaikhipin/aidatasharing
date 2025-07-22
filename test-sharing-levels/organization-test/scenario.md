# Organization Level Test Scenario

## Authentication Requirements
- User must be logged in
- User must belong to the same organization as the dataset
- Share links work only for organization members

## Test Cases

### Test 1: Organization Member Access
**Setup**: Organization member tries to access organization dataset
**Expected**: ✅ Full access granted
**Authentication**: Login + organization membership verification

### Test 2: Organization Member via Share Link
**Setup**: Organization member accesses via share link while logged in
**Expected**: ✅ Access granted (faster access)
**Authentication**: Share token + login verification

### Test 3: External User with Share Link
**Setup**: User from different organization tries share link
**Expected**: ❌ Access denied, prompted to login
**Authentication**: Share token exists but organization check fails

### Test 4: Anonymous User with Share Link
**Setup**: Non-logged-in user tries to access via share link
**Expected**: ❌ Redirected to login page
**Authentication**: Must login first, then organization check

### Test 5: Organization Admin Access
**Setup**: Organization admin accesses any org dataset
**Expected**: ✅ Full access granted
**Authentication**: Login + admin role verification

## Implementation Notes
- Share tokens are generated but require organization membership
- Login is always required
- Organization membership is verified on each access
- Admins have access to all organization datasets