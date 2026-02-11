# app/models/opportunity.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class OpportunityDetail(BaseModel):
    """Detailed opportunity information from Salesforce"""
    id: str = Field(..., description="Salesforce Opportunity ID")
    name: str = Field(..., description="Opportunity name")
    stage: str = Field(..., description="Current stage of the opportunity")
    amount: Optional[float] = Field(None, description="Opportunity amount in dollars")
    close_date: Optional[str] = Field(None, description="Expected close date (YYYY-MM-DD)")
    probability: Optional[int] = Field(None, ge=0, le=100, description="Win probability percentage")
    type: Optional[str] = Field(None, description="Opportunity type")
    owner: Optional[str] = Field(None, description="Opportunity owner name")
    account: Optional[str] = Field(None, description="Associated account name")
    lead_source: Optional[str] = Field(None, description="Lead source")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "006XXXXXXXXXXXXXXX",
                "name": "Acme Corp - 1000 Licenses",
                "stage": "Negotiation/Review",
                "amount": 150000.0,
                "close_date": "2025-03-15",
                "probability": 75,
                "type": "New Business",
                "owner": "John Doe",
                "account": "Acme Corporation",
                "lead_source": "Web"
            }
        }

class OpportunityExistsResponse(BaseModel):
    """Response for opportunity existence check"""
    exists: bool = Field(..., description="Whether the opportunity exists")
    opportunity: Optional[OpportunityDetail] = Field(None, description="Opportunity details if found")
    
    class Config:
        json_schema_extra = {
            "example": {
                "exists": True,
                "opportunity": {
                    "id": "006XXXXXXXXXXXXXXX",
                    "name": "Acme Corp - 1000 Licenses",
                    "stage": "Negotiation/Review",
                    "amount": 150000.0,
                    "close_date": "2025-03-15",
                    "probability": 75,
                    "type": "New Business",
                    "owner": "John Doe",
                    "account": "Acme Corporation",
                    "lead_source": "Web"
                }
            }
        }

class OpportunitySearchResponse(BaseModel):
    """Response for opportunity search and list operations"""
    count: int = Field(..., description="Total number of opportunities found")
    opportunities: list[OpportunityDetail] = Field(..., description="List of opportunities")
    
    class Config:
        json_schema_extra = {
            "example": {
                "count": 2,
                "opportunities": [
                    {
                        "id": "006XXXXXXXXXXXXXXX",
                        "name": "Acme Corp - 1000 Licenses",
                        "stage": "Negotiation/Review",
                        "amount": 150000.0,
                        "close_date": "2025-03-15",
                        "probability": 75,
                        "type": "New Business",
                        "owner": "John Doe",
                        "account": "Acme Corporation",
                        "lead_source": "Web"
                    }
                ]
            }
        }

class OpportunityQueryParams(BaseModel):
    """Query parameters for opportunity search"""
    sf_user_id: str = Field(..., description="Salesforce user ID")
    name: Optional[str] = Field(None, description="Filter by opportunity name (partial match)")
    stage: Optional[str] = Field(None, description="Filter by stage name (exact match)")
    owner_id: Optional[str] = Field(None, description="Filter by owner ID")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")