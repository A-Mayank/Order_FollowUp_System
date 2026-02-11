from beanie import Document, Link
from pydantic import Field
from datetime import datetime
from typing import Optional
from enum import Enum

from .order import Order, Sentiment


class MessageType(str, Enum):
    """Message type enum"""
    ORDER_CONFIRMATION = "ORDER_CONFIRMATION"
    PAYMENT_REMINDER_1 = "PAYMENT_REMINDER_1"
    PAYMENT_REMINDER_2 = "PAYMENT_REMINDER_2"
    IN_PROCESS_NOTIFICATION = "IN_PROCESS_NOTIFICATION"
    SHIPPING_NOTIFICATION = "SHIPPING_NOTIFICATION"
    OUT_FOR_DELIVERY_NOTIFICATION = "OUT_FOR_DELIVERY_NOTIFICATION"
    DELIVERY_NOTIFICATION = "DELIVERY_NOTIFICATION"
    PAYMENT_CONFIRMATION = "PAYMENT_CONFIRMATION"
    FEEDBACK_REQUEST = "FEEDBACK_REQUEST"
    CUSTOMER_REPLY = "CUSTOMER_REPLY"


class MessageLog(Document):
    """Log of all WhatsApp messages sent/received"""
    
    order_id: Link[Order] = Field(..., description="Reference to order")
    message_type: MessageType
    message_content: str = Field(..., description="Actual message text sent/received")
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    
    # For incoming messages
    is_incoming: bool = Field(default=False)
    sentiment: Optional[Sentiment] = None
    
    # WhatsApp metadata
    whatsapp_message_id: Optional[str] = None
    
    class Settings:
        name = "message_logs"
        
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "message_type": "ORDER_CONFIRMATION",
                "message_content": "Hi John! Your order #123 has been confirmed.",
                "is_incoming": False
            }
        }
