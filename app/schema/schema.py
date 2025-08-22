"""
GraphQL Schema for DevOps PoC
Main schema definition with project management capabilities
"""
import strawberry
from typing import List

from app.models.project import Project
from app.resolvers.project_resolvers import ProjectQuery, ProjectMutation, ProjectSubscription


@strawberry.type
class Query(ProjectQuery):
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


@strawberry.type
class Mutation(ProjectMutation):
    """Root mutation type"""
    @strawberry.field(description="Placeholder mutation field")
    def placeholder_mutation(self) -> str:
        return "placeholder"


@strawberry.type
class Subscription(ProjectSubscription):
    """Root subscription type"""
    @strawberry.field(description="Placeholder subscription field")
    def placeholder_subscription(self) -> str:
        return "placeholder"


# Create the GraphQL schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription
)


