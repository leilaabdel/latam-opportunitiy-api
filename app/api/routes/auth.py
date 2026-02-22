# app/api/routes/auth.py - Update login and callback
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from app.core.salesforce import sf_oauth
from app.db.mongodb import get_database

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Fortinet brand constants
_FORTINET_RED = "#DA291C"
_FORTINET_DARK = "#1A1A2E"
_FORTINET_GRAY = "#4A4A68"

_BASE_STYLES = f"""
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        background: #f5f5f7;
    }}
    .card {{
        background: #fff;
        padding: 2.5rem 3rem;
        border-radius: 8px;
        box-shadow: 0 2px 16px rgba(0,0,0,0.08);
        text-align: center;
        max-width: 420px;
        width: 90%;
    }}
    .logo-area {{
        margin-bottom: 1.5rem;
    }}
    .logo-area svg {{
        width: 160px;
        height: auto;
    }}
    .divider {{
        width: 48px;
        height: 3px;
        background: {_FORTINET_RED};
        margin: 0 auto 1.5rem;
        border-radius: 2px;
    }}
"""

_FORTINET_LOGO_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" x="0" y="0" version="1.1" viewBox="0 0 487.6 55"><path d="M279.9 11.7V0h13.4v54.8h-13.4V11.7zM220.9 0h51.7v11.8h-24.3v43.1H235V11.8h-14.1V0zm266.7 0v11.8h-24.3v43.1H450V11.8h-14.1V0h51.7zM0 0h58v11.8H13.4v11.7h38v11.8h-38v19.5H0V0zm374.5 0h54v11.8h-40.6v9.8h33.3v11.8h-33.3v9.8h41.3V55h-54.7V0zm-10.3 15.5v39.3h-13.4V15.5c0-2.1-1.6-3.7-3.7-3.7h-30v43.1h-13.4V0h45c8.5 0 15.5 7 15.5 15.5zM200.3 0h-45.7v54.8H168V35.3h30c1.6.1 2.9 1.4 2.9 3v16.6h13.4V38.1c0-2.9-1.6-5.4-4-6.8 2.9-2.7 4.7-6.6 4.7-10.8v-5.8c.1-8.1-6.5-14.7-14.7-14.7zm1.4 20.5c0 1.6-1.3 3-3 3H168V11.8h30.7c1.6 0 3 1.3 3 3v5.7z"/><path d="M144.2 20.4v14.2H122V20.4h22.2zM93.9 54.8H116V40.6H93.9v14.2zm50.3-42.9c0-6.6-5.3-11.9-11.9-11.9h-10.2v14.2h22.1v-2.3zM93.9 0v14.2H116V0H93.9zM65.7 20.4v14.2h22.1V20.4H65.7zM122 54.8h10.2c6.6 0 11.9-5.3 11.9-11.9v-2.3H122v14.2zM65.7 42.9c0 6.6 5.3 11.9 11.9 11.9h10.2V40.6H65.7v2.3zm0-31v2.3h22.1V0H77.6C71 0 65.7 5.3 65.7 11.9z" fill="#da291c"/></svg>
"""


@router.get("/login")
async def salesforce_login():
    """Show Fortinet-branded login page to initiate Salesforce OAuth"""
    auth_url, state = sf_oauth.get_auth_url()

    return HTMLResponse(f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Connect to Salesforce | Fortinet</title>
            <style>
                {_BASE_STYLES}
                .subtitle {{
                    color: {_FORTINET_GRAY};
                    font-size: 0.95rem;
                    line-height: 1.5;
                    margin-bottom: 2rem;
                }}
                .sf-icon {{
                    width: 48px;
                    height: 48px;
                    margin-bottom: 1rem;
                }}
                .btn-connect {{
                    display: inline-flex;
                    align-items: center;
                    gap: 0.6rem;
                    background: {_FORTINET_RED};
                    color: #fff;
                    border: none;
                    padding: 0.85rem 2rem;
                    border-radius: 6px;
                    font-size: 1rem;
                    font-weight: 600;
                    cursor: pointer;
                    text-decoration: none;
                    transition: background 0.2s, box-shadow 0.2s;
                }}
                .btn-connect:hover {{
                    background: #b8221a;
                    box-shadow: 0 4px 12px rgba(218, 41, 28, 0.3);
                }}
                .btn-connect svg {{
                    width: 20px;
                    height: 20px;
                    fill: currentColor;
                }}
                .footer-note {{
                    margin-top: 1.5rem;
                    font-size: 0.8rem;
                    color: #999;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="logo-area">{_FORTINET_LOGO_SVG}</div>
                <div class="divider"></div>
                <p class="subtitle">
                    Connect your Salesforce account to enable<br>
                    opportunity tracking and management.
                </p>
                <!-- Salesforce cloud icon -->
                <svg class="sf-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M19.35 10.04A7.49 7.49 0 0 0 12 4C9.11 4 6.6 5.64 5.35 8.04A5.994 5.994 0 0 0 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z" fill="#00A1E0"/>
                </svg>
                <a class="btn-connect" href="{auth_url}">
                    <svg viewBox="0 0 24 24"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg>
                    Connect with Salesforce
                </a>
                <p class="footer-note">
                    You will be redirected to Salesforce to authorize access.
                </p>
            </div>
        </body>
        </html>
    """)


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
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Connected | Fortinet</title>
                <style>
                    {_BASE_STYLES}
                    .success-icon {{
                        width: 64px;
                        height: 64px;
                        border-radius: 50%;
                        background: #e8f9ee;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0 auto 1.25rem;
                    }}
                    .success-icon svg {{
                        width: 32px;
                        height: 32px;
                        fill: #22c55e;
                    }}
                    h1 {{
                        color: {_FORTINET_DARK};
                        font-size: 1.35rem;
                        margin-bottom: 0.5rem;
                    }}
                    .message {{
                        color: {_FORTINET_GRAY};
                        font-size: 0.9rem;
                        margin-bottom: 1.5rem;
                    }}
                    .user-id {{
                        background: #f5f5f7;
                        padding: 0.75rem 1rem;
                        border-radius: 6px;
                        font-family: 'SF Mono', 'Fira Code', monospace;
                        font-size: 0.85rem;
                        color: {_FORTINET_DARK};
                        word-break: break-all;
                        border-left: 3px solid {_FORTINET_RED};
                        text-align: left;
                    }}
                    .user-id strong {{
                        color: {_FORTINET_GRAY};
                        font-weight: 500;
                        font-family: 'Segoe UI', Roboto, sans-serif;
                        font-size: 0.75rem;
                        text-transform: uppercase;
                        letter-spacing: 0.05em;
                    }}
                    .close-note {{
                        margin-top: 1.5rem;
                        font-size: 0.8rem;
                        color: #999;
                    }}
                </style>
            </head>
            <body>
                <div class="card">
                    <div class="logo-area">{_FORTINET_LOGO_SVG}</div>
                    <div class="divider"></div>
                    <div class="success-icon">
                        <svg viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                    </div>
                    <h1>Successfully Connected</h1>
                    <p class="message">Your Salesforce account has been linked.</p>
                    <div class="user-id">
                        <strong>Salesforce User ID</strong><br>
                        {sf_user_id}
                    </div>
                    <p class="close-note">You may close this window.</p>
                </div>
            </body>
            </html>
        """)

    except Exception as e:
        error_message = str(e)
        return HTMLResponse(f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Connection Failed | Fortinet</title>
                <style>
                    {_BASE_STYLES}
                    .error-icon {{
                        width: 64px;
                        height: 64px;
                        border-radius: 50%;
                        background: #fef2f2;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0 auto 1.25rem;
                    }}
                    .error-icon svg {{
                        width: 32px;
                        height: 32px;
                        fill: {_FORTINET_RED};
                    }}
                    h1 {{
                        color: {_FORTINET_DARK};
                        font-size: 1.35rem;
                        margin-bottom: 0.5rem;
                    }}
                    .message {{
                        color: {_FORTINET_GRAY};
                        font-size: 0.9rem;
                        margin-bottom: 1.5rem;
                    }}
                    .error-detail {{
                        background: #fef2f2;
                        padding: 0.75rem 1rem;
                        border-radius: 6px;
                        font-size: 0.85rem;
                        color: #991b1b;
                        border-left: 3px solid {_FORTINET_RED};
                        text-align: left;
                        word-break: break-all;
                    }}
                    .btn-retry {{
                        display: inline-block;
                        margin-top: 1.5rem;
                        background: {_FORTINET_RED};
                        color: #fff;
                        border: none;
                        padding: 0.7rem 1.5rem;
                        border-radius: 6px;
                        font-size: 0.9rem;
                        font-weight: 600;
                        cursor: pointer;
                        text-decoration: none;
                        transition: background 0.2s;
                    }}
                    .btn-retry:hover {{
                        background: #b8221a;
                    }}
                </style>
            </head>
            <body>
                <div class="card">
                    <div class="logo-area">{_FORTINET_LOGO_SVG}</div>
                    <div class="divider"></div>
                    <div class="error-icon">
                        <svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
                    </div>
                    <h1>Connection Failed</h1>
                    <p class="message">Unable to connect to Salesforce.</p>
                    <div class="error-detail">{error_message}</div>
                    <a class="btn-retry" href="/auth/login">Try Again</a>
                </div>
            </body>
            </html>
        """, status_code=500)

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