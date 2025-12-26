"""
User data models for Cosmos DB.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
import uuid


class UserSettings(BaseModel):
    """User settings model - expandable for future features."""
    pass


class UserBase(BaseModel):
    """Base user model with common fields."""
    email: EmailStr
    firstName: str
    lastName: str


class UserCreate(UserBase):
    """Model for creating a new user."""
    pass


class UserUpdate(BaseModel):
    """Model for updating user information."""
    email: Optional[EmailStr] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class User(UserBase):
    """
    Complete User model for Cosmos DB.
    Represents the full user document structure.
    """
    id: str = Field(default_factory=lambda: f"user-{uuid.uuid4()}")
    userId: str = Field(default_factory=lambda: f"user-{uuid.uuid4()}")
    schemaVersion: str = Field(default="1.0")
    createdAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updatedAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    settings: Dict[str, Any] = Field(default_factory=dict)
    type: str = Field(default="user")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "user-550e8400-e29b-41d4-a716-446655440000",
                "userId": "user-550e8400-e29b-41d4-a716-446655440000",
                "schemaVersion": "1.0",
                "email": "user@example.com",
                "firstName": "John",
                "lastName": "Doe",
                "createdAt": "2025-01-01T00:00:00Z",
                "updatedAt": "2025-01-15T12:30:00Z",
                "settings": {},
                "type": "user"
            }
        }
