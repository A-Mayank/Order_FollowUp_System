from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional


class User(Document):
    """User model for storing customer information"""
    
    name: str = Field(..., description="Customer name")
    whatsapp_number: str = Field(..., description="WhatsApp number with country code")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "users"  # MongoDB collection name
        
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "whatsapp_number": "+1234567890"
            }
        }
