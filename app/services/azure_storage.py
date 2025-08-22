"""
Azure Storage Service for DevOps PoC
Implements blob storage operations for API result persistence
"""
from typing import Any, Optional
import json
import logging
from datetime import datetime
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.core.exceptions import ResourceNotFoundError

from config.settings import get_settings

logger = logging.getLogger(__name__)


class AzureStorageService:
    """Real Azure Storage service implementation"""
    
    def __init__(self):
        """Initialize Azure Storage client"""
        settings = get_settings()
        
        self.blob_service_client = BlobServiceClient.from_connection_string(
            settings.STORAGE_CONNECTION_STRING
        )
        
        self.container_name = settings.STORAGE_CONTAINER_NAME
        self.account_name = settings.STORAGE_ACCOUNT_NAME
        
        # Get container reference
        self.container_client = self.blob_service_client.get_container_client(self.container_name)
        
        logger.info(f"Azure Storage service initialized for container: {self.container_name}")
    
    async def test_connection(self) -> bool:
        """Test Azure Storage connectivity"""
        try:
            # Try to get container properties
            properties = self.container_client.get_container_properties()
            logger.info(f"✅ Azure Storage connection successful. Container: {properties.name}")
            return True
        except ResourceNotFoundError:
            # Container doesn't exist, try to create it
            try:
                self.container_client.create_container()
                logger.info(f"✅ Created container: {self.container_name}")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to create container: {e}")
                return False
        except Exception as e:
            logger.error(f"❌ Azure Storage connection failed: {e}")
            return False
    
    async def upload_text(
        self, 
        container_name: str, 
        blob_name: str, 
        data: str
    ) -> dict:
        """Upload text data to blob storage"""
        try:
            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            # Upload the data
            blob_client.upload_blob(data, overwrite=True)
            
            # Get blob properties
            properties = blob_client.get_blob_properties()
            
            result = {
                "container": container_name,
                "blob": blob_name,
                "length": len(data),
                "etag": properties.etag,
                "last_modified": properties.last_modified.isoformat(),
                "url": blob_client.url
            }
            
            logger.info(f"Uploaded blob: {blob_name} ({len(data)} bytes)")
            return result
            
        except Exception as e:
            logger.error(f"Error uploading blob {blob_name}: {e}")
            raise
    
    async def upload_json(
        self, 
        container_name: str, 
        blob_name: str, 
        data: dict
    ) -> dict:
        """Upload JSON data to blob storage"""
        json_string = json.dumps(data, indent=2, default=str)
        return await self.upload_text(container_name, blob_name, json_string)
    
    async def download_text(self, container_name: str, blob_name: str) -> Optional[str]:
        """Download text data from blob storage"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            # Download the blob
            download_stream = blob_client.download_blob()
            content = download_stream.readall().decode('utf-8')
            
            logger.info(f"Downloaded blob: {blob_name}")
            return content
            
        except ResourceNotFoundError:
            logger.info(f"Blob not found: {blob_name}")
            return None
        except Exception as e:
            logger.error(f"Error downloading blob {blob_name}: {e}")
            return None
    
    async def download_json(self, container_name: str, blob_name: str) -> Optional[dict]:
        """Download JSON data from blob storage"""
        content = await self.download_text(container_name, blob_name)
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON from blob {blob_name}: {e}")
                return None
        return None
    
    async def list_blobs(
        self, 
        container_name: str, 
        name_starts_with: Optional[str] = None
    ) -> list:
        """List blobs in a container"""
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            
            blobs = []
            for blob in container_client.list_blobs(name_starts_with=name_starts_with):
                blobs.append({
                    "name": blob.name,
                    "size": blob.size,
                    "last_modified": blob.last_modified.isoformat(),
                    "etag": blob.etag
                })
            
            logger.info(f"Listed {len(blobs)} blobs in container: {container_name}")
            return blobs
            
        except Exception as e:
            logger.error(f"Error listing blobs in container {container_name}: {e}")
            return []
    
    async def delete_blob(self, container_name: str, blob_name: str) -> bool:
        """Delete a blob from storage"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            blob_client.delete_blob()
            
            logger.info(f"Deleted blob: {blob_name}")
            return True
            
        except ResourceNotFoundError:
            logger.info(f"Blob not found for deletion: {blob_name}")
            return False
        except Exception as e:
            logger.error(f"Error deleting blob {blob_name}: {e}")
            return False
    
    async def get_blob_properties(self, container_name: str, blob_name: str) -> Optional[dict]:
        """Get blob properties"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            properties = blob_client.get_blob_properties()
            
            return {
                "name": properties.name,
                "size": properties.size,
                "last_modified": properties.last_modified.isoformat(),
                "etag": properties.etag,
                "content_type": properties.content_settings.content_type,
                "url": blob_client.url
            }
            
        except ResourceNotFoundError:
            logger.info(f"Blob not found: {blob_name}")
            return None
        except Exception as e:
            logger.error(f"Error getting blob properties for {blob_name}: {e}")
            return None
    
    async def store_api_result(
        self, 
        operation: str, 
        data: dict, 
        prefix: str = "api-results"
    ) -> dict:
        """Store API operation result in blob storage"""
        try:
            # Generate blob name with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
            blob_name = f"{prefix}/{operation}-{timestamp}.json"
            
            # Add metadata
            result_data = {
                "operation": operation,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            
            # Upload to blob storage
            result = await self.upload_json(self.container_name, blob_name, result_data)
            
            logger.info(f"Stored API result: {operation} -> {blob_name}")
            return result
            
        except Exception as e:
            logger.error(f"Error storing API result for {operation}: {e}")
            raise


