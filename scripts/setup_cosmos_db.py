#!/usr/bin/env python3
"""
Cosmos DB Setup Script for DevOps PoC
Creates and configures the database and container for the project management system
"""

import asyncio
import sys
import os
from datetime import datetime
import uuid

# Add the parent directory to the path to import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceExistsError, CosmosHttpResponseError
from config.settings import get_settings

def setup_cosmos_db():
    """Set up Cosmos DB database and container with proper configuration"""
    
    settings = get_settings()
    print(f"🔧 Setting up Cosmos DB: {settings.COSMOS_DB_DATABASE}")
    
    try:
        # Initialize Cosmos client
        client = CosmosClient(
            url=settings.COSMOS_DB_URI,
            credential=settings.COSMOS_DB_KEY
        )
        print("✅ Connected to Cosmos DB account")
        
        # Create database
        try:
            database = client.create_database(
                id=settings.COSMOS_DB_DATABASE,
                offer_throughput=400  # Minimum throughput for cost efficiency
            )
            print(f"✅ Created database: {settings.COSMOS_DB_DATABASE}")
        except CosmosResourceExistsError:
            database = client.get_database_client(settings.COSMOS_DB_DATABASE)
            print(f"✅ Database already exists: {settings.COSMOS_DB_DATABASE}")
        
        # Create container with proper partition key
        try:
            container = database.create_container(
                id=settings.COSMOS_DB_CONTAINER,
                partition_key=PartitionKey(path="/id"),  # Partition by project ID
                offer_throughput=400  # Minimum throughput
            )
            print(f"✅ Created container: {settings.COSMOS_DB_CONTAINER}")
        except CosmosResourceExistsError:
            container = database.get_container_client(settings.COSMOS_DB_CONTAINER)
            print(f"✅ Container already exists: {settings.COSMOS_DB_CONTAINER}")
        
        # Test the configuration with a sample document
        test_project = {
            "id": "test-setup-project",
            "name": "Setup Test Project",
            "description": "Test project created during Cosmos DB setup",
            "status": "PLANNING",
            "owner": "setup-script",
            "team": "devops-team",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "tags": ["setup", "test"],
            "priority": "LOW",
            "risk_level": "LOW",
            "dependencies": [],
            "budget": None,
            "estimated_completion": None,
            "actual_completion": None
        }
        
        # Insert test document
        try:
            response = container.upsert_item(test_project)
            print(f"✅ Test document created successfully: {response['id']}")
            
            # Verify we can read it back
            read_item = container.read_item(
                item=test_project["id"],
                partition_key=test_project["id"]
            )
            print(f"✅ Test document verified: {read_item['name']}")
            
            # Clean up test document
            container.delete_item(
                item=test_project["id"],
                partition_key=test_project["id"]
            )
            print("✅ Test document cleaned up")
            
        except Exception as e:
            print(f"❌ Test document operation failed: {e}")
            return False
        
        print("\n🎉 Cosmos DB setup completed successfully!")
        print(f"Database: {settings.COSMOS_DB_DATABASE}")
        print(f"Container: {settings.COSMOS_DB_CONTAINER}")
        print(f"Partition Key: /id")
        return True
        
    except Exception as e:
        print(f"❌ Cosmos DB setup failed: {e}")
        return False


def create_sample_data():
    """Create sample project data for testing"""
    
    settings = get_settings()
    
    try:
        client = CosmosClient(
            url=settings.COSMOS_DB_URI,
            credential=settings.COSMOS_DB_KEY
        )
        
        database = client.get_database_client(settings.COSMOS_DB_DATABASE)
        container = database.get_container_client(settings.COSMOS_DB_CONTAINER)
        
        sample_projects = [
            {
                "id": str(uuid.uuid4()),
                "name": "E-Commerce Platform Migration",
                "description": "Migrate legacy e-commerce platform to cloud-native architecture",
                "status": "IN_PROGRESS",
                "owner": "sarah.wilson@company.com",
                "team": "platform-team",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "tags": ["migration", "e-commerce", "cloud"],
                "priority": "HIGH",
                "risk_level": "MEDIUM",
                "dependencies": ["database-migration", "security-audit"],
                "budget": 75000.0,
                "estimated_completion": "2024-03-15T00:00:00Z",
                "actual_completion": None
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Mobile App API Development",
                "description": "Create RESTful API for new mobile application",
                "status": "PLANNING",
                "owner": "john.doe@company.com",
                "team": "mobile-team",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "tags": ["api", "mobile", "backend"],
                "priority": "MEDIUM",
                "risk_level": "LOW",
                "dependencies": ["requirements-gathering"],
                "budget": 50000.0,
                "estimated_completion": "2024-02-28T00:00:00Z",
                "actual_completion": None
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Security Audit Implementation",
                "description": "Implement recommendations from annual security audit",
                "status": "COMPLETED",
                "owner": "mike.security@company.com",
                "team": "security-team",
                "created_at": (datetime.utcnow().replace(month=1)).isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "tags": ["security", "compliance", "audit"],
                "priority": "CRITICAL",
                "risk_level": "HIGH",
                "dependencies": [],
                "budget": 25000.0,
                "estimated_completion": "2024-01-31T00:00:00Z",
                "actual_completion": datetime.utcnow().isoformat()
            }
        ]
        
        print("\n📊 Creating sample project data...")
        
        for project in sample_projects:
            try:
                container.create_item(project)
                print(f"✅ Created project: {project['name']}")
            except CosmosResourceExistsError:
                print(f"⚠️ Project already exists: {project['name']}")
        
        print(f"✅ Sample data created successfully! ({len(sample_projects)} projects)")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create sample data: {e}")
        return False


if __name__ == "__main__":
    print("🚀 DevOps PoC - Cosmos DB Setup")
    print("=" * 50)
    
    # Setup database and container
    if setup_cosmos_db():
        # Ask if user wants sample data
        response = input("\n📊 Would you like to create sample project data? (y/n): ").lower()
        if response in ['y', 'yes']:
            create_sample_data()
    
    print("\n🎯 Setup complete! You can now test your GraphQL API.")
    print("💡 Try: curl -X POST http://localhost:8000/graphql -H \"Content-Type: application/json\" -d '{\"query\": \"{ projects { id name status owner team } }\"}'")
