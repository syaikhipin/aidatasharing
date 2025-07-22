# Private Level Test Scenario

## Authentication Requirements
- User must be logged in
- User must be the dataset owner
- No share links work for private datasets

## Test Cases

### Test 1: Owner Access
**Setup**: Dataset owner tries to access their private dataset
**Expected**: ✅ Full access granted
**Authentication**: Standard login

### Test 2: Organization Member Access
**Setup**: Another organization member tries to access private dataset
**Expected**: ❌ Access denied
**Authentication**: Login required, but access still denied

### Test 3: Public Access via Share Link
**Setup**: Anonymous user tries to access via share link
**Expected**: ❌ Share link should not exist for private datasets
**Authentication**: No share links generated

### Test 4: External User Access
**Setup**: User from different organization tries to access
**Expected**: ❌ Access denied
**Authentication**: Login required, but access denied

## Implementation Notes
- Private datasets should not generate share tokens
- All access requires full authentication
- Only owner can view/download