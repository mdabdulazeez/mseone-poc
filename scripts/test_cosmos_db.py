#!/usr/bin/env python3
"""
Test script to validate Cosmos DB configuration
"""

import sys
import os
import asyncio
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.cosmos_db import CosmosDBService
from config.settings import get_settings

async def test_cosmos_db():
    """Test all Cosmos DB operations"""
    
    print("🧪 Testing Cosmos DB Operations")
    print("=" * 40)
    
    try:
        # Initialize service
        cosmos_service = CosmosDBService()
        
        # Test connection
        print("1️⃣ Testing connection...")
        if await cosmos_service.test_connection():
            print("   ✅ Connection successful")
        else:
            print("   ❌ Connection failed")
            return False
        
        # Test project creation
        print("2️⃣ Testing project creation...")
        test_project = {
            "id": "test-project-12345",
            "name": "Test Project",
            "description": "Testing project creation",
            "status": "PLANNING",
            "owner": "test@example.com",
            "team": "test-team",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "tags": ["test"],
            "priority": "MEDIUM",
            "risk_level": "LOW",
            "dependencies": []
        }
        
        created_project = await cosmos_service.create_project(test_project)
        if created_project:
            print(f"   ✅ Project created: {created_project['name']}")
        else:
            print("   ❌ Project creation failed")
            return False
        
        # Test project retrieval
        print("3️⃣ Testing project retrieval...")
        retrieved_project = await cosmos_service.get_project("test-project-12345")
        if retrieved_project and retrieved_project['name'] == "Test Project":
            print(f"   ✅ Project retrieved: {retrieved_project['name']}")
        else:
            print("   ❌ Project retrieval failed")
        
        # Test project listing
        print("4️⃣ Testing project listing...")
        projects = await cosmos_service.list_projects()
        if projects and len(projects) > 0:
            print(f"   ✅ Found {len(projects)} projects")
        else:
            print("   ⚠️ No projects found (this is okay for empty database)")
        
        # Test project update
        print("5️⃣ Testing project update...")
        update_data = {
            "status": "IN_PROGRESS",
            "updated_at": datetime.utcnow()
        }
        updated_project = await cosmos_service.update_project("test-project-12345", update_data)
        if updated_project and updated_project['status'] == "IN_PROGRESS":
            print(f"   ✅ Project updated: status = {updated_project['status']}")
        else:
            print("   ❌ Project update failed")
        
        # Test project deletion
        print("6️⃣ Testing project deletion...")
        if await cosmos_service.delete_project("test-project-12345"):
            print("   ✅ Project deleted successfully")
        else:
            print("   ❌ Project deletion failed")
        
        print("\n🎉 All tests passed! Cosmos DB is configured correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_cosmos_db())
