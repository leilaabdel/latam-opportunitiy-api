# Fortinet Salesforce Integration Service

> **Phase 1 — Opportunity Validation & Retrieval**
>
> This service fulfills the Phase 1 requirements of the *Salesforce Integration Requirements* document (v1.0, 2026-02-20). It provides the Fortinet Assessment Tool with the ability to **validate** and **retrieve** Salesforce Opportunities via REST API, so that every assessment and Business Case can be tied back to a verified CRM record.

**Production URL:** `https://sales.fortinet-us.com`

---

## What This Delivers (Phase 1 Scope)

| Capability | Status | Requirement Reference |
|-----------|--------|----------------------|
| Validate that an Opportunity exists and is eligible for assessment linking | Delivered | Section 4 |
| Retrieve full Opportunity details (account, owner, product bundle) | Delivered | Section 6 |
| Health check endpoint | Delivered | Section 8.6 |
| Standardized error responses | Delivered | Section 9 |
| Support for multiple concurrent users/sessions | Delivered | Section 3 |
| Opportunity search by account/name/stage | Not yet | Section 4.4 (Phase 1b) |
| Opportunity creation from Business Case | Not yet | Section 5 (Phase 2) |

---

## Interactive API Documentation

Full endpoint documentation with example requests, response schemas, and a "Try it out" feature is available via Swagger UI:

| Environment | Swagger UI | Alternative (ReDoc) |
|-------------|-----------|---------------------|
| **Production** | [sales.fortinet-us.com/docs](https://sales.fortinet-us.com/docs) | [sales.fortinet-us.com/redoc](https://sales.fortinet-us.com/redoc) |
| **Local dev** | [localhost:8000/docs](http://localhost:8000/docs) | [localhost:8000/redoc](http://localhost:8000/redoc) |

The machine-readable OpenAPI specification is available at `/openapi.json`.

---

## Endpoints

All endpoints are versioned under `/api/v1` per Section 8.1 of the requirements.

### `GET /api/v1/health`

No authentication required. Returns service status.

```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2026-02-20T14:00:00+00:00"
}
```

---

### `GET /api/v1/opportunities/{opportunityId}/validate`

*Requirement: Section 4.2*

Confirms that a Salesforce Opportunity exists and is in an eligible state to receive an assessment. Returns `valid: true` or `valid: false` with human-readable messages explaining why.

**Example — eligible opportunity:**

```json
{
  "valid": true,
  "opportunityId": "006Hs00000AbCdEFGH",
  "opportunityName": "Acme Corp — MSSP Security Package 2026",
  "stage": "Proposal/Price Quote",
  "closeDate": "2026-06-30",
  "account": {
    "accountId": "001Hs00000XyZaBCDE",
    "accountName": "Acme Corporation"
  },
  "validationMessages": []
}
```

**Example — ineligible opportunity:**

```json
{
  "valid": false,
  "opportunityId": "006Hs00000AbCdEFGH",
  "opportunityName": "Acme Corp — Legacy Deal",
  "stage": "Closed Lost",
  "closeDate": "2025-09-01",
  "account": {
    "accountId": "001Hs00000XyZaBCDE",
    "accountName": "Acme Corporation"
  },
  "validationMessages": [
    "Opportunity is in 'Closed Lost' stage and cannot receive new assessments."
  ]
}
```

#### Validation Business Rules

| Rule ID | Rule | Behavior |
|---------|------|----------|
| VR-01 | Opportunity must exist in Salesforce | `404 Not Found` |
| VR-02 | Stage must not be `Closed Lost` | `valid: false` + message |
| VR-03 | Stage must not be `Closed Won` | `valid: false` + message |
| VR-05 | Close date must not be more than 180 days in the past | `valid: false` + message |

---

### `GET /api/v1/opportunities/{opportunityId}`

*Requirement: Section 6.2*

Returns full Opportunity details including account information, opportunity owner, and the product/service bundle (OpportunityLineItems).

**Response includes all required fields from Section 6.3:**

| Field | JSON Path | Salesforce Source |
|-------|-----------|-------------------|
| Opportunity ID | `opportunityId` | `Opportunity.Id` |
| Opportunity Name | `opportunityName` | `Opportunity.Name` |
| Stage | `stage` | `Opportunity.StageName` |
| Close Date | `closeDate` | `Opportunity.CloseDate` |
| Amount | `amount` | `Opportunity.Amount` |
| Probability | `probability` | `Opportunity.Probability` |
| Account ID | `account.accountId` | `Account.Id` |
| Account Name | `account.accountName` | `Account.Name` |
| Owner | `owner.fullName` | `User.Name` |
| Product Code | `products[].productCode` | `Product2.ProductCode` |
| Product Name | `products[].productName` | `Product2.Name` |
| Quantity | `products[].quantity` | `OpportunityLineItem.Quantity` |
| Unit Price | `products[].unitPrice` | `OpportunityLineItem.UnitPrice` |
| Total Price | `products[].totalPrice` | `OpportunityLineItem.TotalPrice` |
| Product Family | `products[].family` | `Product2.Family` |

---

## Authentication

Every request (except `/health`) must include the caller's Salesforce session credentials as headers:

| Header | Value | Description |
|--------|-------|-------------|
| `Authorization` | `Bearer <access_token>` | A valid Salesforce access token |
| `X-Sfdc-Instance-Url` | `https://fortinet.my.salesforce.com` | The Fortinet Salesforce instance URL |

**How to obtain these credentials:**

```bash
# 1. Install the Salesforce CLI (one-time):  https://developer.salesforce.com/tools/salesforcecli
# 2. Log in to the Fortinet org (opens a browser window — one-time):
sf org login web --alias fortinet

# 3. Retrieve your access token and instance URL:
sf org display --target-org fortinet --json
```

The JSON output contains `accessToken` and `instanceUrl` — pass these as the two headers above.

The API supports **multiple concurrent sessions** — each user authenticates with their own Salesforce credentials, and the service handles them independently with no server-side state.

---

## Error Handling

*Requirement: Section 9*

All errors follow a consistent JSON structure:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable description.",
  "detail": "Optional technical detail.",
  "requestId": "from X-Request-ID header",
  "timestamp": "2026-02-20T14:00:00+00:00"
}
```

| HTTP Status | Error Code | Scenario |
|-------------|-----------|----------|
| `401` | `UNAUTHORIZED` | Missing, expired, or invalid Salesforce access token |
| `404` | `NOT_FOUND` | Opportunity ID does not exist in Salesforce |
| `422` | `Validation Error` | Missing required headers |
| `502` | `SALESFORCE_UNAVAILABLE` | Salesforce API is unreachable or returned an error |

Pass an `X-Request-ID` header (UUID) on each call for distributed tracing — it will be echoed back in error responses.

---

## Running the Demo

A demo script is included that pulls credentials from the Salesforce CLI, hits the API, and pretty-prints results:

```bash
# Make sure the API server is running, then in another terminal:
./scripts/demo.sh --target-org fortinet

# Or point it at the production URL:
./scripts/demo.sh --target-org fortinet --api https://sales.fortinet-us.com
```

The script will:
1. Extract your Salesforce access token automatically
2. Verify the API is healthy
3. Prompt you for an Opportunity ID
4. Call both the **validate** and **retrieve** endpoints
5. Display color-coded results

---

## Deployment

### Docker

```bash
# Production build (distroless — minimal attack surface)
docker build -t fortinet-sf-api:latest .
docker run -d -p 8000:8000 -e ENVIRONMENT=production fortinet-sf-api:latest

# Development build (hot reload)
docker build -f Dockerfile.dev -t fortinet-sf-api:dev .
docker run -p 8000:8000 fortinet-sf-api:dev
```

### Hosting at `sales.fortinet-us.com`

1. **Deploy the Docker container** to your server (Azure VM, Azure App Service, EC2, etc.)
2. **Configure DNS** — add an `A` record pointing `sales.fortinet-us.com` to the server IP (or a `CNAME` to your Azure App Service hostname)
3. **Terminate TLS** — use a reverse proxy (Nginx + Let's Encrypt) or Azure's managed certificates to serve HTTPS

A CI/CD pipeline is already configured in `.github/workflows/build-deploy.yaml` — every push to `main` builds the Docker image and creates a GitHub release.

### Local Development

```bash
git clone <repo-url> && cd latam-salesforce-api
python -m venv env && source env/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

---

## What's Next (Future Phases)

| Phase | Capability | Requirement Reference |
|-------|-----------|----------------------|
| **1b** | Search opportunities by account name, opportunity name, stage, or owner | Section 4.4 |
| **2** | Create new Opportunities from Assessment Tool Business Cases | Section 5 |
| **2** | Idempotent creation based on `Business_Case_ID__c` | Section 5.4 |
| **2** | Product line item mapping to `OpportunityLineItem` records | Section 5.2 |
| **Future** | API-level authentication (OAuth 2.0 Client Credentials or API Key) | Section 7 |
| **Future** | Custom field support (`Assessment_Tool_ID__c`, `Business_Case_ID__c`) | Section 10.3 |
