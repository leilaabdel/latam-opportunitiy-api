# app/api/routes/opportunities.py
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from app.models.opportunity import (
    OpportunityDetail,
    OpportunityExistsResponse,
    OpportunitySearchResponse
)
from app.services.opportunity_service import OpportunityService
from app.db.mongodb import get_database

router = APIRouter(prefix="/opportunities", tags=["Opportunities"])

@router.get("/{opp_id}", response_model=OpportunityExistsResponse)
async def check_opportunity(
    opp_id: str,
    sf_user_id: str = Query(..., description="Salesforce user ID"),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> OpportunityExistsResponse:
    """Check if an opportunity exists in Salesforce"""
    service = OpportunityService(db)
    result = await service.check_opportunity_exists(sf_user_id, opp_id)
    return OpportunityExistsResponse(**result)

@router.get("/", response_model=OpportunitySearchResponse)
async def search_opportunities(
    sf_user_id: str = Query(..., description="Salesforce user ID"),
    name: Optional[str] = Query(None, description="Filter by opportunity name (partial match)"),
    stage: Optional[str] = Query(None, description="Filter by stage name (exact match)"),
    owner_id: Optional[str] = Query(None, description="Filter by owner ID"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> OpportunitySearchResponse:
    """Search for opportunities with optional filters"""
    service = OpportunityService(db)
    result = await service.search_opportunities(
        sf_user_id=sf_user_id,
        name=name,
        stage=stage,
        owner_id=owner_id,
        limit=limit
    )
    return OpportunitySearchResponse(**result)

@router.get("/user/my-opportunities", response_model=OpportunitySearchResponse)
async def get_my_opportunities(
    sf_user_id: str = Query(..., description="Salesforce user ID"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> OpportunitySearchResponse:
    """Get opportunities owned by the authenticated user"""
    service = OpportunityService(db)
    result = await service.get_user_opportunities(
        sf_user_id=sf_user_id,
        limit=limit
    )
    return OpportunitySearchResponse(**result)