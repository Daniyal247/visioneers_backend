#!/usr/bin/env python3
"""
Script to add missing columns to the users table
This preserves all existing user data.
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os

# Database connection parameters
DB_HOST = "visioneers_postgres_dev"  # Changed from "localhost" to Docker container name
DB_PORT = "5432"  # Changed from "5434" to default PostgreSQL port
DB_NAME = "visioneers_marketplace_dev"
DB_USER = "visioneers_user"
DB_PASSWORD = "visioneers_password"

def add_missing_columns():
    """Add missing columns to users table"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('email_verification_token', 'email_token_expires_at')
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # Add missing columns
        if 'email_verification_token' not in existing_columns:
            print("Adding email_verification_token column...")
            cursor.execute("ALTER TABLE users ADD COLUMN email_verification_token VARCHAR")
            print("✓ email_verification_token column added")
        else:
            print("✓ email_verification_token column already exists")
            
        if 'email_token_expires_at' not in existing_columns:
            print("Adding email_token_expires_at column...")
            cursor.execute("ALTER TABLE users ADD COLUMN email_token_expires_at TIMESTAMP")
            print("✓ email_token_expires_at column added")
        else:
            print("✓ email_token_expires_at column already exists")
        
        # Verify the table structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """)
        
        print("\nCurrent users table structure:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]}")
        
        cursor.close()
        conn.close()
        print("\n✅ Database schema updated successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔧 Adding missing columns to users table...")
    success = add_missing_columns()
    
    if success:
        print("\n🎉 All done! You can now restart your backend.")
    else:
        print("\n💥 Failed to update database schema.") 