#!/usr/bin/env python3
"""
Script to create all database tables using SQLAlchemy models
This will create the tables that your FastAPI app expects.
"""

import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import engine, Base
from app.models.user import User
from app.models.product import Product
from app.models.order import Order
from app.models.conversation import Conversation

def create_tables():
    """Create all database tables"""
    try:
        print("🔧 Creating database tables...")
        print(f"📡 Connecting to database: {engine.url}")
        
        # Import all models to ensure they're registered with Base
        # (The imports above should handle this, but let's be explicit)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ All tables created successfully!")
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n📋 Created tables: {', '.join(tables)}")
        
        # Show users table structure
        if 'users' in tables:
            print("\n📊 Users table structure:")
            columns = inspector.get_columns('users')
            for column in columns:
                print(f"  {column['name']}: {column['type']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Setting up Visioneers Marketplace database...")
    success = create_tables()
    
    if success:
        print("\n🎉 Database setup complete! You can now start your backend.")
    else:
        print("\n💥 Database setup failed.") 