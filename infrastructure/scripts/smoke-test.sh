#!/bin/bash

# Smoke tests for deployed infrastructure
# Usage: ./smoke-test.sh [staging|production]

set -e

ENVIRONMENT=${1:-staging}
STACK_NAME="AnnaDrishtiCollectiveStack"

echo "Running smoke tests for: $ENVIRONMENT"
echo ""

# Get API URL from stack outputs
API_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
    --output text)

if [ -z "$API_URL" ]; then
    echo "Error: Could not retrieve API URL from stack"
    exit 1
fi

echo "API URL: $API_URL"
echo ""

# Test 1: Health check
echo "Test 1: Health check endpoint..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}health")
if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo "✓ Health check passed (HTTP $HEALTH_RESPONSE)"
else
    echo "✗ Health check failed (HTTP $HEALTH_RESPONSE)"
    exit 1
fi
echo ""

# Test 2: Root endpoint
echo "Test 2: Root endpoint..."
ROOT_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}")
if [ "$ROOT_RESPONSE" = "200" ]; then
    echo "✓ Root endpoint passed (HTTP $ROOT_RESPONSE)"
else
    echo "✗ Root endpoint failed (HTTP $ROOT_RESPONSE)"
    exit 1
fi
echo ""

# Test 3: Inventory endpoint (should return 404 or 200 with empty data)
echo "Test 3: Inventory endpoint..."
INVENTORY_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}api/inventory/test-fpo/tomato")
if [ "$INVENTORY_RESPONSE" = "404" ] || [ "$INVENTORY_RESPONSE" = "200" ]; then
    echo "✓ Inventory endpoint accessible (HTTP $INVENTORY_RESPONSE)"
else
    echo "✗ Inventory endpoint failed (HTTP $INVENTORY_RESPONSE)"
    exit 1
fi
echo ""

# Test 4: Societies endpoint
echo "Test 4: Societies endpoint..."
SOCIETIES_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}api/societies")
if [ "$SOCIETIES_RESPONSE" = "200" ]; then
    echo "✓ Societies endpoint passed (HTTP $SOCIETIES_RESPONSE)"
else
    echo "✗ Societies endpoint failed (HTTP $SOCIETIES_RESPONSE)"
    exit 1
fi
echo ""

# Test 5: Processing partners endpoint
echo "Test 5: Processing partners endpoint..."
PROCESSING_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}api/processing-partners")
if [ "$PROCESSING_RESPONSE" = "200" ]; then
    echo "✓ Processing partners endpoint passed (HTTP $PROCESSING_RESPONSE)"
else
    echo "✗ Processing partners endpoint failed (HTTP $PROCESSING_RESPONSE)"
    exit 1
fi
echo ""

# Test 6: Check DynamoDB tables exist
echo "Test 6: Checking DynamoDB tables..."
INVENTORY_TABLE=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query "Stacks[0].Outputs[?OutputKey=='InventoryTableName'].OutputValue" \
    --output text)

TABLE_STATUS=$(aws dynamodb describe-table \
    --table-name $INVENTORY_TABLE \
    --query "Table.TableStatus" \
    --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$TABLE_STATUS" = "ACTIVE" ]; then
    echo "✓ DynamoDB tables are active"
else
    echo "✗ DynamoDB tables not found or not active (Status: $TABLE_STATUS)"
    exit 1
fi
echo ""

# Test 7: Check Lambda function exists
echo "Test 7: Checking Lambda function..."
LAMBDA_NAME="collective-api-${ENVIRONMENT}"
LAMBDA_STATE=$(aws lambda get-function \
    --function-name $LAMBDA_NAME \
    --query "Configuration.State" \
    --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$LAMBDA_STATE" = "Active" ]; then
    echo "✓ Lambda function is active"
else
    echo "✗ Lambda function not found or not active (State: $LAMBDA_STATE)"
    exit 1
fi
echo ""

# Test 8: Check CloudWatch log groups exist
echo "Test 8: Checking CloudWatch log groups..."
LOG_GROUP="/aws/lambda/collective-api-${ENVIRONMENT}"
LOG_GROUP_EXISTS=$(aws logs describe-log-groups \
    --log-group-name-prefix $LOG_GROUP \
    --query "logGroups[?logGroupName=='$LOG_GROUP'].logGroupName" \
    --output text 2>/dev/null || echo "")

if [ -n "$LOG_GROUP_EXISTS" ]; then
    echo "✓ CloudWatch log groups exist"
else
    echo "✗ CloudWatch log groups not found"
    exit 1
fi
echo ""

echo "========================================="
echo "All smoke tests passed! ✓"
echo "========================================="
echo ""
echo "API URL: $API_URL"
echo "Environment: $ENVIRONMENT"
echo ""
echo "You can now:"
echo "1. Test the API with sample data"
echo "2. View logs in CloudWatch"
echo "3. Monitor metrics in the dashboard"
