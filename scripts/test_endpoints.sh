#!/bin/bash
# Script to test all AI Engine endpoints
# Usage: ./scripts/test_endpoints.sh <service-url> <jwt-token>

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <service-url> [jwt-token]"
    echo "Example: $0 http://ai-engine.railway.internal <token>"
    exit 1
fi

SERVICE_URL=$1
JWT_TOKEN=${2:-""}

echo "=========================================="
echo "AI Engine Endpoint Testing"
echo "=========================================="
echo "Service URL: $SERVICE_URL"
echo "=========================================="
echo ""

# Test 1: Health endpoint (no auth required)
echo -e "${YELLOW}Test 1: Health Check (GET /health)${NC}"
HEALTH_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$SERVICE_URL/health")
HTTP_STATUS=$(echo "$HEALTH_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
RESPONSE_BODY=$(echo "$HEALTH_RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" == "200" ]; then
    echo -e "${GREEN}✅ PASSED${NC}"
    echo "Response: $RESPONSE_BODY"
else
    echo -e "${RED}❌ FAILED${NC} (Status: $HTTP_STATUS)"
    echo "Response: $RESPONSE_BODY"
fi
echo ""

# Exit if no JWT token provided
if [ -z "$JWT_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  No JWT token provided. Skipping authenticated endpoints.${NC}"
    echo "To test all endpoints, provide a JWT token as the second argument."
    exit 0
fi

# Test 2: Inference endpoint
echo -e "${YELLOW}Test 2: Inference (POST /inference)${NC}"
INFERENCE_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$SERVICE_URL/inference" \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "What is the Indian Penal Code?",
        "context": "User is asking about criminal law in India.",
        "tenant_id": "test_tenant"
    }')
HTTP_STATUS=$(echo "$INFERENCE_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
RESPONSE_BODY=$(echo "$INFERENCE_RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" == "200" ]; then
    echo -e "${GREEN}✅ PASSED${NC}"
    echo "Response: $RESPONSE_BODY" | head -c 200
    echo "..."
else
    echo -e "${RED}❌ FAILED${NC} (Status: $HTTP_STATUS)"
    echo "Response: $RESPONSE_BODY"
fi
echo ""

# Test 3: Embed endpoint
echo -e "${YELLOW}Test 3: Embed (POST /embed)${NC}"
EMBED_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$SERVICE_URL/embed" \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "doc_id": "test_doc_123",
        "text": "This is a sample legal document for testing embeddings."
    }')
HTTP_STATUS=$(echo "$EMBED_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
RESPONSE_BODY=$(echo "$EMBED_RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" == "200" ]; then
    echo -e "${GREEN}✅ PASSED${NC}"
    echo "Response: $RESPONSE_BODY"
else
    echo -e "${RED}❌ FAILED${NC} (Status: $HTTP_STATUS)"
    echo "Response: $RESPONSE_BODY"
fi
echo ""

# Test 4: Search endpoint
echo -e "${YELLOW}Test 4: Search (POST /search)${NC}"
SEARCH_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$SERVICE_URL/search" \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "property law cases",
        "top_k": 5,
        "tenant_id": "test_tenant"
    }')
HTTP_STATUS=$(echo "$SEARCH_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
RESPONSE_BODY=$(echo "$SEARCH_RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" == "200" ]; then
    echo -e "${GREEN}✅ PASSED${NC}"
    echo "Response: $RESPONSE_BODY" | head -c 200
    echo "..."
else
    echo -e "${RED}❌ FAILED${NC} (Status: $HTTP_STATUS)"
    echo "Response: $RESPONSE_BODY"
fi
echo ""

# Test 5: Missing auth header (should fail)
echo -e "${YELLOW}Test 5: Missing Authorization (should return 401)${NC}"
NO_AUTH_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$SERVICE_URL/inference" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "test",
        "context": "test",
        "tenant_id": "test"
    }')
HTTP_STATUS=$(echo "$NO_AUTH_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
RESPONSE_BODY=$(echo "$NO_AUTH_RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" == "401" ]; then
    echo -e "${GREEN}✅ PASSED${NC} (Correctly rejected)"
    echo "Response: $RESPONSE_BODY"
else
    echo -e "${RED}❌ FAILED${NC} (Expected 401, got: $HTTP_STATUS)"
    echo "Response: $RESPONSE_BODY"
fi
echo ""

echo "=========================================="
echo "Testing Complete"
echo "=========================================="

