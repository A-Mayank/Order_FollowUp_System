from beanie import Document, Link
from pydantic import Field
from datetime import datetime
from typing import Optional
from enum import Enum

from .order import Order


class AlertReason(str, Enum):
    """Alert reason enum"""
    NEGATIVE_SENTIMENT = "NEGATIVE_SENTIMENT"
    NO_CUSTOMER_RESPONSE = "NO_CUSTOMER_RESPONSE"
    PAYMENT_OVERDUE = "PAYMENT_OVERDUE"
    DELIVERY_DELAYED = "DELIVERY_DELAYED"
    CANCELLATION_REQUEST = "CANCELLATION_REQUEST"


class Alert(Document):
    """Admin alerts for orders requiring attention"""
    
    order_id: Link[Order] = Field(..., description="Reference to order")
    reason: AlertReason
    description: str = Field(..., description="Human-readable alert description")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = Field(default=False)
    resolved_at: Optional[datetime] = None
    
    class Settings:
        name = "alerts"
        
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "reason": "NEGATIVE_SENTIMENT",
                "description": "Customer expressed dissatisfaction in recent message",
                "resolved": False
            }
        }
