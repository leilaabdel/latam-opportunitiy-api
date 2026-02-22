from datetime import date, timedelta
from simple_salesforce import Salesforce
from simple_salesforce.exceptions import SalesforceMalformedRequest

from app.models.opportunity import (
    AccountInfo,
    OpportunityDetailResponse,
    OpportunityValidationResponse,
    OwnerInfo,
    ProductLineItem,
)

# Stages that are ineligible for assessment linking
_CLOSED_LOST = "Closed Lost"
_CLOSED_WON = "Closed Won"
_MAX_PAST_CLOSE_DAYS = 180


def _build_account(record: dict) -> AccountInfo | None:
    acct = record.get("Account")
    if not acct or not acct.get("Id"):
        return None
    return AccountInfo(
        accountId=acct["Id"],
        accountName=acct.get("Name", ""),
        industry=acct.get("Industry"),
        country=acct.get("BillingCountry"),
        website=acct.get("Website"),
    )


def _build_owner(record: dict) -> OwnerInfo | None:
    owner = record.get("Owner")
    if not owner or not owner.get("Id"):
        return None
    return OwnerInfo(
        userId=owner["Id"],
        fullName=owner.get("Name"),
        email=owner.get("Email"),
    )


def _build_products(line_items: dict | None) -> list[ProductLineItem]:
    if not line_items or not line_items.get("records"):
        return []
    products = []
    for li in line_items["records"]:
        prod = li.get("Product2") or {}
        products.append(
            ProductLineItem(
                lineItemId=li["Id"],
                productId=prod.get("Id"),
                productCode=prod.get("ProductCode"),
                productName=prod.get("Name"),
                quantity=li.get("Quantity"),
                unitPrice=li.get("UnitPrice"),
                totalPrice=li.get("TotalPrice"),
                type=prod.get("Family"),
                family=prod.get("Family"),
            )
        )
    return products


class OpportunityService:
    """Stateless service — receives a Salesforce client per call."""

    def __init__(self, sf: Salesforce):
        self.sf = sf

    # ------------------------------------------------------------------
    # Validate (Section 4 of requirements)
    # ------------------------------------------------------------------

    def validate(self, opportunity_id: str) -> OpportunityValidationResponse | None:
        """Return validation response, or None if the opportunity does not exist."""
        query = (
            "SELECT Id, Name, StageName, CloseDate, "
            "AccountId, Account.Id, Account.Name, Account.Industry, "
            "Account.BillingCountry "
            "FROM Opportunity "
            f"WHERE Id = '{opportunity_id}'"
        )

        try:
            result = self.sf.query(query)
        except SalesforceMalformedRequest:
            return None  # bad ID format → treat as not found

        if result["totalSize"] == 0:
            return None

        opp = result["records"][0]
        stage = opp.get("StageName", "")
        close_date_str = opp.get("CloseDate")
        account = _build_account(opp)

        messages: list[str] = []

        # VR-02
        if stage == _CLOSED_LOST:
            messages.append(
                "Opportunity is in 'Closed Lost' stage and cannot receive new assessments."
            )
        # VR-03
        if stage == _CLOSED_WON:
            messages.append(
                "Opportunity is in 'Closed Won' stage and cannot receive new assessments."
            )
        # VR-05
        if close_date_str:
            try:
                close_date = date.fromisoformat(close_date_str)
                cutoff = date.today() - timedelta(days=_MAX_PAST_CLOSE_DAYS)
                if close_date < cutoff:
                    messages.append(
                        f"Opportunity close date ({close_date_str}) is more than {_MAX_PAST_CLOSE_DAYS} days in the past."
                    )
            except ValueError:
                pass

        return OpportunityValidationResponse(
            valid=len(messages) == 0,
            opportunityId=opp["Id"],
            opportunityName=opp.get("Name"),
            stage=stage,
            closeDate=close_date_str,
            account=account,
            validationMessages=messages,
        )

    # ------------------------------------------------------------------
    # Retrieve full details (Section 6 of requirements)
    # ------------------------------------------------------------------

    def get_detail(self, opportunity_id: str) -> OpportunityDetailResponse | None:
        """Return full opportunity details, or None if not found."""
        query = (
            "SELECT Id, Name, StageName, CloseDate, Amount, CurrencyIsoCode, "
            "Probability, Description, "
            "OwnerId, Owner.Id, Owner.Name, Owner.Email, "
            "AccountId, Account.Id, Account.Name, Account.Industry, "
            "Account.BillingCountry, Account.Website, "
            "CreatedDate, LastModifiedDate, "
            "(SELECT Id, Product2Id, Product2.Id, Product2.Name, "
            "Product2.ProductCode, Product2.Family, "
            "Quantity, UnitPrice, TotalPrice "
            "FROM OpportunityLineItems) "
            "FROM Opportunity "
            f"WHERE Id = '{opportunity_id}'"
        )

        try:
            result = self.sf.query(query)
        except SalesforceMalformedRequest:
            return None

        if result["totalSize"] == 0:
            return None

        opp = result["records"][0]

        return OpportunityDetailResponse(
            opportunityId=opp["Id"],
            opportunityName=opp.get("Name", ""),
            stage=opp.get("StageName", ""),
            closeDate=opp.get("CloseDate"),
            amount=opp.get("Amount"),
            currency=opp.get("CurrencyIsoCode"),
            probability=opp.get("Probability"),
            description=opp.get("Description"),
            owner=_build_owner(opp),
            account=_build_account(opp),
            products=_build_products(opp.get("OpportunityLineItems")),
            createdDate=opp.get("CreatedDate"),
            lastModifiedDate=opp.get("LastModifiedDate"),
        )
