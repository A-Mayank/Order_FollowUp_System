import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def cleanup_database():
    uri = ""
    db_name = "order_followup_db"
    
    print(f"🧹 Connecting to {db_name}...")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    collections = await db.list_collection_names()
    print(f"Found collections: {collections}")
    
    for collection_name in collections:
        # Don't drop system collections if any
        if collection_name.startswith("system."):
            continue
            
        print(f"🗑️ Clearing collection: {collection_name}...")
        result = await db[collection_name].delete_many({})
        print(f"✅ Deleted {result.deleted_count} documents from {collection_name}")
    
    print("\n✨ Database cleared successfully! Ready for your demo.")

if __name__ == "__main__":
    asyncio.run(cleanup_database())

