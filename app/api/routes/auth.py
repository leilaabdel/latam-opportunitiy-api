# app/api/routes/auth.py - Update login and callback
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from app.core.salesforce import sf_oauth
from app.db.mongodb import get_database

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/login")
async def salesforce_login():
    """Initiate Salesforce OAuth flow with PKCE"""
    auth_url, state = sf_oauth.get_auth_url()  # Returns tuple (url, state)
    return RedirectResponse(url=auth_url)

@router.get("/callback")
async def salesforce_callback(
    code: str = Query(..., description="Authorization code from Salesforce"),
    state: str = Query(..., description="State parameter"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """OAuth callback with PKCE"""
    try:
        # Exchange code for tokens (includes PKCE verification)
        tokens = sf_oauth.exchange_code(code, state)
        
        # Extract Salesforce user ID
        sf_user_id = tokens.get('id', '').split('/')[-1]
        
        if not sf_user_id:
            raise HTTPException(status_code=400, detail="Could not extract user ID")
        
        # Encrypt and store refresh token
        encrypted_refresh = sf_oauth.encrypt(tokens['refresh_token'])
        
        await db.sf_tokens.update_one(
            {'sf_user_id': sf_user_id},
            {
                '$set': {
                    'refresh_token': encrypted_refresh,
                    'instance_url': tokens['instance_url'],
                    'connected_at': datetime.utcnow(),
                    'salesforce_org_id': tokens.get('id', '').split('/')[-2]
                }
            },
            upsert=True
        )
        
        return HTMLResponse(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Connected to Salesforce</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }}
                    .container {{
                        background: white;
                        padding: 3rem;
                        border-radius: 12px;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                        text-align: center;
                        max-width: 400px;
                    }}
                    h1 {{ color: #2d3748; margin-bottom: 1rem; }}
                    .success-icon {{ font-size: 4rem; margin-bottom: 1rem; }}
                    .user-id {{
                        background: #f7fafc;
                        padding: 0.75rem;
                        border-radius: 6px;
                        font-family: monospace;
                        font-size: 0.9rem;
                        color: #2d3748;
                        word-break: break-all;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="success-icon">✅</div>
                    <h1>Connected to Salesforce!</h1>
                    <div class="user-id">
                        <strong>User ID:</strong><br>
                        {sf_user_id}
                    </div>
                </div>
            </body>
            </html>
        """)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth failed: {str(e)}")

@router.get("/status/{sf_user_id}")
async def check_connection_status(
    sf_user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Check if a user has connected their Salesforce account
    
    Args:
        sf_user_id: Salesforce user ID
        db: Database instance
        
    Returns:
        Connection status and details
    """
    token = await db.sf_tokens.find_one({'sf_user_id': sf_user_id})
    
    if token:
        return {
            "connected": True,
            "sf_user_id": sf_user_id,
            "instance_url": token.get('instance_url'),
            "connected_at": token.get('connected_at'),
            "salesforce_org_id": token.get('salesforce_org_id')
        }
    else:
        return {
            "connected": False,
            "sf_user_id": sf_user_id,
            "message": "User has not connected their Salesforce account",
            "auth_url": "/auth/login"
        }

@router.delete("/disconnect/{sf_user_id}")
async def disconnect_salesforce(
    sf_user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Disconnect user from Salesforce (delete stored tokens)
    
    Args:
        sf_user_id: Salesforce user ID
        db: Database instance
        
    Returns:
        Success status
    """
    result = await db.sf_tokens.delete_one({'sf_user_id': sf_user_id})
    
    if result.deleted_count > 0:
        return {
            "success": True,
            "message": "Successfully disconnected from Salesforce",
            "sf_user_id": sf_user_id
        }
    else:
        raise HTTPException(
            status_code=404,
            detail="User was not connected to Salesforce"
        )