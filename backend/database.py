import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from models.user import User
from models.order import Order
from models.message_log import MessageLog
from models.alert import Alert


async def init_db():
    """Initialize MongoDB connection with Beanie ODM"""
    
    # Get MongoDB URI from environment
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("MONGODB_DATABASE", "order_followup_db")
    
    # Create Motor client
    client = AsyncIOMotorClient(mongodb_uri)
    
    # Initialize Beanie with document models
    await init_beanie(
        database=client[database_name],
        document_models=[User, Order, MessageLog, Alert]
    )
    
    print(f"Connected to MongoDB: {database_name}")


async def close_db():
    """Close MongoDB connection (called on shutdown)"""
    # Beanie/Motor handles connection pooling automatically
    print("MongoDB connection closed")
