# Three-Level Sharing Authentication Test

This folder contains test scenarios for the three-level sharing system:

## 1. Private Level
- **Access**: Only the dataset owner
- **Authentication**: Full login required
- **Test**: `private-test/`

## 2. Organization Level
- **Access**: All members within the same organization
- **Authentication**: Organization membership verification
- **Test**: `organization-test/`

## 3. Public Level
- **Access**: Anyone with the share link
- **Authentication**: No login required (anonymous access)
- **Test**: `public-test/`

## Testing Instructions

1. **Private Test**: User must be logged in and be the owner
2. **Organization Test**: User must be logged in and belong to the same organization
3. **Public Test**: No authentication required, works with share token only

Each test folder contains specific scenarios and expected behaviors.