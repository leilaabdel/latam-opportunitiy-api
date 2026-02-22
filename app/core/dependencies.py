from fastapi import Header, HTTPException
from simple_salesforce import Salesforce
from simple_salesforce.exceptions import SalesforceAuthenticationFailed


async def get_sf_client(
    authorization: str = Header(..., description="Bearer <salesforce_access_token>"),
    x_sfdc_instance_url: str = Header(
        ...,
        alias="X-Sfdc-Instance-Url",
        description="Salesforce instance URL (e.g. https://yourinstance.my.salesforce.com)",
    ),
) -> Salesforce:
    """Extract Salesforce credentials from request headers and return an authenticated client."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={
                "error": "UNAUTHORIZED",
                "message": "Authorization header must use Bearer scheme.",
            },
        )

    access_token = authorization[7:]  # strip "Bearer "
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "UNAUTHORIZED",
                "message": "Access token is empty.",
            },
        )

    instance_url = x_sfdc_instance_url.rstrip("/")

    try:
        return Salesforce(instance_url=instance_url, session_id=access_token)
    except SalesforceAuthenticationFailed:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "UNAUTHORIZED",
                "message": "Salesforce authentication failed. The access token may be expired or invalid.",
            },
        )
