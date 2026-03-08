# Anna Drishti Infrastructure

AWS CDK infrastructure for Anna Drishti platform, including:
- Hackathon MVP (Demo Stack)
- Collective Selling & Allocation System
- Monitoring & Alerting
- Dashboard Hosting

## Quick Start

### Prerequisites
- AWS CLI configured with credentials
- Node.js 18+ installed
- AWS CDK CLI installed: `npm install -g aws-cdk`

### Deploy to Staging

```bash
# Install dependencies
npm install

# Deploy collective selling system
cd scripts
./deploy-staging.sh
```

### Deploy Specific Stack

```bash
# Build TypeScript
npm run build

# Deploy collective stack
npm run cdk deploy AnnaDrishtiCollectiveStack

# Deploy monitoring
npm run cdk deploy AnnaDrishtiMonitoringStack
```

## Stacks

### 1. Demo Stack (AnnaDrishtiDemoStack)
Hackathon MVP infrastructure with Lambda functions for:
- Workflow management
- Market scanning
- Surplus detection
- AI negotiation
- IVR handling
- Farmer portfolio
- Payment tracking
- Satellite data

### 2. Collective Stack (AnnaDrishtiCollectiveStack)
Collective Selling & Allocation system with:
- DynamoDB tables for real-time inventory
- Lambda function for FastAPI application
- API Gateway with REST endpoints
- Optional PostgreSQL RDS for relational data

### 3. Monitoring Stack (AnnaDrishtiMonitoringStack)
Monitoring and alerting with:
- CloudWatch dashboard with key metrics
- CloudWatch alarms for errors and latency
- SNS topic for alarm notifications

### 4. Dashboard Stack (AnnaDrishtiDashboardStack)
Frontend hosting for React dashboard

## Configuration

### Environment Files
- `.env.example`: Template for environment variables
- `config/staging.json`: Staging environment configuration
- `config/production.json`: Production environment configuration

### Scripts
- `scripts/setup-env.sh`: Configure environment variables
- `scripts/deploy-staging.sh`: Automated staging deployment
- `scripts/export-lambda-env.sh`: Export Lambda environment variables
- `scripts/smoke-test.sh`: Run smoke tests after deployment

## Documentation

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for detailed deployment instructions.

## Commands

```bash
# Build TypeScript
npm run build

# Watch for changes
npm run watch

# List all stacks
npm run cdk list

# Show diff for a stack
npm run cdk diff AnnaDrishtiCollectiveStack

# Deploy a stack
npm run cdk deploy AnnaDrishtiCollectiveStack

# Deploy all stacks
npm run cdk deploy --all

# Destroy a stack
npm run cdk destroy AnnaDrishtiCollectiveStack
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AWS Cloud                                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │  API Gateway │─────▶│   Lambda     │                    │
│  │              │      │  (FastAPI)   │                    │
│  └──────────────┘      └──────┬───────┘                    │
│                                │                             │
│                    ┌───────────┴───────────┐                │
│                    │                       │                │
│           ┌────────▼────────┐    ┌────────▼────────┐       │
│           │   DynamoDB      │    │   PostgreSQL    │       │
│           │   (Inventory)   │    │   (Optional)    │       │
│           └─────────────────┘    └─────────────────┘       │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              CloudWatch Monitoring                    │  │
│  │  - Dashboard  - Alarms  - Logs  - Metrics           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Resources Created

### DynamoDB Tables
- `collective-inventory-{env}`: Collective inventory aggregation
- `farmer-contributions-{env}`: Individual farmer contributions
- `reservations-{env}`: Society demand reservations

### Lambda Functions
- `collective-api-{env}`: Main API handler (FastAPI)

### API Gateway
- REST API with proxy integration
- CORS enabled
- Throttling configured

### CloudWatch
- Log groups for Lambda functions
- Custom dashboard with metrics
- Alarms for errors and latency

### Optional: RDS
- PostgreSQL database for relational data
- VPC with public/private subnets
- Security groups for database access

## Cost Estimation

### Staging (Minimal Usage)
- DynamoDB: ~$5-10/month (on-demand)
- Lambda: ~$5-10/month (512 MB, low traffic)
- API Gateway: ~$3-5/month (low traffic)
- CloudWatch: ~$5/month (logs + metrics)
- **Total**: ~$20-30/month

### Production (Moderate Usage)
- DynamoDB: ~$50-100/month
- Lambda: ~$20-50/month
- API Gateway: ~$10-20/month
- RDS (if enabled): ~$50-100/month
- CloudWatch: ~$10-20/month
- **Total**: ~$140-290/month

## Security

- IAM roles with least privilege
- Secrets stored in AWS Secrets Manager
- VPC for RDS access
- Encryption at rest for DynamoDB
- API authentication (to be implemented)

## Support

For deployment issues:
1. Check CloudWatch logs
2. Run smoke tests
3. Review deployment guide
4. Check AWS service health

## License

MIT
