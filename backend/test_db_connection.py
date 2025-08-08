#!/usr/bin/env python3
"""
Test script to debug database connection
"""

import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import settings

print(f"Database URL from settings: {settings.database_url}")
print(f"Postgres user: {settings.postgres_user}")
print(f"Postgres password: {settings.postgres_password}")

# Check environment variables
print(f"\nEnvironment variables:")
print(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'Not set')}")
print(f"POSTGRES_USER: {os.getenv('POSTGRES_USER', 'Not set')}")
print(f"POSTGRES_PASSWORD: {os.getenv('POSTGRES_PASSWORD', 'Not set')}") 