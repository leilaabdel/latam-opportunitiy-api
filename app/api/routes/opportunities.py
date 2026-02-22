from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from simple_salesforce import Salesforce
from simple_salesforce.exceptions import SalesforceExpiredSession

from app.core.dependencies import get_sf_client
from app.models.opportunity import (
    ErrorResponse,
    OpportunityDetailResponse,
    OpportunityValidationResponse,
)
from app.services.opportunity_service import OpportunityService

router = APIRouter(tags=["Opportunities"])


def _request_id(x_request_id: str | None = Header(None, alias="X-Request-ID")) -> str | None:
    return x_request_id


@router.get(
    "/opportunities/{opportunity_id}/validate",
    response_model=OpportunityValidationResponse,
    responses={
        404: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
)
async def validate_opportunity(
    opportunity_id: str,
    sf: Salesforce = Depends(get_sf_client),
    request_id: str | None = Depends(_request_id),
):
    """Validate whether a Salesforce Opportunity is eligible for assessment linking."""
    service = OpportunityService(sf)
    try:
        result = service.validate(opportunity_id)
    except SalesforceExpiredSession:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "UNAUTHORIZED",
                "message": "Salesforce session has expired. Please provide a fresh access token.",
                "requestId": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "SALESFORCE_UNAVAILABLE",
                "message": "Failed to communicate with Salesforce.",
                "detail": str(exc),
                "requestId": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "NOT_FOUND",
                "message": f"No opportunity found with ID '{opportunity_id}'.",
                "opportunityId": opportunity_id,
                "requestId": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    return result


@router.get(
    "/opportunities/{opportunity_id}",
    response_model=OpportunityDetailResponse,
    responses={
        404: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
)
async def get_opportunity(
    opportunity_id: str,
    sf: Salesforce = Depends(get_sf_client),
    request_id: str | None = Depends(_request_id),
):
    """Retrieve full details for a Salesforce Opportunity."""
    service = OpportunityService(sf)
    try:
        result = service.get_detail(opportunity_id)
    except SalesforceExpiredSession:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "UNAUTHORIZED",
                "message": "Salesforce session has expired. Please provide a fresh access token.",
                "requestId": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "SALESFORCE_UNAVAILABLE",
                "message": "Failed to communicate with Salesforce.",
                "detail": str(exc),
                "requestId": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "NOT_FOUND",
                "message": f"No opportunity found with ID '{opportunity_id}'.",
                "opportunityId": opportunity_id,
                "requestId": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    return result
