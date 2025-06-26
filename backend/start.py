#!/usr/bin/env python3
"""
Startup script for AI Share Platform Backend
"""
import uvicorn
from app.core.init_db import init_db

def main():
    """Initialize database and start the server."""
    print("Initializing database...")
    init_db()
    
    print("Starting FastAPI server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main() 