"""
Document data models for Cosmos DB.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid

class DocumentBase(BaseModel):
    """Base document model with common fields."""
    originalFileName: str
    displayName: str
    contentType: str
    fileSize: int

class DocumentCreate(DocumentBase):
    """Model for creating a new document."""
    userId: str
    reportId: str
    blobUri: str
    blobName: str
    blobContainer: str
    thumbnailUri: Optional[str] = None
    blobUploadDurationMs: Optional[int] = None
    searchDocumentIds: List[str] = Field(default_factory=list)
    totalPages: int = 1
    searchUploadDurationMs: Optional[int] = None

class DocumentUpdate(BaseModel):
    """Model for updating document information."""
    displayName: Optional[str] = None
    status: Optional[str] = None

class Document(DocumentBase):
    """
    Complete Document model for Cosmos DB.
    Represents the full document structure.
    """
    id: str = Field(default_factory=lambda: f"doc-{uuid.uuid4()}")
    userId: str
    documentId: str = Field(default_factory=lambda: f"doc-{uuid.uuid4()}")
    reportId: str
    schemaVersion: str = Field(default="1.0")
    
    # Storage references
    blobUri: str
    blobName: str
    blobContainer: str
    thumbnailUri: Optional[str] = None
    blobUploadDurationMs: Optional[int] = None
    
    # Azure Search references
    searchDocumentIds: List[str] = Field(default_factory=list)
    totalPages: int = 1
    searchUploadDurationMs: Optional[int] = None
    
    # Timestamps
    uploadedAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    # Status
    status: str = Field(default="active")
    
    # Type discriminator
    type: str = Field(default="document")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "doc-550e8400-e29b-41d4-a716-446655440000",
                "userId": "user-550e8400-e29b-41d4-a716-446655440000",
                "documentId": "doc-550e8400-e29b-41d4-a716-446655440000",
                "reportId": "report-550e8400-e29b-41d4-a716-446655440000",
                "schemaVersion": "1.0",
                "originalFileName": "lab_results_2024.pdf",
                "displayName": "Lab Results - Iron Panel",
                "contentType": "application/pdf",
                "fileSize": 2048576,
                "blobUri": "https://storage.blob.core.windows.net/raw/abc123.pdf",
                "blobName": "abc123_lab_results_2024.pdf",
                "blobContainer": "raw",
                "thumbnailUri": "https://storage.blob.core.windows.net/thumbnails/abc123_thumb.jpg",
                "blobUploadDurationMs": 1250,
                "searchDocumentIds": ["search-page1-id", "search-page2-id"],
                "totalPages": 5,
                "searchUploadDurationMs": 1250,
                "uploadedAt": "2025-01-15T10:30:00Z",
                "status": "active",
                "type": "document"
            }
        }
