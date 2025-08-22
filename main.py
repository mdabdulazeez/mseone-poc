"""
DevOps PoC - Main FastAPI Application
Demonstrates: API Development with FastAPI + GraphQL
"""
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
from contextlib import asynccontextmanager
import uvicorn
import logging
from datetime import datetime
import uuid

from config.settings import get_settings
from app.schema.schema import schema
from app.middleware.auth import get_current_user
from app.services.azure_storage import AzureStorageService
from app.services.cosmos_db import CosmosDBService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global services
storage_service = None
cosmos_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    global storage_service, cosmos_service
    
    settings = get_settings()
    logger.info("Initializing Azure services...")
    
    try:
        # Initialize Azure services (PoC Requirement)
        storage_service = AzureStorageService()
        cosmos_service = CosmosDBService()
        
        # Test connections
        await storage_service.test_connection()
        await cosmos_service.test_connection()
        
        logger.info("✅ Azure services initialized successfully")
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        yield
    finally:
        logger.info("Shutting down services...")

# Create FastAPI app with lifecycle
app = FastAPI(
    title="DevOps Platform PoC API",
    version="1.0.0",
    description="GraphQL API demonstrating Azure integration and automation",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GraphQL Router (PoC Requirement: GraphQL APIs)
graphql_app = GraphQLRouter(
    schema,
    context_getter=lambda: {
        "storage_service": storage_service,
        "cosmos_service": cosmos_service
    }
)
app.include_router(graphql_app, prefix="/graphql")

# Health check endpoint (PoC Requirement: Monitoring)
@app.get("/health")
async def health_check():
    """Health check endpoint for container monitoring"""
    try:
        # Test Azure services connectivity
        if storage_service:
            await storage_service.test_connection()
        if cosmos_service:
            await cosmos_service.test_connection()
            
        return {
            "status": "healthy",
            "service": "devops-poc-api",
            "azure_services": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

# API Info endpoint
@app.get("/")
async def root():
    return {
        "message": "DevOps Platform PoC API",
        "graphql_endpoint": "/graphql",
        "documentation": "/docs",
        "health": "/health"
    }

# Protected endpoint example (PoC Requirement: Authentication)
# @app.get("/protected")
# async def protected_endpoint(current_user: dict = Depends(get_current_user)):
#     """Example of protected endpoint with Azure AD authentication"""
#     return {
#         "message": "This is a protected endpoint",
#         "user": current_user.get("preferred_username", "Unknown"),
#         "roles": current_user.get("roles", [])
#     }

# File upload endpoint (PoC Requirement: File Management)
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload file to Azure Blob Storage"""
    try:
        if storage_service:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"{timestamp}-{file.filename}"
            
            # Read file content
            content = await file.read()
            
            # Upload to Azure Storage
            result = await storage_service.upload_text(
                container_name="api-results",
                blob_name=filename,
                data=content.decode('utf-8') if file.content_type and 'text' in file.content_type else str(content)
            )
            
            return {
                "message": "File uploaded successfully",
                "filename": filename,
                "storage_url": result["url"],
                "size": result["length"]
            }
        else:
            raise HTTPException(status_code=500, detail="Storage service not available")
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )