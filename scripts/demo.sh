#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────
#  Fortinet Salesforce API — Demo Script
#
#  Prerequisites:
#    1. Salesforce CLI installed  (https://developer.salesforce.com/tools/salesforcecli)
#    2. Logged in:  sf org login web --alias fortinet
#    3. API server running:  uvicorn app.main:app --port 8000
#
#  Usage:
#    ./scripts/demo.sh                               # uses default org
#    ./scripts/demo.sh --target-org fortinet          # uses the Fortinet org
#    ./scripts/demo.sh --target-org fortinet --api https://sales.fortinet-us.com
# ──────────────────────────────────────────────────────────
set -euo pipefail

# ── Defaults ──────────────────────────────────────────────
API_BASE="http://localhost:8000"
SF_TARGET_ORG=""

# ── Parse args ────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target-org)  SF_TARGET_ORG="$2"; shift 2 ;;
    --api)         API_BASE="$2";      shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--target-org <alias>] [--api <base_url>]"
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

API_BASE="${API_BASE%/}"  # strip trailing slash

# ── Colours ───────────────────────────────────────────────
BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
RESET='\033[0m'

banner()  { echo -e "\n${BOLD}${CYAN}═══  $1  ═══${RESET}\n"; }
ok()      { echo -e "${GREEN}✔  $1${RESET}"; }
warn()    { echo -e "${YELLOW}⚠  $1${RESET}"; }
fail()    { echo -e "${RED}✖  $1${RESET}"; }

# ── 1. Extract SF credentials from CLI ───────────────────
banner "Step 1 — Extracting Salesforce credentials"

SF_CMD="sf org display --json"
[[ -n "$SF_TARGET_ORG" ]] && SF_CMD="$SF_CMD --target-org $SF_TARGET_ORG"

echo "Running: $SF_CMD"
SF_JSON=$($SF_CMD 2>&1) || {
  fail "sf org display failed. Are you logged in?"
  echo "$SF_JSON"
  exit 1
}

ACCESS_TOKEN=$(echo "$SF_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['accessToken'])")
INSTANCE_URL=$(echo "$SF_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['instanceUrl'])")

ok "Access token: ${ACCESS_TOKEN:0:20}…"
ok "Instance URL: $INSTANCE_URL"

# ── 2. Health check ──────────────────────────────────────
banner "Step 2 — Health check"

HTTP_CODE=$(curl -s -o /tmp/demo_health.json -w "%{http_code}" "$API_BASE/api/v1/health")

if [[ "$HTTP_CODE" == "200" ]]; then
  ok "GET /api/v1/health → $HTTP_CODE"
  python3 -m json.tool /tmp/demo_health.json
else
  fail "Health check failed (HTTP $HTTP_CODE). Is the server running at $API_BASE?"
  cat /tmp/demo_health.json 2>/dev/null
  exit 1
fi

# ── 3. Prompt for Opportunity ID ─────────────────────────
banner "Step 3 — Opportunity lookup"

if [[ -t 0 ]]; then
  read -rp "Enter a Salesforce Opportunity ID (18-char, e.g. 006...): " OPP_ID
else
  # non-interactive — allow passing via env
  OPP_ID="${OPP_ID:-}"
fi

if [[ -z "$OPP_ID" ]]; then
  warn "No Opportunity ID provided — skipping opportunity endpoints."
  echo -e "\nRe-run with an Opportunity ID to test the full flow."
  exit 0
fi

# ── 4. Validate endpoint ─────────────────────────────────
banner "Step 4 — Validate opportunity"

echo "GET /api/v1/opportunities/$OPP_ID/validate"
HTTP_CODE=$(curl -s -o /tmp/demo_validate.json -w "%{http_code}" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "X-Sfdc-Instance-Url: $INSTANCE_URL" \
  "$API_BASE/api/v1/opportunities/$OPP_ID/validate")

if [[ "$HTTP_CODE" == "200" ]]; then
  ok "Validate → $HTTP_CODE"
  python3 -m json.tool /tmp/demo_validate.json
elif [[ "$HTTP_CODE" == "404" ]]; then
  warn "Opportunity not found (404)"
  python3 -m json.tool /tmp/demo_validate.json
else
  fail "Validate failed (HTTP $HTTP_CODE)"
  python3 -m json.tool /tmp/demo_validate.json 2>/dev/null || cat /tmp/demo_validate.json
fi

# ── 5. Retrieve endpoint ─────────────────────────────────
banner "Step 5 — Retrieve opportunity details"

echo "GET /api/v1/opportunities/$OPP_ID"
HTTP_CODE=$(curl -s -o /tmp/demo_detail.json -w "%{http_code}" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "X-Sfdc-Instance-Url: $INSTANCE_URL" \
  "$API_BASE/api/v1/opportunities/$OPP_ID")

if [[ "$HTTP_CODE" == "200" ]]; then
  ok "Retrieve → $HTTP_CODE"
  python3 -m json.tool /tmp/demo_detail.json
elif [[ "$HTTP_CODE" == "404" ]]; then
  warn "Opportunity not found (404)"
  python3 -m json.tool /tmp/demo_detail.json
else
  fail "Retrieve failed (HTTP $HTTP_CODE)"
  python3 -m json.tool /tmp/demo_detail.json 2>/dev/null || cat /tmp/demo_detail.json
fi

# ── Done ──────────────────────────────────────────────────
banner "Demo complete"
echo -e "API docs available at: ${BOLD}$API_BASE/docs${RESET}"
