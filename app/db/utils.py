from datetime import datetime, timedelta
from app.db.mongodb import get_database

async def cleanup_old_tokens(days: int = 90):
    """
    Cleanup tokens older than specified days
    Run this periodically to remove stale connections
    """
    db = await get_database()
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.sf_tokens.delete_many({
        "connected_at": {"$lt": cutoff_date}
    })
    
    return {
        "deleted_count": result.deleted_count,
        "cutoff_date": cutoff_date
    }

async def get_token_stats():
    """Get statistics about stored tokens"""
    db = await get_database()
    
    total = await db.sf_tokens.count_documents({})
    
    # Count tokens by age
    now = datetime.utcnow()
    last_week = now - timedelta(days=7)
    last_month = now - timedelta(days=30)
    
    recent = await db.sf_tokens.count_documents({
        "connected_at": {"$gte": last_week}
    })
    
    monthly = await db.sf_tokens.count_documents({
        "connected_at": {"$gte": last_month}
    })
    
    return {
        "total_tokens": total,
        "connected_last_week": recent,
        "connected_last_month": monthly
    }