"""
Cosmos DB Service for DevOps PoC
Implements real Cosmos DB operations for project management
"""
from typing import Any, Dict, List, Optional
import json
import logging
from datetime import datetime
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosHttpResponseError

from config.settings import get_settings

logger = logging.getLogger(__name__)


class CosmosDBService:
    """Real Cosmos DB service implementation"""
    
    def __init__(self):
        """Initialize Cosmos DB client"""
        settings = get_settings()
        
        self.client = CosmosClient(
            url=settings.COSMOS_DB_URI,
            credential=settings.COSMOS_DB_KEY
        )
        
        self.database_name = settings.COSMOS_DB_DATABASE
        self.container_name = settings.COSMOS_DB_CONTAINER
        
        # Get database and container references
        self.database = self.client.get_database_client(self.database_name)
        self.container = self.database.get_container_client(self.container_name)
        
        logger.info(f"Cosmos DB service initialized for database: {self.database_name}")
    
    async def test_connection(self) -> bool:
        """Test Cosmos DB connectivity"""
        try:
            # Try to read container properties
            properties = self.container.read()
            logger.info(f"✅ Cosmos DB connection successful. Container: {properties['id']}")
            return True
        except CosmosHttpResponseError as e:
            logger.error(f"❌ Cosmos DB connection failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error testing Cosmos DB: {e}")
            return False
    
    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a project by ID"""
        try:
            response = self.container.read_item(
                item=project_id,
                partition_key=project_id
            )
            logger.info(f"Retrieved project: {project_id}")
            return response
        except CosmosHttpResponseError as e:
            if e.status_code == 404:
                logger.info(f"Project not found: {project_id}")
                return None
            logger.error(f"Error retrieving project {project_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving project {project_id}: {e}")
            return None
    
    async def list_projects(
        self, 
        filter_params: Optional[Dict[str, Any]] = None,
        pagination_params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """List projects with optional filtering and pagination"""
        try:
            # Build query
            query = "SELECT * FROM c"
            parameters = []
            
            # Add filters
            if filter_params:
                conditions = []
                param_count = 0
                
                for key, value in filter_params.items():
                    if value is not None:
                        if key == "tags" and isinstance(value, list):
                            # Handle array contains for tags
                            tag_conditions = []
                            for tag in value:
                                param_count += 1
                                param_name = f"@tag{param_count}"
                                tag_conditions.append(f"ARRAY_CONTAINS(c.{key}, {param_name})")
                                parameters.append({"name": param_name, "value": tag})
                            if tag_conditions:
                                conditions.append(f"({' AND '.join(tag_conditions)})")
                        elif key in ["created_after", "created_before"]:
                            # Handle date comparisons
                            param_count += 1
                            param_name = f"@{key}{param_count}"
                            if key == "created_after":
                                conditions.append(f"c.created_at >= {param_name}")
                            else:
                                conditions.append(f"c.created_at <= {param_name}")
                            parameters.append({"name": param_name, "value": value.isoformat()})
                        else:
                            # Handle simple equality
                            param_count += 1
                            param_name = f"@{key}{param_count}"
                            conditions.append(f"c.{key} = {param_name}")
                            parameters.append({"name": param_name, "value": value})
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            # Add sorting
            if pagination_params and pagination_params.get("sort_by"):
                sort_field = pagination_params["sort_by"]
                sort_order = pagination_params.get("sort_order", "desc").upper()
                query += f" ORDER BY c.{sort_field} {sort_order}"
            
            # Execute query
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            # Apply pagination
            if pagination_params:
                offset = pagination_params.get("offset", 0)
                limit = pagination_params.get("limit", 10)
                items = items[offset:offset + limit]
            
            logger.info(f"Retrieved {len(items)} projects")
            return items
            
        except Exception as e:
            logger.error(f"Error listing projects: {e}")
            return []
    
    async def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project"""
        try:
            # Ensure required fields
            if "id" not in project_data:
                raise ValueError("Project ID is required")
            
            # Ensure datetime fields are properly serialized
            for field, value in project_data.items():
                if isinstance(value, datetime):
                    project_data[field] = value.isoformat()
            
            # Add metadata
            project_data["_ts"] = int(datetime.utcnow().timestamp())
            project_data["_etag"] = None
            
            # Create the item (fix partition key format)
            response = self.container.create_item(
                body=project_data
            )
            
            logger.info(f"Created project: {project_data['id']}")
            return response
            
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            raise
    
    async def update_project(self, project_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing project"""
        try:
            # Get existing project
            existing_project = await self.get_project(project_id)
            if not existing_project:
                raise ValueError(f"Project {project_id} not found")
            
            # Apply updates
            updated_project = {**existing_project, **updates}
            
            # Ensure datetime fields are properly serialized
            for field, value in updated_project.items():
                if isinstance(value, datetime):
                    updated_project[field] = value.isoformat()
            
            updated_project["_ts"] = int(datetime.utcnow().timestamp())
            
            # Update the item
            response = self.container.replace_item(
                item=project_id,
                body=updated_project
            )
            
            logger.info(f"Updated project: {project_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {e}")
            raise
    
    async def delete_project(self, project_id: str) -> bool:
        """Delete a project"""
        try:
            self.container.delete_item(
                item=project_id,
                partition_key=project_id
            )
            
            logger.info(f"Deleted project: {project_id}")
            return True
            
        except CosmosHttpResponseError as e:
            if e.status_code == 404:
                logger.info(f"Project not found for deletion: {project_id}")
                return False
            logger.error(f"Error deleting project {project_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting project {project_id}: {e}")
            return False
    
    async def get_project_stats(self) -> Dict[str, Any]:
        """Get project statistics"""
        try:
            # Count total projects
            total_query = "SELECT VALUE COUNT(1) FROM c"
            total_result = list(self.container.query_items(
                query=total_query,
                enable_cross_partition_query=True
            ))
            total_projects = total_result[0] if total_result else 0
            
            # Count by status
            status_query = "SELECT c.status, COUNT(1) as count FROM c GROUP BY c.status"
            status_results = list(self.container.query_items(
                query=status_query,
                enable_cross_partition_query=True
            ))
            
            # Count by priority
            priority_query = "SELECT c.priority, COUNT(1) as count FROM c GROUP BY c.priority"
            priority_results = list(self.container.query_items(
                query=priority_query,
                enable_cross_partition_query=True
            ))
            
            # Count by team
            team_query = "SELECT c.team, COUNT(1) as count FROM c GROUP BY c.team"
            team_results = list(self.container.query_items(
                query=team_query,
                enable_cross_partition_query=True
            ))
            
            return {
                "total_projects": total_projects,
                "status_distribution": {r["status"]: r["count"] for r in status_results},
                "priority_distribution": {r["priority"]: r["count"] for r in priority_results},
                "team_distribution": {r["team"]: r["count"] for r in team_results},
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting project stats: {e}")
            return {
                "total_projects": 0,
                "status_distribution": {},
                "priority_distribution": {},
                "team_distribution": {},
                "last_updated": datetime.utcnow().isoformat()
            }


