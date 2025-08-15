#!/usr/bin/env python3
"""
Enhanced Startup script for AI Share Platform Backend with Configuration Validation
"""
import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Initialize database and start the server with configuration validation and enhanced logging."""
    startup_time = datetime.now()
    
    print("=" * 80)
    print("🚀 AI SHARE PLATFORM - BACKEND STARTUP")
    print("=" * 80)
    logger.info(f"⏰ Startup Time: {startup_time.isoformat()}")
    logger.info(f"🌐 Environment: {os.getenv('NODE_ENV', 'development')}")
    logger.info(f"🏠 Host: 0.0.0.0:8000")
    
    # Step 1: Validate configuration
    print("\n🔍 Step 1: Validating configuration...")
    try:
        from app.core.config_validator import validate_configuration
        if not validate_configuration():
            print("\n❌ Configuration validation failed. Cannot start server.")
            print("Please fix the configuration errors above and try again.")
            sys.exit(1)
    except ImportError as e:
        print(f"❌ Failed to import configuration validator: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error during configuration validation: {e}")
        sys.exit(1)
    
    print("\n✅ Configuration validation completed successfully!")
    
    # Step 2: Initialize database
    print("\n💾 Step 2: Initializing database...")
    try:
        from app.core.init_db import init_db
        init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        print(f"⚠️ Database initialization warning: {e}")
        print("The server will start but some features may not work properly")
    
    # Display helpful information
    logger.info("-" * 80)
    logger.info("📚 DOCUMENTATION ENDPOINTS:")
    logger.info("  📖 Swagger UI:  http://localhost:8000/docs")
    logger.info("  🔍 ReDoc:       http://localhost:8000/redoc")
    logger.info("  🏥 Health:      http://localhost:8000/health")
    logger.info("  📊 Root:        http://localhost:8000/")
    logger.info("-" * 80)
    logger.info("👤 DEMO ACCOUNTS:")
    logger.info("  🔑 Admin:       admin@example.com / SuperAdmin123!")
    logger.info("  👨‍💼 TechCorp:     alice@techcorp.com / Password123!")
    logger.info("  👩‍💻 DataAnalytics: bob@dataanalytics.com / Password123!")
    logger.info("=" * 80)
    
    # Step 3: Start the server
    print("\n🌐 Step 3: Starting FastAPI server...")
    print("Server will be available at: http://localhost:8000")
    print("API documentation: http://localhost:8000/docs")
    print("=" * 80)
    
    try:
        import uvicorn
        from main import app
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=["app", "."],
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()