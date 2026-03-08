#!/bin/bash

# Export Lambda environment variables from deployed stack
# Usage: ./export-lambda-env.sh [staging|production]

set -e

ENVIRONMENT=${1:-staging}
STACK_NAME="AnnaDrishtiCollectiveStack"

echo "Exporting Lambda environment variables for: $ENVIRONMENT"

# Get stack outputs
INVENTORY_TABLE=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query "Stacks[0].Outputs[?OutputKey=='InventoryTableName'].OutputValue" \
    --output text)

CONTRIBUTIONS_TABLE=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query "Stacks[0].Outputs[?OutputKey=='ContributionsTableName'].OutputValue" \
    --output text)

RESERVATIONS_TABLE=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query "Stacks[0].Outputs[?OutputKey=='ReservationsTableName'].OutputValue" \
    --output text)

API_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
    --output text)

# Create backend .env file
cat > ../backend/collective/.env << EOF
# Environment
ENVIRONMENT=$ENVIRONMENT

# AWS Configuration
AWS_REGION=$(aws configure get region)
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# DynamoDB Tables
INVENTORY_TABLE_NAME=$INVENTORY_TABLE
CONTRIBUTIONS_TABLE_NAME=$CONTRIBUTIONS_TABLE
RESERVATIONS_TABLE_NAME=$RESERVATIONS_TABLE

# API Configuration
API_URL=$API_URL
FEATURE_FLAG_COLLECTIVE_MODE=true

# Logging
LOG_LEVEL=INFO
ENABLE_AUDIT_LOGGING=true
EOF

echo "Lambda environment variables exported to: ../backend/collective/.env"
echo ""
echo "API URL: $API_URL"
echo "Inventory Table: $INVENTORY_TABLE"
echo "Contributions Table: $CONTRIBUTIONS_TABLE"
echo "Reservations Table: $RESERVATIONS_TABLE"
