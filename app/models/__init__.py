# app/models/__init__.py
from .opportunity import (
    OpportunityDetail,
    OpportunityExistsResponse,
    OpportunitySearchResponse,
    OpportunityQueryParams
)

__all__ = [
    "OpportunityDetail",
    "OpportunityExistsResponse", 
    "OpportunitySearchResponse",
    "OpportunityQueryParams"
]