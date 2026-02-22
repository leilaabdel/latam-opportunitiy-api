from pydantic import BaseModel, Field
from typing import Optional


class AccountInfo(BaseModel):
    accountId: str
    accountName: str
    industry: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None


class OwnerInfo(BaseModel):
    userId: str
    fullName: Optional[str] = None
    email: Optional[str] = None


class ProductLineItem(BaseModel):
    lineItemId: str
    productId: Optional[str] = None
    productCode: Optional[str] = None
    productName: Optional[str] = None
    quantity: Optional[float] = None
    unitPrice: Optional[float] = None
    totalPrice: Optional[float] = None
    type: Optional[str] = None
    family: Optional[str] = None


class OpportunityValidationResponse(BaseModel):
    """Response for GET /opportunities/{id}/validate"""
    valid: bool
    opportunityId: str
    opportunityName: Optional[str] = None
    stage: Optional[str] = None
    closeDate: Optional[str] = None
    account: Optional[AccountInfo] = None
    validationMessages: list[str] = Field(default_factory=list)


class OpportunityDetailResponse(BaseModel):
    """Response for GET /opportunities/{id}"""
    opportunityId: str
    opportunityName: str
    stage: str
    closeDate: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    probability: Optional[float] = None
    description: Optional[str] = None
    owner: Optional[OwnerInfo] = None
    account: Optional[AccountInfo] = None
    products: list[ProductLineItem] = Field(default_factory=list)
    createdDate: Optional[str] = None
    lastModifiedDate: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response per Section 9 of requirements"""
    error: str
    message: str
    detail: Optional[str] = None
    field: Optional[str] = None
    requestId: Optional[str] = None
    timestamp: Optional[str] = None
