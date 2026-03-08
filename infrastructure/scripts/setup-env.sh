#!/bin/bash

# Setup environment variables for deployment
# Usage: ./setup-env.sh [staging|production]

set -e

ENVIRONMENT=${1:-staging}

echo "Setting up environment variables for: $ENVIRONMENT"

# Check if config file exists
CONFIG_FILE="config/${ENVIRONMENT}.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file $CONFIG_FILE not found"
    exit 1
fi

# Load AWS account and region
export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
export CDK_DEFAULT_REGION=$(jq -r '.region' "$CONFIG_FILE")
export ENVIRONMENT=$ENVIRONMENT

echo "AWS Account: $CDK_DEFAULT_ACCOUNT"
echo "AWS Region: $CDK_DEFAULT_REGION"
echo "Environment: $ENVIRONMENT"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example"
    cp .env.example .env
fi

# Update .env file with current values
cat > .env << EOF
# AWS Configuration
CDK_DEFAULT_ACCOUNT=$CDK_DEFAULT_ACCOUNT
CDK_DEFAULT_REGION=$CDK_DEFAULT_REGION

# Environment
ENVIRONMENT=$ENVIRONMENT

# Feature Flags
FEATURE_FLAG_COLLECTIVE_MODE=$(jq -r '.featureFlags.collectiveMode' "$CONFIG_FILE")
FEATURE_FLAG_RDS_ENABLED=$(jq -r '.enableRds' "$CONFIG_FILE")

# API Configuration
API_THROTTLE_BURST_LIMIT=$(jq -r '.apiThrottleBurstLimit' "$CONFIG_FILE")
API_THROTTLE_RATE_LIMIT=$(jq -r '.apiThrottleRateLimit' "$CONFIG_FILE")

# Monitoring
CLOUDWATCH_RETENTION_DAYS=$(jq -r '.cloudwatchRetentionDays' "$CONFIG_FILE")
ENABLE_DETAILED_MONITORING=$(jq -r '.featureFlags.detailedMonitoring' "$CONFIG_FILE")

# Deployment
ENABLE_POINT_IN_TIME_RECOVERY=$(jq -r '.enablePointInTimeRecovery' "$CONFIG_FILE")
ENABLE_DELETION_PROTECTION=$(jq -r '.enableDeletionProtection' "$CONFIG_FILE")
EOF

echo "Environment variables configured successfully"
echo "Configuration loaded from: $CONFIG_FILE"
echo ""
echo "To deploy, run:"
echo "  npm run build"
echo "  npm run cdk deploy AnnaDrishtiCollectiveStack"
