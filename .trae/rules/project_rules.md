
# AI-Share Platform Project Rules

## Environment Management
- **Primary Environment**: Always use `ai-share` conda environment for development/testing
- **MindsDB Environment**: Use separate `mindsdb-server` conda environment for MindsDB
- **Service Management**: Never auto-restart/start/stop services - always manual control

## MindsDB Rules
- **Connection**: Always use MindsDB connection platform, never direct API
- **SQL First**: Use SQL for all model operations (CREATE MODEL, predictions, etc.)
- **Documentation**: Always refer to official MindsDB docs before implementation

## File Organization
```
project-root/
├── logs/                    # Main logs folder
│   ├── mindsdb/            # MindsDB operations
│   ├── test/               # Test outputs  
│   └── application/        # App logs
├── backend/.env
└── frontend/.env
```

## Configuration
- **Backend**: `.env` in backend root
- **Frontend**: `.env` in frontend root  
- **Unified**: Single config approach, separate files

## Database Changes Protocol
1. Update main schema
2. Update `init.sql` scripts
3. Create migration scripts (`YYYY-MM-DD_description.sql`)
4. Update documentation

## Quick Commands
```bash
# Environment
conda activate ai-share
conda activate mindsdb-server  # when needed

# Logs setup
mkdir -p logs/{mindsdb,test,application}

# MindsDB SQL example
CREATE MODEL my_model
FROM my_datasource
(SELECT * FROM my_table)
PREDICT target_column;
```

## Key Rules Summary
✅ Use `ai-share` environment  
✅ MindsDB connection platform only  
✅ SQL for all MindsDB operations  
✅ Manual service management  
✅ Main `logs/` directory  
✅ Separate `.env` files  
✅ Always check MindsDB docs first
