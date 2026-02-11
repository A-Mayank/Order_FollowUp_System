import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie, Document
from datetime import datetime
from typing import Optional
from enum import Enum

# Bare minimum models for check
class OrderStatus(str, Enum):
    CREATED = "CREATED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"

class Order(Document):
    status: str
    created_at: datetime
    class Settings:
        name = "orders"

async def check_orders():
    client = AsyncIOMotorClient("")
    await init_beanie(database=client.order_followup_db, document_models=[Order])
    
    all_orders = await Order.find_all().to_list()
    print(f"Total orders in database: {len(all_orders)}")
    
    recent_orders = await Order.find_all().sort(-Order.created_at).limit(5).to_list()
    print(f"Total most recent orders: {len(recent_orders)}")
    for o in recent_orders:
        print(f"ID: {o.id} | Status: {o.status} | Created: {o.created_at}")

if __name__ == "__main__":
    asyncio.run(check_orders())

