# Unified Data Sharing & Connection Hub

## Overview

The Data Sharing & Connection Hub provides a unified interface for managing all aspects of data sharing, secure proxies, and data connections in one centralized location. This replaces the previously separate interfaces for datasets, proxy management, and simplified connections.

## Features

### 📊 Dataset Sharing Management
- Manage sharing levels (Private, Organization, Public) for all datasets
- Create and manage public share links with chat functionality
- View sharing statistics and dataset metadata
- Copy and open share links directly from the interface

### 🛡️ Secure Proxy Connectors
- Create secure proxies that hide real URLs and credentials from users
- Support for API and database proxy types
- Configure allowed operations and access levels
- Generate shared links for proxy access
- View usage analytics and request counts

### 🔗 Shared Links
- Manage all shared links created from proxy connectors
- Set expiration dates and usage limits
- Configure authentication requirements
- Monitor usage statistics and access patterns

### 🔌 Data Connections
- Simplified connector creation using connection URLs
- Support for multiple database types (MySQL, PostgreSQL, MongoDB, ClickHouse)
- Test connections and sync with MindsDB
- Create datasets directly from API connectors

## Navigation

The interface is organized into four main tabs:

1. **Dataset Sharing** - Manage dataset sharing levels and public links
2. **Secure Proxies** - Create and manage proxy connectors
3. **Shared Links** - Manage shared access links
4. **Data Connections** - Manage simplified data connectors

## URL Navigation

The interface supports deep linking with URL parameters:
- `/datasets/sharing` - Default view (Dataset Sharing tab)
- `/datasets/sharing?tab=proxies` - Direct access to Secure Proxies tab
- `/datasets/sharing?tab=links` - Direct access to Shared Links tab
- `/datasets/sharing?tab=connectors` - Direct access to Data Connections tab

## Legacy Redirects

The following legacy URLs automatically redirect to the unified interface:
- `/proxy` → `/datasets/sharing?tab=proxies`
- `/connections/simplified` → `/datasets/sharing?tab=connectors`

## Integration Benefits

### Unified User Experience
- Single interface for all data sharing and connection management
- Consistent UI/UX across all functionality
- Centralized statistics and overview

### Improved Workflow
- Create datasets, set up proxies, and manage sharing all in one place
- Seamless transitions between different types of data access
- Integrated proxy creation and shared link generation

### Enhanced Security
- Proxy URL parsing and credential encryption integrated with sharing workflows
- Consistent security policies across all connection types
- Centralized access control and monitoring

## Technical Implementation

### Architecture
- React/TypeScript frontend with Next.js app router
- Unified state management across all connection types
- Integrated API calls for datasets, proxies, and connectors
- Backward compatibility with existing sharing workflows

### Components
- Reuses existing form components (ProxyConnectorForm, SharedLinkForm, SimplifiedConnectorForm)
- Maintains existing SharingLevelSelector and related components
- Integrated modal system for creating new resources

### Data Flow
- Single data fetching function for all resource types
- Unified error handling and loading states
- Consistent toast notifications across all operations

## Future Enhancements

- Real-time updates for shared link usage
- Advanced analytics dashboard
- Bulk operations for multiple datasets/connectors
- Enhanced filtering and search capabilities
- Export functionality for sharing reports