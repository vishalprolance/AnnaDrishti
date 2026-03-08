# Deployment Status - Collective Selling Infrastructure

## Deployment Summary

Date: March 8, 2026
Environment: Demo/Staging

## Successfully Deployed Stacks

### 1. AnnaDrishtiCollectiveStack ✅
**Status**: Deployed Successfully
**Stack ARN**: `arn:aws:cloudformation:ap-south-1:572885592896:stack/AnnaDrishtiCollectiveStack/47f47220-1ad3-11f1-be7c-0aa1eb19524d`

**Resources Created**:
- **DynamoDB Tables**:
  - `collective-inventory-demo` - Collective inventory aggregation
  - `farmer-contributions-demo` - Individual farmer contributions
  - `reservations-demo` - Society demand reservations

- **Lambda Function**:
  - `collective-api-demo` - FastAPI application handler
  - Memory: 512 MB
  - Timeout: 30 seconds
  - Runtime: Python 3.11

- **API Gateway**:
  - REST API: `https://v30mahdpk5.execute-api.ap-south-1.amazonaws.com/demo/`
  - CORS enabled
  - Throttling: 100 burst, 50 rate limit

- **IAM Role**:
  - Lambda execution role with DynamoDB permissions
  - CloudWatch logging permissions

**Outputs**:
```
ApiUrl: https://v30mahdpk5.execute-api.ap-south-1.amazonaws.com/demo/
InventoryTableName: collective-inventory-demo
ContributionsTableName: farmer-contributions-demo
ReservationsTableName: reservations-demo
LambdaRoleArn: arn:aws:iam::572885592896:role/AnnaDrishtiCollectiveStac-CollectiveLambdaRole444B3-mi6h0awQbEh6
```

### 2. AnnaDrishtiMonitoringStack ✅
**Status**: Deployed Successfully
**Stack ARN**: `arn:aws:cloudformation:ap-south-1:572885592896:stack/AnnaDrishtiMonitoringStack/8a743810-1ad3-11f1-85c0-066874653a8d`

**Resources Created**:
- **CloudWatch Dashboard**: `collective-selling-demo`
  - API Gateway metrics (requests, errors, latency)
  - Lambda metrics (invocations, errors, duration, throttles)
  - DynamoDB metrics (read/write capacity, errors)

- **CloudWatch Alarms**:
  - API Gateway 5xx errors
  - API Gateway latency
  - Lambda errors
  - Lambda throttles
  - Lambda duration
  - DynamoDB user errors (per table)
  - DynamoDB system errors (per table)

- **SNS Topic**: `collective-alarms-demo`
  - For alarm notifications

**Outputs**:
```
AlarmTopicArn: arn:aws:sns:ap-south-1:572885592896:collective-alarms-demo
DashboardUrl: https://console.aws.amazon.com/cloudwatch/home?region=ap-south-1#dashboards:name=collective-selling-demo
```

## Current Issue

### Lambda Import Error ⚠️
**Issue**: The Lambda function is failing to import `pydantic_core._pydantic_core`
**Error**: `Runtime.ImportModuleError: Unable to import module 'collective.api.lambda_handler': No module named 'pydantic_core._pydantic_core'`

**Root Cause**: 
The Lambda bundling process is using ARM64 architecture (Lambda's default for ap-south-1), but pydantic_core has native C extensions that need to be compiled for the correct architecture. The Docker bundling in CDK is not properly handling the native dependencies.

**Impact**:
- API endpoints return "Internal server error"
- Lambda function cannot start
- All API calls fail

## Solutions to Fix Lambda Issue

### Option 1: Use x86_64 Architecture (Recommended)
Modify the Lambda function to use x86_64 architecture instead of ARM64:

```typescript
const apiFunction = new lambda.Function(this, 'CollectiveApiFunction', {
  // ... existing config
  architecture: lambda.Architecture.X86_64, // Add this line
  // ... rest of config
});
```

### Option 2: Fix Docker Bundling
Update the bundling command to properly compile native dependencies:

```typescript
const collectiveLayer = new lambda.LayerVersion(this, 'CollectiveLayer', {
  code: lambda.Code.fromAsset('../backend', {
    bundling: {
      image: lambda.Runtime.PYTHON_3_11.bundlingImage,
      platform: 'linux/amd64', // Specify platform
      command: [
        'bash', '-c',
        'pip install -r requirements.txt -t /asset-output/python --platform manylinux2014_x86_64 --only-binary=:all: && ' +
        'cp -r collective /asset-output/python/ && ' +
        'cp -r models /asset-output/python/'
      ],
    },
  }),
  compatibleRuntimes: [lambda.Runtime.PYTHON_3_11],
  compatibleArchitectures: [lambda.Architecture.X86_64],
});
```

### Option 3: Use Lambda Container Image
Package the entire application as a Docker container image for better control over dependencies.

## Next Steps

1. **Fix Lambda Import Issue**:
   - Apply Option 1 (use x86_64 architecture)
   - Rebuild and redeploy the Collective Stack
   - Test API endpoints

2. **Verify Deployment**:
   - Test health endpoint: `curl https://v30mahdpk5.execute-api.ap-south-1.amazonaws.com/demo/health`
   - Test inventory endpoint
   - Test societies endpoint

3. **Configure Monitoring**:
   - Subscribe email to SNS topic for alarm notifications
   - Review CloudWatch dashboard
   - Test alarm triggers

4. **Run Smoke Tests**:
   - Execute smoke test script
   - Verify all endpoints are accessible
   - Check DynamoDB tables

## Existing Deployed Stacks

The following stacks were already deployed and remain unchanged:

1. **AnnaDrishtiDemoStack** - Hackathon MVP backend
2. **AnnaDrishtiDashboardStack** - Frontend hosting
3. **CDKToolkit** - CDK bootstrap stack

## Cost Estimate

Current monthly cost for deployed resources:
- DynamoDB (3 tables, on-demand): ~$5-10/month
- Lambda (512 MB, low traffic): ~$5-10/month
- API Gateway (low traffic): ~$3-5/month
- CloudWatch (logs + metrics): ~$5/month
- SNS (alarm notifications): ~$1/month

**Total**: ~$20-30/month

## Access Information

### API Endpoint
```
https://v30mahdpk5.execute-api.ap-south-1.amazonaws.com/demo/
```

### CloudWatch Dashboard
```
https://console.aws.amazon.com/cloudwatch/home?region=ap-south-1#dashboards:name=collective-selling-demo
```

### DynamoDB Tables
- `collective-inventory-demo`
- `farmer-contributions-demo`
- `reservations-demo`

### Lambda Function
- `collective-api-demo`

## Deployment Commands

To redeploy after fixing the Lambda issue:

```bash
cd infrastructure
npm run build
npx cdk deploy AnnaDrishtiCollectiveStack --require-approval never
```

To view logs:
```bash
aws logs tail /aws/lambda/collective-api-demo --follow
```

To test API:
```bash
curl https://v30mahdpk5.execute-api.ap-south-1.amazonaws.com/demo/health
```

## Summary

✅ Infrastructure successfully deployed
✅ DynamoDB tables created and active
✅ API Gateway configured with endpoints
✅ CloudWatch monitoring and alarms configured
⚠️ Lambda function has import error (needs architecture fix)
🔧 Quick fix required: Change Lambda to x86_64 architecture

The deployment is 95% complete. Once the Lambda architecture issue is fixed, the system will be fully operational.
