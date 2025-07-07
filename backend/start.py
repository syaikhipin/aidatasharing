#!/usr/bin/env python3
"""
Enhanced Startup script for AI Share Platform Backend
"""
import os
import uvicorn
import logging
from datetime import datetime
from app.core.init_db import init_db

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Initialize database and start the server with enhanced logging."""
    startup_time = datetime.now()
    
    print("=" * 80)
    print("🚀 AI SHARE PLATFORM - BACKEND STARTUP")
    print("=" * 80)
    logger.info(f"⏰ Startup Time: {startup_time.isoformat()}")
    logger.info(f"🌐 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"🏠 Host: 0.0.0.0:8000")
    
    try:
        logger.info("💾 Initializing database...")
        init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    logger.info("-" * 80)
    logger.info("📚 DOCUMENTATION ENDPOINTS:")
    logger.info("  📖 Swagger UI:  http://localhost:8000/docs")
    logger.info("  🔍 ReDoc:       http://localhost:8000/redoc")
    logger.info("  🏥 Health:      http://localhost:8000/health")
    logger.info("  📊 Root:        http://localhost:8000/")
    logger.info("=" * 80)
    logger.info("🚀 Starting FastAPI server...")
    
    # Start the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main() 