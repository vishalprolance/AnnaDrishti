# Anna Drishti Infrastructure

AWS CDK infrastructure for the hackathon MVP.

## Setup

```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# List stacks
cdk ls

# Show what will be deployed
cdk diff

# Deploy backend
cdk deploy AnnaDrishtiDemoStack

# Deploy dashboard
cdk deploy AnnaDrishtiDashboardStack

# Deploy all
cdk deploy --all
```

## Stacks

### AnnaDrishtiDemoStack
Backend infrastructure:
- DynamoDB table for workflow state
- Lambda layer with shared code
- IAM roles with Bedrock permissions
- API Gateway (REST)
- CloudWatch logs

### AnnaDrishtiDashboardStack
Frontend hosting:
- S3 bucket for static files
- CloudFront distribution
- Origin Access Identity

## Outputs

After deployment, you'll get:
- `ApiUrl` - REST API endpoint
- `WorkflowTableName` - DynamoDB table name
- `DashboardUrl` - CloudFront URL
- `SharedLayerArn` - Lambda layer ARN

## Clean Up

```bash
# Destroy all resources
cdk destroy --all
```

## Cost Estimate

For 48-hour hackathon:
- DynamoDB: Free tier
- Lambda: Free tier
- API Gateway: Free tier
- S3: Free tier
- CloudFront: ~₹50
- Bedrock: ~₹50

Total: ~₹100-200
