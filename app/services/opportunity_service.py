# app/services/opportunity_service.py
from simple_salesforce import Salesforce
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException
from typing import Dict, Optional, List
from datetime import datetime
from app.core.salesforce import sf_oauth

class OpportunityService:
    """
    Service for Salesforce opportunity operations
    Handles authentication, token refresh, and SOQL queries
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def get_sf_client(self, sf_user_id: str) -> Salesforce:
        """
        Get authenticated Salesforce client for a user
        Automatically refreshes access token using stored refresh token
        
        Args:
            sf_user_id: Salesforce user ID
            
        Returns:
            Authenticated Salesforce client
            
        Raises:
            HTTPException: If user not connected or authentication fails
        """
        # Get stored refresh token
        user_token = await self.db.sf_tokens.find_one({'sf_user_id': sf_user_id})
        
        if not user_token:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "Not connected to Salesforce",
                    "message": "Please authorize your Salesforce account first",
                    "auth_url": "/auth/login"
                }
            )
        
        # Decrypt refresh token
        try:
            refresh_token = sf_oauth.decrypt(user_token['refresh_token'])
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to decrypt token: {str(e)}"
            )
        
        # Get fresh access token (not stored, just used in memory)
        try:
            tokens = sf_oauth.refresh_token(refresh_token)
            
            # Return authenticated Salesforce client
            return Salesforce(
                instance_url=user_token['instance_url'],
                session_id=tokens['access_token']
            )
            
        except HTTPException as e:
            # Refresh token might be revoked or expired
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "Salesforce connection expired",
                    "message": "Please reconnect your Salesforce account",
                    "auth_url": "/auth/login"
                }
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to authenticate with Salesforce: {str(e)}"
            )
    
    async def check_opportunity_exists(
        self, 
        sf_user_id: str, 
        opp_id: str
    ) -> Dict:
        """
        Check if an opportunity exists in Salesforce
        
        Args:
            sf_user_id: Salesforce user ID
            opp_id: Salesforce Opportunity ID (e.g., '006...')
            
        Returns:
            Dict with exists flag and opportunity data if found
        """
        sf = await self.get_sf_client(sf_user_id)
        
        try:
            query = f"""
                SELECT Id, Name, StageName, Amount, CloseDate, 
                       OwnerId, Owner.Name, AccountId, Account.Name,
                       Probability, Type, LeadSource
                FROM Opportunity 
                WHERE Id = '{opp_id}'
            """
            
            result = sf.query(query)
            
            if result['totalSize'] > 0:
                opp = result['records'][0]
                return {
                    "exists": True,
                    "opportunity": {
                        "id": opp.get('Id'),
                        "name": opp.get('Name'),
                        "stage": opp.get('StageName'),
                        "amount": opp.get('Amount'),
                        "close_date": opp.get('CloseDate'),
                        "probability": opp.get('Probability'),
                        "type": opp.get('Type'),
                        "owner": opp.get('Owner', {}).get('Name') if opp.get('Owner') else None,
                        "account": opp.get('Account', {}).get('Name') if opp.get('Account') else None,
                        "lead_source": opp.get('LeadSource')
                    }
                }
            else:
                return {
                    "exists": False,
                    "opportunity": None
                }
                
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Salesforce query failed: {str(e)}"
            )
    
    async def search_opportunities(
        self,
        sf_user_id: str,
        name: Optional[str] = None,
        stage: Optional[str] = None,
        owner_id: Optional[str] = None,
        limit: int = 10
    ) -> Dict:
        """
        Search for opportunities with filters
        
        Args:
            sf_user_id: Salesforce user ID
            name: Optional name filter (partial match)
            stage: Optional stage filter (exact match)
            owner_id: Optional owner ID filter
            limit: Maximum results to return
            
        Returns:
            Dict with opportunities list and count
        """
        sf = await self.get_sf_client(sf_user_id)
        
        # Build WHERE clause dynamically
        conditions = []
        
        if name:
            # Escape single quotes for SOQL
            safe_name = name.replace("'", "\\'")
            conditions.append(f"Name LIKE '%{safe_name}%'")
        
        if stage:
            safe_stage = stage.replace("'", "\\'")
            conditions.append(f"StageName = '{safe_stage}'")
        
        if owner_id:
            conditions.append(f"OwnerId = '{owner_id}'")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        try:
            query = f"""
                SELECT Id, Name, StageName, Amount, CloseDate,
                       Owner.Name, Account.Name, Probability
                FROM Opportunity
                WHERE {where_clause}
                ORDER BY CloseDate DESC
                LIMIT {limit}
            """
            
            result = sf.query(query)
            
            opportunities = [
                {
                    "id": opp.get('Id'),
                    "name": opp.get('Name'),
                    "stage": opp.get('StageName'),
                    "amount": opp.get('Amount'),
                    "close_date": opp.get('CloseDate'),
                    "probability": opp.get('Probability'),
                    "owner": opp.get('Owner', {}).get('Name') if opp.get('Owner') else None,
                    "account": opp.get('Account', {}).get('Name') if opp.get('Account') else None
                }
                for opp in result['records']
            ]
            
            return {
                "count": result['totalSize'],
                "opportunities": opportunities
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Salesforce search failed: {str(e)}"
            )
    
    async def get_user_opportunities(
        self,
        sf_user_id: str,
        limit: int = 20
    ) -> Dict:
        """
        Get opportunities owned by the authenticated user
        
        Args:
            sf_user_id: Salesforce user ID
            limit: Maximum results to return
            
        Returns:
            Dict with user's opportunities
        """
        sf = await self.get_sf_client(sf_user_id)
        
        try:
            # Get current user's info
            user_info = sf.query(f"SELECT Id FROM User WHERE Id = '{sf_user_id}'")
            
            if user_info['totalSize'] == 0:
                raise HTTPException(
                    status_code=404,
                    detail="User not found in Salesforce"
                )
            
            # Query user's opportunities
            query = f"""
                SELECT Id, Name, StageName, Amount, CloseDate,
                       Account.Name, Probability, Type
                FROM Opportunity
                WHERE OwnerId = '{sf_user_id}'
                ORDER BY CloseDate DESC
                LIMIT {limit}
            """
            
            result = sf.query(query)
            
            opportunities = [
                {
                    "id": opp.get('Id'),
                    "name": opp.get('Name'),
                    "stage": opp.get('StageName'),
                    "amount": opp.get('Amount'),
                    "close_date": opp.get('CloseDate'),
                    "probability": opp.get('Probability'),
                    "type": opp.get('Type'),
                    "account": opp.get('Account', {}).get('Name') if opp.get('Account') else None
                }
                for opp in result['records']
            ]
            
            return {
                "count": result['totalSize'],
                "opportunities": opportunities
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch user opportunities: {str(e)}"
            )
    
    async def disconnect_user(self, sf_user_id: str) -> Dict:
        """
        Disconnect user from Salesforce (delete stored tokens)
        
        Args:
            sf_user_id: Salesforce user ID
            
        Returns:
            Dict with success status
        """
        result = await self.db.sf_tokens.delete_one({'sf_user_id': sf_user_id})
        
        if result.deleted_count > 0:
            return {
                "success": True,
                "message": "Successfully disconnected from Salesforce"
            }
        else:
            return {
                "success": False,
                "message": "User was not connected to Salesforce"
            }