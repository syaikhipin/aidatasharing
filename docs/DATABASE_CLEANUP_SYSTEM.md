# Database Cleanup System - Implementation Guide

## Overview
Comprehensive database cleanup system to remove orphaned datasets and empty organizations from the platform. This system helps maintain database integrity by cleaning up data that is no longer associated with valid users or organizations.

## Problem Statement
Over time, databases can accumulate orphaned data:
- **Orphaned Datasets**: Datasets that reference non-existent user IDs as owners
- **Empty Organizations**: Organizations that have no users (excluding admin organizations)
- **Related Data**: Access logs, downloads, models, chat sessions, etc. tied to orphaned datasets

## Solution Components

### 1. Standalone Cleanup Script (`database_cleanup.py`)
A comprehensive Python script for direct database cleanup operations.

**Features:**
- Dry-run mode to preview changes without executing
- Detailed statistics and impact analysis
- Safe deletion order respecting foreign key constraints
- Protection of admin-related organizations
- Comprehensive logging and error handling

**Usage:**
```bash
# Preview what would be cleaned up
python database_cleanup.py --dry-run

# Show database statistics only
python database_cleanup.py --stats-only

# Run actual cleanup with confirmation
python database_cleanup.py

# Run cleanup without confirmation prompts
python database_cleanup.py --force
```

### 2. Admin API Endpoints
REST API endpoints integrated into the admin panel for web-based cleanup operations.

**Endpoints:**

#### GET `/api/admin/cleanup/stats`
Get comprehensive cleanup statistics and preview of orphaned data.

**Response:**
```json
{
  "database_stats": {
    "total_users": 5,
    "total_organizations": 3,
    "total_datasets": 10,
    "active_datasets": 8
  },
  "orphaned_data": {
    "orphaned_datasets": {
      "count": 2,
      "datasets": [
        {
          "id": 15,
          "name": "Old Dataset",
          "owner_id": 999,
          "created_at": "2024-01-15T10:30:00"
        }
      ],
      "related_data": {
        "access_logs": 5,
        "downloads": 2,
        "models": 1,
        "chat_sessions": 3,
        "chat_messages": 12,
        "share_accesses": 1
      }
    },
    "empty_organizations": {
      "count": 1,
      "organizations": [
        {
          "id": 8,
          "name": "Unused Corp",
          "type": "small_business",
          "created_at": "2024-01-10T15:45:00"
        }
      ],
      "related_data": {
        "connectors": 2,
        "org_datasets": 0
      }
    }
  }
}
```

#### POST `/api/admin/cleanup/orphaned-datasets?confirm=true`
Clean up orphaned datasets and all related data.

**Parameters:**
- `confirm` (boolean, required): Must be `true` to execute cleanup

**Response:**
```json
{
  "message": "Successfully deleted 2 orphaned datasets",
  "deleted_count": 2,
  "deleted_datasets": [
    {"id": 15, "name": "Old Dataset", "owner_id": 999},
    {"id": 16, "name": "Another Old Dataset", "owner_id": 888}
  ],
  "related_data_deleted": {
    "access_logs": 5,
    "downloads": 2,
    "models": 1,
    "chat_sessions": 3,
    "chat_messages": 12,
    "share_accesses": 1
  }
}
```

#### POST `/api/admin/cleanup/empty-organizations?confirm=true`
Clean up empty organizations and related data.

#### POST `/api/admin/cleanup/all?confirm=true`
Clean up both orphaned datasets and empty organizations in one operation.

### 3. Frontend API Integration
JavaScript client functions integrated into the admin panel API.

```typescript
// Get cleanup statistics
const stats = await adminAPI.getCleanupStats();

// Clean up orphaned datasets
const result = await adminAPI.cleanupOrphanedDatasets(true);

// Clean up empty organizations
const result = await adminAPI.cleanupEmptyOrganizations(true);

// Clean up all orphaned data
const result = await adminAPI.cleanupAllOrphanedData(true);
```

### 4. Test Suite (`test_database_cleanup.py`)
Comprehensive testing and demonstration script.

**Features:**
- Database state analysis and reporting
- Cleanup simulation (dry-run)
- Before/after comparison
- API endpoint testing framework

**Usage:**
```bash
# Analyze database state
python test_database_cleanup.py

# Run actual cleanup (destructive)
python test_database_cleanup.py --run-cleanup

# Test API endpoints
python test_database_cleanup.py --api-test
```

## Technical Implementation Details

### Database Relationships Handled
The cleanup system properly handles the following relationships:

1. **Dataset Dependencies:**
   - `DatasetAccessLog` → `Dataset`
   - `DatasetDownload` → `Dataset`
   - `DatasetModel` → `Dataset`
   - `DatasetChatSession` → `Dataset`
   - `ChatMessage` → `DatasetChatSession`
   - `DatasetShareAccess` → `Dataset`

2. **Organization Dependencies:**
   - `DatabaseConnector` → `Organization`
   - `Dataset` → `Organization`
   - `User` → `Organization`

### Deletion Order
Critical order of operations to respect foreign key constraints:

1. **For Datasets:**
   ```
   ChatMessage → DatasetChatSession → Other Dataset Relations → Dataset
   ```

2. **For Organizations:**
   ```
   DatabaseConnector → Organization
   ```

### Safety Measures

#### Admin Organization Protection
Organizations are excluded from cleanup if their name contains:
- "admin"
- "system" 
- "default"
- "super"

#### Confirmation Requirements
All destructive operations require explicit confirmation:
- CLI: Interactive prompts or `--force` flag
- API: `confirm=true` parameter

#### Transaction Safety
All operations use database transactions with rollback on errors.

## Security Considerations

### Authentication & Authorization
- All API endpoints require superuser authentication
- Only system administrators can perform cleanup operations

### Audit Trail
- All cleanup operations are logged with timestamps
- Detailed information about deleted entities is captured
- Error logging for troubleshooting

### Data Recovery
- **Important**: This system performs hard deletes, not soft deletes
- Ensure database backups are available before running cleanup
- Consider implementing backup verification before cleanup

## Monitoring & Maintenance

### Regular Health Checks
Recommended to run cleanup statistics regularly:

```bash
# Weekly health check
python database_cleanup.py --stats-only

# Include in monitoring dashboard
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/api/admin/cleanup/stats
```

### Automated Cleanup
For production environments, consider:

```bash
# Monthly automated cleanup with backup
#!/bin/bash
backup_db.sh
python database_cleanup.py --force
```

## Error Handling & Troubleshooting

### Common Issues

1. **Foreign Key Constraint Errors**
   - Check deletion order in code
   - Verify all related models are imported
   - Review database schema changes

2. **Authentication Errors**
   - Verify superuser token is valid
   - Check user permissions in database

3. **Transaction Rollback**
   - Review error logs for specific SQL errors
   - Check database connectivity
   - Verify sufficient disk space

### Logging
All operations include comprehensive logging:
- Info level: Operation progress and results
- Error level: Failures and rollbacks
- Debug level: SQL queries and detailed flow

## Best Practices

### Before Running Cleanup
1. **Backup Database**
   ```bash
   sqlite3 storage/aishare_platform.db ".backup backup_$(date +%Y%m%d_%H%M%S).db"
   ```

2. **Run Statistics First**
   ```bash
   python database_cleanup.py --stats-only
   ```

3. **Test with Dry Run**
   ```bash
   python database_cleanup.py --dry-run
   ```

### Production Deployment
1. Schedule during maintenance windows
2. Monitor database performance during/after cleanup
3. Verify application functionality post-cleanup
4. Keep cleanup logs for audit purposes

### Integration with CI/CD
```yaml
# Example GitHub Action
- name: Database Health Check
  run: |
    python test_database_cleanup.py
    if [ $? -eq 0 ]; then
      echo "Database health check passed"
    else
      echo "Database health issues detected"
      exit 1
    fi
```

## Future Enhancements

### Potential Improvements
1. **Scheduled Cleanup**: Automatic cleanup based on configurable schedules
2. **Soft Delete Recovery**: Option to recover recently deleted items
3. **Granular Permissions**: Role-based access to different cleanup operations
4. **Cleanup Policies**: Configurable rules for what constitutes "orphaned" data
5. **Notification System**: Email alerts for cleanup results
6. **Performance Optimization**: Batch processing for large datasets

### Monitoring Integration
- Prometheus metrics for cleanup operations
- Grafana dashboards for orphaned data tracking
- Alerting for excessive orphaned data accumulation

## API Client Examples

### React Component Example
```typescript
import { adminAPI } from '@/lib/api';

const DatabaseCleanupPanel = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const fetchStats = async () => {
    setLoading(true);
    try {
      const data = await adminAPI.getCleanupStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch cleanup stats:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const runCleanup = async () => {
    if (confirm('Are you sure you want to clean up orphaned data?')) {
      try {
        const result = await adminAPI.cleanupAllOrphanedData(true);
        alert(`Cleanup completed: ${result.message}`);
        fetchStats(); // Refresh stats
      } catch (error) {
        alert('Cleanup failed: ' + error.message);
      }
    }
  };
  
  return (
    <div>
      <button onClick={fetchStats}>Refresh Stats</button>
      <button onClick={runCleanup}>Run Cleanup</button>
      {stats && (
        <div>
          <p>Orphaned Datasets: {stats.orphaned_data.orphaned_datasets.count}</p>
          <p>Empty Organizations: {stats.orphaned_data.empty_organizations.count}</p>
        </div>
      )}
    </div>
  );
};
```

This comprehensive cleanup system provides both command-line and web-based tools for maintaining database integrity while ensuring safety and providing detailed feedback on all operations.