"""
Project model for DevOps PoC
Defines the data structure for project metadata and GraphQL schema
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
import strawberry
from strawberry.scalars import ID


@strawberry.type
class ProjectStats:
    """Project statistics for GraphQL schema"""
    total_projects: int
    status_distribution: str
    priority_distribution: str
    team_distribution: str
    last_updated: str

@strawberry.type
class Project:
    """Project entity for GraphQL schema"""
    id: ID
    name: str
    description: str
    status: str
    owner: str
    team: str
    created_at: datetime
    updated_at: datetime
    tags: List[str]
    priority: str
    estimated_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    budget: Optional[float] = None
    risk_level: str = "LOW"
    dependencies: List[str]


class ProjectCreate(BaseModel):
    """Input model for creating projects"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    status: str = Field(default="PLANNING", pattern="^(PLANNING|IN_PROGRESS|COMPLETED|ON_HOLD|CANCELLED)$")
    owner: str = Field(..., min_length=1)
    team: str = Field(..., min_length=1)
    tags: List[str] = Field(default_factory=list)
    priority: str = Field(default="MEDIUM", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    estimated_completion: Optional[datetime] = None
    budget: Optional[float] = Field(None, ge=0)
    risk_level: str = Field(default="LOW", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    dependencies: List[str] = Field(default_factory=list)


class ProjectUpdate(BaseModel):
    """Input model for updating projects"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    status: Optional[str] = Field(None, pattern="^(PLANNING|IN_PROGRESS|COMPLETED|ON_HOLD|CANCELLED)$")
    owner: Optional[str] = Field(None, min_length=1)
    team: Optional[str] = Field(None, min_length=1)
    tags: Optional[List[str]] = None
    priority: Optional[str] = Field(None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    estimated_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    budget: Optional[float] = Field(None, ge=0)
    risk_level: Optional[str] = Field(None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    dependencies: Optional[List[str]] = None


class ProjectFilter(BaseModel):
    """Filter model for project queries"""
    status: Optional[str] = None
    owner: Optional[str] = None
    team: Optional[str] = None
    priority: Optional[str] = None
    risk_level: Optional[str] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class ProjectPagination(BaseModel):
    """Pagination model for project queries"""
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


# Strawberry input types
@strawberry.input
class ProjectCreateInput:
    name: str
    description: str
    status: str = "PLANNING"
    owner: str
    team: str
    tags: Optional[List[str]] = None
    priority: str = "MEDIUM"
    estimated_completion: Optional[datetime] = None
    budget: Optional[float] = None
    risk_level: str = "LOW"
    dependencies: Optional[List[str]] = None


@strawberry.input
class ProjectUpdateInput:
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    owner: Optional[str] = None
    team: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: Optional[str] = None
    estimated_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    budget: Optional[float] = None
    risk_level: Optional[str] = None
    dependencies: Optional[List[str]] = None


@strawberry.input
class ProjectFilterInput:
    status: Optional[str] = None
    owner: Optional[str] = None
    team: Optional[str] = None
    priority: Optional[str] = None
    risk_level: Optional[str] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


@strawberry.input
class ProjectPaginationInput:
    limit: int = 10
    offset: int = 0
    sort_by: str = "created_at"
    sort_order: str = "desc"


