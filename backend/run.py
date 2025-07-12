#!/usr/bin/env python3
"""
Startup script for Visioneers Marketplace Backend
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("DEBUG", "True").lower() == "true"
    
    print(f"Starting Visioneers Marketplace Backend...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug: {reload}")
    print(f"API Docs: http://{host}:{port}/docs")
    print(f"Health Check: http://{host}:{port}/health")
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    ) 