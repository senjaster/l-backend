#!/usr/bin/env python3
"""CLI utility to add inspectors to the database"""
import asyncio
import asyncpg
import sys
from pathlib import Path
from getpass import getpass

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.services.auth import AuthService


async def add_inspector(full_name: str, username: str, password: str):
    """Add a new inspector to the database"""
    auth_service = AuthService()
    
    # Hash the password
    password_hash = auth_service.hash_password(password)
    
    # Connect to database
    conn = await asyncpg.connect(settings.get_database_url())
    try:
        # Check if username already exists
        existing = await conn.fetchval(
            "SELECT id FROM lesiv.inspector WHERE username = $1",
            username
        )
        
        if existing:
            print(f"❌ Error: Username '{username}' already exists (ID: {existing})")
            return False
        
        # Insert new inspector
        inspector_id = await conn.fetchval(
            """
            INSERT INTO lesiv.inspector (full_name, username, password_hash)
            VALUES ($1, $2, $3)
            RETURNING id
            """,
            full_name,
            username,
            password_hash
        )
        
        print(f"✅ Successfully added inspector:")
        print(f"   ID: {inspector_id}")
        print(f"   Full Name: {full_name}")
        print(f"   Username: {username}")
        return True
        
    finally:
        await conn.close()


async def list_inspectors():
    """List all inspectors in the database"""
    conn = await asyncpg.connect(settings.get_database_url())
    try:
        rows = await conn.fetch(
            """
            SELECT id, full_name, username, server_modified_at
            FROM lesiv.inspector
            ORDER BY id
            """
        )
        
        if not rows:
            print("No inspectors found in database.")
            return
        
        print(f"\n{'ID':<5} {'Username':<20} {'Full Name':<30} {'Modified At'}")
        print("-" * 85)
        for row in rows:
            print(f"{row['id']:<5} {row['username']:<20} {row['full_name']:<30} {row['server_modified_at']}")
        print()
        
    finally:
        await conn.close()


def main():
    """Main CLI entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        # List all inspectors
        asyncio.run(list_inspectors())
        return
    
    print("=== Add New Inspector ===\n")
    
    # Get inspector details
    full_name = input("Full Name: ").strip()
    if not full_name:
        print("❌ Error: Full name is required")
        sys.exit(1)
    
    username = input("Username: ").strip()
    if not username:
        print("❌ Error: Username is required")
        sys.exit(1)
    
    # Get password securely
    password = getpass("Password: ")
    if not password:
        print("❌ Error: Password is required")
        sys.exit(1)
    
    password_confirm = getpass("Confirm Password: ")
    if password != password_confirm:
        print("❌ Error: Passwords do not match")
        sys.exit(1)
    
    # Add inspector
    success = asyncio.run(add_inspector(full_name, username, password))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
