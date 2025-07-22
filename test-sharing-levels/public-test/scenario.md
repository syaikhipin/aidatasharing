# Public Level Test Scenario

## Authentication Requirements
- No login required
- Anyone with share link can access
- Anonymous access supported
- Optional password protection

## Test Cases

### Test 1: Anonymous Access via Share Link
**Setup**: Non-logged-in user accesses via share link
**Expected**: ✅ Full access granted
**Authentication**: Share token only, no login required

### Test 2: Logged-in User Access via Share Link
**Setup**: Logged-in user accesses via share link
**Expected**: ✅ Full access granted
**Authentication**: Share token (login status irrelevant)

### Test 3: Password-Protected Public Dataset
**Setup**: Anonymous user accesses password-protected public dataset
**Expected**: ✅ Access granted after password entry
**Authentication**: Share token + password, no login required

### Test 4: Expired Share Link
**Setup**: User tries to access expired public share link
**Expected**: ❌ Access denied with expiration message
**Authentication**: Share token validation fails

### Test 5: Invalid Share Token
**Setup**: User tries to access with invalid/non-existent token
**Expected**: ❌ 404 error - dataset not found
**Authentication**: Token validation fails

### Test 6: Public Dataset Chat
**Setup**: Anonymous user chats with public dataset
**Expected**: ✅ Chat works without login
**Authentication**: Share token + anonymous session

### Test 7: Public Dataset Download
**Setup**: Anonymous user downloads public dataset
**Expected**: ✅ Download works without login
**Authentication**: Share token only

## Implementation Notes
- No authentication required beyond share token
- Anonymous sessions are created for tracking
- Password protection is optional additional layer
- All features (view, download, chat) work anonymously
- Session tokens track anonymous usage