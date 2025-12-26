"""
SearchActivity data models for Cosmos DB.
Tracks search queries, results, and user interactions.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid

class RefinedQuery(BaseModel):
    """Refined query structure from Azure OpenAI."""
    search_phrases: List[str] = Field(default_factory=list)
    search_filters: Dict[str, Any] = Field(default_factory=dict)

class SearchActivityBase(BaseModel):
    """Base search activity model with common fields."""
    userId: str
    searchId: str
    originalQuery: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

class SearchActivityCreate(SearchActivityBase):
    """
    Model for creating a new search activity entry.
    
    Note: resultsDocumentIds stores both blob URIs and document IDs from search results.
    This allows tracking both the storage location and the Cosmos DB document identifier.
    """
    refinedQuery: RefinedQuery
    resultsFound: bool
    resultsDocumentIds: List[str] = Field(
        default_factory=list,
        description="List of document identifiers including blob URIs and document IDs"
    )
    resultNumDocuments: int = 0
    topResultScore: Optional[float] = None
    totalResultsReturned: int = 0
    deviceType: Optional[str] = None
    appVersion: Optional[str] = None
    searchDurationMs: Optional[int] = None

class SearchActivityUpdate(BaseModel):
    """Model for updating search activity (PATCH operations)."""
    userOpenedDocument: Optional[bool] = None
    documentOpenedIds: Optional[List[str]] = None
    timeToClickFirstDocumentMs: Optional[int] = None
    wasAnswerHelpful: Optional[bool] = None

class SearchActivity(SearchActivityBase):
    """
    Complete SearchActivity model for Cosmos DB.
    Tracks the full lifecycle of a search query and user interaction.
    """
    id: str = Field(default_factory=lambda: f"search-{uuid.uuid4()}")
    searchId: str = Field(default_factory=lambda: f"search-{uuid.uuid4()}")
    schemaVersion: str = Field(default="1.0")
    
    # Search query details
    refinedQuery: RefinedQuery
    
    # Search results
    resultsFound: bool
    resultsDocumentIds: List[str] = Field(
        default_factory=list,
        description="List of document identifiers including blob URIs and document IDs"
    )
    resultNumDocuments: int = 0
    topResultScore: Optional[float] = None
    totalResultsReturned: int = 0
    
    # User interaction
    userOpenedDocument: Optional[bool] = None
    documentOpenedIds: List[str] = Field(default_factory=list)
    timeToClickFirstDocumentMs: Optional[int] = None
    wasAnswerHelpful: Optional[bool] = None
    
    # Context
    deviceType: Optional[str] = None
    appVersion: Optional[str] = None
    
    # Performance metrics
    searchDurationMs: Optional[int] = None
    
    # Type discriminator
    type: str = Field(default="search_activity")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "search-550e8400-e29b-41d4-a716-446655440000",
                "userId": "user-550e8400-e29b-41d4-a716-446655440000",
                "searchId": "search-550e8400-e29b-41d4-a716-446655440000",
                "schemaVersion": "1.0",
                "originalQuery": "What are my iron levels?",
                "refinedQuery": {
                    "search_phrases": ["ferritin", "iron", "Fe"],
                    "search_filters": {}
                },
                "timestamp": "2025-01-16T14:20:00Z",
                "resultsFound": True,
                "resultsDocumentIds": ["https://storage.blob.core.windows.net/container/file.pdf", "doc-123"],
                "resultNumDocuments": 5,
                "topResultScore": 0.95,
                "totalResultsReturned": 1,
                "userOpenedDocument": True,
                "documentOpenedIds": ["doc-123"],
                "timeToClickFirstDocumentMs": 2500,
                "wasAnswerHelpful": None,
                "deviceType": "mobile",
                "appVersion": "1.0.0",
                "searchDurationMs": 1250,
                "type": "search_activity"
            }
        }
