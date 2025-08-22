"""
GraphQL Schema for DevOps PoC
Main schema definition with project management capabilities
"""
import strawberry
from typing import List, Optional
from strawberry.types import Info
from dataclasses import field as dc_field
from datetime import datetime

from app.models.project import Project, ProjectStats, ProjectCreateInput, ProjectUpdateInput, ProjectFilterInput, ProjectPaginationInput
from app.resolvers.project_resolvers import ProjectQuery, ProjectMutation, ProjectSubscription


@strawberry.type
class Query:
    """Root query type"""
    @strawberry.field(description="Health check endpoint")
    def health(self) -> str:
        return "ok"
    
    @strawberry.field(description="API version information")
    def version(self) -> str:
        return "1.0.0"
    
    @strawberry.field(description="API status information")
    def status(self) -> str:
        return '{"status": "healthy", "service": "devops-poc-api", "version": "1.0.0"}'

    # Project queries
    @strawberry.field(description="Get a single project by ID")
    async def project(self, info: Info, id: str) -> Optional[Project]:
        """Retrieve a project by its ID"""
        cosmos_service = info.context["cosmos_service"]
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
        cosmos_service = info.context["cosmos_service"]
        
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
        cosmos_service = info.context["cosmos_service"]
        
        if cosmos_service is None:
            return ProjectStats(
                total_projects=2,
                status_distribution='{"IN_PROGRESS": 1, "COMPLETED": 1}',
                priority_distribution='{"HIGH": 1, "MEDIUM": 1}',
                team_distribution='{"demo-team": 2}',
                last_updated=datetime.utcnow().isoformat()
            )
        
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


@strawberry.type
class Mutation:
    """Root mutation type"""

    @strawberry.mutation(description="Create a new project")
    async def createProject(self, info: Info, input: ProjectCreateInput) -> Project:
        mutation_resolver = ProjectMutation()
        return await mutation_resolver.create_project(info, input)

    @strawberry.mutation(description="Update an existing project")
    async def updateProject(self, info: Info, id: str, input: ProjectUpdateInput) -> Optional[Project]:
        mutation_resolver = ProjectMutation()
        return await mutation_resolver.update_project(info, id, input)

    @strawberry.mutation(description="Delete a project")
    async def deleteProject(self, info: Info, id: str) -> bool:
        mutation_resolver = ProjectMutation()
        return await mutation_resolver.delete_project(info, id)

@strawberry.type
class Subscription:
    @strawberry.field
    def ping(self) -> str:
        return "pong"


# Create the GraphQL schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription
)


