from beanie import Document, Link
from pydantic import Field
from datetime import datetime
from typing import Optional
from enum import Enum

from .user import User


class OrderStatus(str, Enum):
    """Order status enum"""
    CREATED = "CREATED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAID = "PAID"
    IN_PROCESS = "IN_PROCESS"
    SHIPPED = "SHIPPED"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, Enum):
    """Payment status enum"""
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"


class Sentiment(str, Enum):
    """Customer sentiment enum"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    UNKNOWN = "unknown"


class Order(Document):
    """Order model with automation tracking"""
    
    user_id: Link[User] = Field(..., description="Reference to user")
    status: OrderStatus = Field(default=OrderStatus.CREATED)
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    automation_enabled: bool = Field(default=True, description="Whether automation is active")
    sentiment: Sentiment = Field(default=Sentiment.UNKNOWN)
    
    # Product/order details
    product_name: Optional[str] = None
    amount: Optional[float] = None
    
    # Tracking
    tracking_id: Optional[str] = None
    carrier: Optional[str] = None
    
    # Feedback
    feedback_rating: Optional[int] = Field(None, description="Customer rating out of 5")
    feedback_text: Optional[str] = Field(None, description="Customer feedback comments")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    payment_reminder_1_sent_at: Optional[datetime] = None
    payment_reminder_2_sent_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    last_customer_reply_at: Optional[datetime] = None
    
    class Settings:
        name = "orders"
        
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "status": "CREATED",
                "payment_status": "PENDING",
                "automation_enabled": True,
                "product_name": "Premium Widget",
                "amount": 99.99
            }
        }
