# Collective Selling & Allocation - Deployment Guide

This guide covers deploying the Collective Selling & Allocation system to AWS using CDK.

## Prerequisites

1. **AWS Account**: Active AWS account with appropriate permissions
2. **AWS CLI**: Installed and configured with credentials
3. **Node.js**: Version 18+ installed
4. **Python**: Version 3.11+ installed
5. **CDK**: AWS CDK CLI installed (`npm install -g aws-cdk`)

## Architecture Overview

The deployment creates the following resources:

### DynamoDB Tables
- `collective-inventory-{env}`: Real-time inventory aggregation
- `farmer-contributions-{env}`: Individual farmer contributions
- `reservations-{env}`: Society demand reservations

### Lambda Functions
- `collective-api-{env}`: FastAPI application handling all API endpoints

### API Gateway
- REST API with proxy integration to Lambda
- CORS enabled for dashboard access
- Throttling configured per environment

### CloudWatch
- Log groups for Lambda functions
- Custom dashboard with key metrics
- Alarms for errors, latency, and throttling

### Optional: PostgreSQL RDS
- Can be enabled for relational data storage
- Configured in private subnet with security groups

## Deployment Steps

### 1. Initial Setup

```bash
# Navigate to infrastructure directory
cd infrastructure

# Install dependencies
npm install

# Configure AWS credentials (if not already done)
aws configure
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your values
# - CDK_DEFAULT_ACCOUNT: Your AWS account ID
# - CDK_DEFAULT_REGION: Your preferred region (default: ap-south-1)
# - ENVIRONMENT: staging or prod
```

### 3. Bootstrap CDK (First Time Only)

```bash
# Bootstrap CDK in your account/region
npm run cdk bootstrap
```

### 4. Deploy to Staging

```bash
# Run automated deployment script
cd scripts
./deploy-staging.sh
```

This script will:
1. Set up environment variables
2. Build TypeScript code
3. Deploy Collective Stack
4. Deploy Monitoring Stack
5. Export Lambda environment variables
6. Run smoke tests

### 5. Manual Deployment (Alternative)

```bash
# Build TypeScript
npm run build

# Deploy specific stack
npm run cdk deploy AnnaDrishtiCollectiveStack

# Deploy monitoring
npm run cdk deploy AnnaDrishtiMonitoringStack

# Deploy all stacks
npm run cdk deploy --all
```

### 6. Verify Deployment

```bash
# Run smoke tests
cd scripts
./smoke-test.sh staging

# Check stack outputs
aws cloudformation describe-stacks --stack-name AnnaDrishtiCollectiveStack

# Test API endpoint
curl https://your-api-url/health
```

## Environment Configuration

### Staging Environment

Configuration file: `config/staging.json`

- **Purpose**: Testing and validation
- **RDS**: Disabled (DynamoDB only)
- **Retention**: 7 days for logs
- **Protection**: No deletion protection
- **Throttling**: 100 burst, 50 rate limit

### Production Environment

Configuration file: `config/production.json`

- **Purpose**: Live production traffic
- **RDS**: Enabled (optional)
- **Retention**: 30 days for logs
- **Protection**: Deletion protection enabled
- **Throttling**: 500 burst, 200 rate limit

## Post-Deployment Tasks

### 1. Configure Alarm Email

```bash
# Deploy with alarm email
npm run cdk deploy AnnaDrishtiMonitoringStack \
  --context anna-drishti:alarm-email=your-email@example.com

# Confirm SNS subscription in email
```

### 2. Export Environment Variables

```bash
# Export Lambda environment variables for local testing
cd scripts
./export-lambda-env.sh staging
```

### 3. Initialize Database (if RDS enabled)

```bash
# Connect to RDS instance
psql -h your-rds-endpoint -U collective_admin -d collective_selling

# Run schema migration
\i ../backend/collective/db/schema.sql
```

### 4. Test API Endpoints

```bash
# Get API URL
API_URL=$(aws cloudformation describe-stacks \
  --stack-name AnnaDrishtiCollectiveStack \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
  --output text)

# Test health endpoint
curl $API_URL/health

# Test inventory endpoint
curl $API_URL/api/inventory/test-fpo/tomato

# Create a society
curl -X POST $API_URL/api/societies \
  -H "Content-Type: application/json" \
  -d '{
    "society_name": "Test Society",
    "location": "Bangalore",
    "contact_details": {"phone": "+91-9876543210"},
    "delivery_address": "123 Test Street",
    "delivery_frequency": "twice_weekly",
    "preferred_day": "Monday",
    "preferred_time_window": "9:00-11:00",
    "crop_preferences": [{"crop_type": "tomato", "typical_quantity_kg": 100}]
  }'
```

## Monitoring

### CloudWatch Dashboard

Access the dashboard:
```bash
# Get dashboard URL
aws cloudformation describe-stacks \
  --stack-name AnnaDrishtiMonitoringStack \
  --query "Stacks[0].Outputs[?OutputKey=='DashboardUrl'].OutputValue" \
  --output text
```

Dashboard includes:
- API Gateway requests, errors, and latency
- Lambda invocations, errors, duration, and throttles
- DynamoDB read/write capacity and errors

### CloudWatch Alarms

Alarms are configured for:
- API Gateway 5xx errors (threshold: 10 in 5 minutes)
- API Gateway latency (threshold: 2 seconds)
- Lambda errors (threshold: 5 in 5 minutes)
- Lambda throttles (threshold: 1 in 5 minutes)
- Lambda duration (threshold: 5 seconds)
- DynamoDB user errors (threshold: 10 in 5 minutes)
- DynamoDB system errors (threshold: 1 in 5 minutes)

### Viewing Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/collective-api-staging --follow

# View recent errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/collective-api-staging \
  --filter-pattern "ERROR"
```

## Troubleshooting

### Deployment Fails

1. **Check AWS credentials**:
   ```bash
   aws sts get-caller-identity
   ```

2. **Check CDK bootstrap**:
   ```bash
   aws cloudformation describe-stacks --stack-name CDKToolkit
   ```

3. **View deployment logs**:
   ```bash
   npm run cdk deploy AnnaDrishtiCollectiveStack --verbose
   ```

### Lambda Function Errors

1. **Check function logs**:
   ```bash
   aws logs tail /aws/lambda/collective-api-staging --follow
   ```

2. **Test function directly**:
   ```bash
   aws lambda invoke \
     --function-name collective-api-staging \
     --payload '{"httpMethod":"GET","path":"/health"}' \
     response.json
   ```

3. **Check environment variables**:
   ```bash
   aws lambda get-function-configuration \
     --function-name collective-api-staging \
     --query Environment
   ```

### DynamoDB Issues

1. **Check table status**:
   ```bash
   aws dynamodb describe-table --table-name collective-inventory-staging
   ```

2. **View table metrics**:
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/DynamoDB \
     --metric-name ConsumedReadCapacityUnits \
     --dimensions Name=TableName,Value=collective-inventory-staging \
     --start-time 2024-01-01T00:00:00Z \
     --end-time 2024-01-01T23:59:59Z \
     --period 3600 \
     --statistics Sum
   ```

### API Gateway Issues

1. **Check API deployment**:
   ```bash
   aws apigateway get-rest-apis
   ```

2. **Test API directly**:
   ```bash
   curl -v https://your-api-url/health
   ```

3. **Check API logs** (if enabled):
   ```bash
   aws logs tail /aws/apigateway/collective-selling-api-staging --follow
   ```

## Updating Deployment

### Update Lambda Code

```bash
# Make code changes in backend/collective/

# Rebuild and deploy
cd infrastructure
npm run build
npm run cdk deploy AnnaDrishtiCollectiveStack
```

### Update Infrastructure

```bash
# Make changes to CDK stacks in infrastructure/lib/

# Preview changes
npm run cdk diff AnnaDrishtiCollectiveStack

# Deploy changes
npm run cdk deploy AnnaDrishtiCollectiveStack
```

### Rollback Deployment

```bash
# List stack events
aws cloudformation describe-stack-events \
  --stack-name AnnaDrishtiCollectiveStack

# Rollback to previous version
aws cloudformation rollback-stack \
  --stack-name AnnaDrishtiCollectiveStack
```

## Cleanup

### Delete Staging Environment

```bash
# Delete monitoring stack first
npm run cdk destroy AnnaDrishtiMonitoringStack

# Delete collective stack
npm run cdk destroy AnnaDrishtiCollectiveStack
```

### Delete All Resources

```bash
# Delete all stacks
npm run cdk destroy --all

# Confirm deletion when prompted
```

**Note**: DynamoDB tables and RDS instances with deletion protection enabled must be manually deleted or have protection disabled first.

## Cost Optimization

### Staging Environment
- Use DynamoDB on-demand pricing
- Disable RDS (use DynamoDB only)
- Set short log retention (7 days)
- Use minimal Lambda memory (512 MB)

### Production Environment
- Consider DynamoDB provisioned capacity for predictable workloads
- Enable RDS only if relational queries are needed
- Use appropriate log retention (30 days)
- Optimize Lambda memory based on actual usage

## Security Best Practices

1. **API Authentication**: Implement API key or JWT authentication in production
2. **VPC**: Deploy Lambda in VPC if accessing RDS
3. **Secrets**: Store database credentials in AWS Secrets Manager
4. **IAM**: Use least privilege IAM roles
5. **Encryption**: Enable encryption at rest for DynamoDB and RDS
6. **CORS**: Restrict CORS origins in production

## Support

For issues or questions:
1. Check CloudWatch logs for errors
2. Review CloudWatch alarms for system health
3. Run smoke tests to verify endpoints
4. Check AWS service health dashboard

## Next Steps

After successful deployment:
1. Configure dashboard to use the new API URL
2. Test with sample data
3. Set up CI/CD pipeline for automated deployments
4. Configure backup and disaster recovery
5. Implement monitoring and alerting workflows
