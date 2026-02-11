# app/db/mongodb.py
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from app.core.config import settings

class Database:
    """MongoDB database manager"""
    client: Optional[AsyncIOMotorClient] = None
    
    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Get database instance"""
        if self.client is None:
            raise RuntimeError("Database not connected. Call connect_db() first.")
        return self.client[settings.MONGODB_DB_NAME]

# Global database instance
database = Database()

async def connect_db():
    """
    Connect to MongoDB on application startup
    Creates indexes for commonly queried fields
    """
    try:
        database.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            maxPoolSize=10,
            minPoolSize=1,
            serverSelectionTimeoutMS=5000
        )
        
        # Ping to verify connection
        await database.client.admin.command('ping')
        
        # Create indexes for better query performance
        db = database.db
        
        # Index on sf_user_id for quick token lookups
        await db.sf_tokens.create_index("sf_user_id", unique=True)
        
        # Index on connected_at for cleanup queries
        await db.sf_tokens.create_index("connected_at")
        
        print(f"✅ Connected to MongoDB: {settings.MONGODB_DB_NAME}")
        
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        raise

async def close_db():
    """Close MongoDB connection on application shutdown"""
    if database.client:
        database.client.close()
        print("❌ Closed MongoDB connection")

async def get_database() -> AsyncIOMotorDatabase:
    """
    Dependency for FastAPI routes to get database instance
    
    Usage:
        @app.get("/example")
        async def example(db = Depends(get_database)):
            await db.collection.find_one(...)
    """
    return database.db