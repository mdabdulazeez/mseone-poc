"""
Project GraphQL resolvers for DevOps PoC
Implements CRUD operations, filtering, and pagination
"""
from typing import List, Optional
from datetime import datetime
import uuid
import logging
import strawberry
from strawberry.types import Info

from app.models.project import (
    Project, ProjectStats, ProjectCreateInput, ProjectUpdateInput, 
    ProjectFilterInput, ProjectPaginationInput
)
from app.services.cosmos_db import CosmosDBService
from app.services.azure_storage import AzureStorageService

logger = logging.getLogger(__name__)


class ProjectQuery:
    """Query resolvers for projects"""
    
    @strawberry.field(description="Get a single project by ID")
    async def project(self, info: Info, id: str) -> Optional[Project]:
        """Retrieve a project by its ID"""
        cosmos_service: CosmosDBService = info.context["cosmos_service"]
        if cosmos_service is None:
            # Return mock data for demo mode
            return Project(
                id=id,
                name="Demo Project",
                description="This is a demo project returned when Cosmos DB is not available",
                status="DEMO",
                owner="demo-user",
                team="demo-team",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                tags=["demo", "testing"],
                priority="MEDIUM",
                risk_level="LOW",
                dependencies=[]
            )
        
        project_data = await cosmos_service.get_project(id)
        if project_data:
            return Project(**project_data)
        return None
    
    @strawberry.field(description="List projects with filtering and pagination")
    async def projects(
        self, 
        info: Info,
        filter: Optional[ProjectFilterInput] = None,
        pagination: Optional[ProjectPaginationInput] = None
    ) -> List[Project]:
        """List projects with optional filtering and pagination"""
        cosmos_service: CosmosDBService = info.context["cosmos_service"]
        
        if cosmos_service is None:
            # Return mock data for demo mode
            return [
                Project(
                    id="demo-1",
                    name="Demo Project 1",
                    description="First demo project",
                    status="IN_PROGRESS",
                    owner="demo-user-1",
                    team="demo-team",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    tags=["demo", "testing"],
                    priority="HIGH",
                    risk_level="LOW",
                    dependencies=[]
                ),
                Project(
                    id="demo-2",
                    name="Demo Project 2",
                    description="Second demo project",
                    status="COMPLETED",
                    owner="demo-user-2",
                    team="demo-team",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    tags=["demo", "completed"],
                    priority="MEDIUM",
                    risk_level="MEDIUM",
                    dependencies=[]
                )
            ]
        
        # Apply filters
        filter_params = {}
        if filter:
            if filter.status:
                filter_params["status"] = filter.status
            if filter.owner:
                filter_params["owner"] = filter.owner
            if filter.team:
                filter_params["team"] = filter.team
            if filter.priority:
                filter_params["priority"] = filter.priority
            if filter.risk_level:
                filter_params["risk_level"] = filter.risk_level
            if filter.tags:
                filter_params["tags"] = filter.tags
            if filter.created_after:
                filter_params["created_after"] = filter.created_after
            if filter.created_before:
                filter_params["created_before"] = filter.created_before
        
        # Apply pagination
        pagination_params = {}
        if pagination:
            pagination_params["limit"] = pagination.limit
            pagination_params["offset"] = pagination.offset
            pagination_params["sort_by"] = pagination.sort_by
            pagination_params["sort_order"] = pagination.sort_order
        
        projects_data = await cosmos_service.list_projects(
            filter_params=filter_params,
            pagination_params=pagination_params
        )
        
        return [Project(**project_data) for project_data in projects_data]
    
    @strawberry.field(description="Get project statistics")
    async def project_stats(self, info: Info) -> ProjectStats:
        """Get aggregated project statistics"""
        cosmos_service: CosmosDBService = info.context["cosmos_service"]
        
        # Get all projects for statistics
        all_projects = await cosmos_service.list_projects()
        
        total_projects = len(all_projects)
        status_counts = {}
        priority_counts = {}
        team_counts = {}
        
        for project in all_projects:
            # Count by status
            status = project.get("status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count by priority
            priority = project.get("priority", "UNKNOWN")
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            # Count by team
            team = project.get("team", "UNKNOWN")
            team_counts[team] = team_counts.get(team, 0) + 1
        
        return ProjectStats(
            total_projects=total_projects,
            status_distribution=str(status_counts),
            priority_distribution=str(priority_counts),
            team_distribution=str(team_counts),
            last_updated=datetime.utcnow().isoformat()
        )


class ProjectMutation:
    """Mutation resolvers for projects"""
    
    async def create_project(
        self,
        info: Info,
        input: ProjectCreateInput
    ) -> Project:
        """Create a new project"""
        cosmos_service: CosmosDBService = info.context["cosmos_service"]
        storage_service: AzureStorageService = info.context["storage_service"]
        
        # Generate project ID
        project_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        if cosmos_service is None:
            # Return mock created project for demo mode
            return Project(
                id=project_id,
                name=input.name,
                description=input.description,
                status=input.status,
                owner=input.owner,
                team=input.team,
                created_at=now,
                updated_at=now,
                tags=input.tags or [],
                priority=input.priority,
                estimated_completion=input.estimated_completion,
                budget=input.budget,
                risk_level=input.risk_level,
                dependencies=input.dependencies or []
            )
        
        # Create project document
        project_data = {
            "id": project_id,
            "name": input.name,
            "description": input.description,
            "status": input.status,
            "owner": input.owner,
            "team": input.team,
            "created_at": now,
            "updated_at": now,
            "tags": input.tags,
            "priority": input.priority,
            "estimated_completion": input.estimated_completion,
            "budget": input.budget,
            "risk_level": input.risk_level,
            "dependencies": input.dependencies
        }
        
        # Save to Cosmos DB (with error handling for demo mode)
        try:
            created_project = await cosmos_service.create_project(project_data)
        except Exception as e:
            logger.warning(f"Cosmos DB error (using demo mode): {e}")
            # Return demo project instead of failing
            return Project(
                id=project_id,
                name=input.name,
                description=input.description,
                status=input.status,
                owner=input.owner,
                team=input.team,
                created_at=now,
                updated_at=now,
                tags=input.tags or [],
                priority=input.priority,
                estimated_completion=input.estimated_completion,
                budget=input.budget,
                risk_level=input.risk_level,
                dependencies=input.dependencies or []
            )

        # Store API result in Azure Blob Storage (if available)
        if storage_service is not None:
            try:
                result_data = {
                    "operation": "create_project",
                    "project_id": project_id,
                    "timestamp": now.isoformat(),
                    "user": input.owner,
                    "result": "success"
                }

                await storage_service.upload_text(
                    container_name="api-results",
                    blob_name=f"project-creation-{project_id}-{now.strftime('%Y%m%d-%H%M%S')}.json",
                    data=str(result_data)
                )
            except Exception as e:
                logger.warning(f"Failed to store API result: {e}")
        
        # Filter out Cosmos DB internal fields before creating Project object
        clean_data = {k: v for k, v in created_project.items() 
                     if not k.startswith('_') and k not in ['ttl', 'pk']}
        return Project(**clean_data)
    
    async def update_project(
        self, 
        info: Info, 
        id: str, 
        input: ProjectUpdateInput
    ) -> Optional[Project]:
        """Update an existing project"""
        cosmos_service: CosmosDBService = info.context["cosmos_service"]
        storage_service: AzureStorageService = info.context["storage_service"]
        
        if cosmos_service is None:
            # Return mock updated project for demo mode
            return Project(
                id=id,
                name=input.name or "Updated Demo Project",
                description=input.description or "Updated demo project",
                status=input.status or "IN_PROGRESS",
                owner=input.owner or "demo-user",
                team=input.team or "demo-team",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                tags=input.tags or ["demo", "updated"],
                priority=input.priority or "MEDIUM",
                estimated_completion=input.estimated_completion,
                actual_completion=input.actual_completion,
                budget=input.budget,
                risk_level=input.risk_level or "LOW",
                dependencies=input.dependencies or []
            )
        
        # Get existing project
        existing_project = await cosmos_service.get_project(id)
        if not existing_project:
            return None
        
        # Prepare update data
        update_data = {}
        for field, value in input.__dict__.items():
            if value is not None:
                update_data[field] = value
        
        # Add updated timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        # Update in Cosmos DB
        updated_project = await cosmos_service.update_project(id, update_data)
        
        # Store API result in Azure Blob Storage (if available)
        if storage_service is not None:
            try:
                result_data = {
                    "operation": "update_project",
                    "project_id": id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "changes": update_data,
                    "result": "success"
                }

                await storage_service.upload_text(
                    container_name="api-results",
                    blob_name=f"project-update-{id}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.json",
                    data=str(result_data)
                )
            except Exception as e:
                logger.warning(f"Failed to store API result: {e}")
        
        # Filter out Cosmos DB internal fields before creating Project object  
        clean_data = {k: v for k, v in updated_project.items() 
                     if not k.startswith('_') and k not in ['ttl', 'pk']}
        return Project(**clean_data)
    
    async def delete_project(self, info: Info, id: str) -> bool:
        """Delete a project"""
        cosmos_service: CosmosDBService = info.context["cosmos_service"]
        storage_service: AzureStorageService = info.context["storage_service"]
        
        if cosmos_service is None:
            # Return success for demo mode
            return True
        
        # Delete from Cosmos DB
        success = await cosmos_service.delete_project(id)
        
        if success and storage_service is not None:
            try:
                # Store API result in Azure Blob Storage
                result_data = {
                    "operation": "delete_project",
                    "project_id": id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "result": "success"
                }
                
                await storage_service.upload_text(
                    container_name="api-results",
                    blob_name=f"project-deletion-{id}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.json",
                    data=str(result_data)
                )
            except Exception as e:
                logger.warning(f"Failed to store API result: {e}")
        
        return success


class ProjectSubscription:
    """Subscription resolvers for real-time project updates"""
    
    @strawberry.field(description="Subscribe to project updates")
    def project_updated(self, info: Info) -> Project:
        """Subscribe to real-time project updates"""
        # This is a placeholder for real-time subscriptions
        # In a real implementation, you'd use WebSockets or Azure SignalR
        pass


# Export the resolver classes
__all__ = ["ProjectQuery", "ProjectMutation", "ProjectSubscription"]
