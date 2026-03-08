#!/bin/bash

# Deploy to staging environment
# Usage: ./deploy-staging.sh

set -e

echo "========================================="
echo "Deploying Collective Selling to Staging"
echo "========================================="
echo ""

# Set environment
export ENVIRONMENT=staging

# Setup environment variables
echo "Step 1: Setting up environment variables..."
./setup-env.sh staging
echo ""

# Build TypeScript
echo "Step 2: Building CDK application..."
cd ..
npm run build
echo ""

# Bootstrap CDK (if not already done)
echo "Step 3: Bootstrapping CDK (if needed)..."
npm run cdk bootstrap
echo ""

# Deploy Collective Stack
echo "Step 4: Deploying Collective Stack..."
npm run cdk deploy AnnaDrishtiCollectiveStack --require-approval never
echo ""

# Deploy Monitoring Stack
echo "Step 5: Deploying Monitoring Stack..."
npm run cdk deploy AnnaDrishtiMonitoringStack --require-approval never
echo ""

# Export Lambda environment variables
echo "Step 6: Exporting Lambda environment variables..."
cd scripts
./export-lambda-env.sh staging
echo ""

# Run smoke tests
echo "Step 7: Running smoke tests..."
./smoke-test.sh staging
echo ""

echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Check CloudWatch dashboard for metrics"
echo "2. Verify API endpoints are working"
echo "3. Test with sample data"
echo ""
echo "To view stack outputs:"
echo "  aws cloudformation describe-stacks --stack-name AnnaDrishtiCollectiveStack"
