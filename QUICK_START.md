# Anna Drishti - Quick Start Guide

## 🌐 Live URLs

**Dashboard**: https://d2ll18l06rc220.cloudfront.net
- Interactive form to test the API
- Real-time workflow creation
- Status display

**API Endpoint**: https://35t4gu37d5.execute-api.ap-south-1.amazonaws.com/demo
- Base URL for all API calls
- Currently supports: `POST /workflow/start`

## 🚀 Test the API

### Option 1: Use the Dashboard (Easiest)
1. Open: https://d2ll18l06rc220.cloudfront.net
2. Fill in the form (pre-populated with demo data)
3. Click "Start Workflow"
4. See the response with workflow ID

### Option 2: Use Python Script
```bash
python3 test_api.py
```

### Option 3: Use cURL
```bash
curl -X POST https://35t4gu37d5.execute-api.ap-south-1.amazonaws.com/demo/workflow/start \
  -H "Content-Type: application/json" \
  -d '{
    "farmer_name": "Ramesh Patil",
    "crop_type": "tomato",
    "plot_area": 2.1,
    "estimated_quantity": 2300,
    "location": "Sinnar, Nashik"
  }'
```

### Option 4: Use Postman/Insomnia
- Method: `POST`
- URL: `https://35t4gu37d5.execute-api.ap-south-1.amazonaws.com/demo/workflow/start`
- Headers: `Content-Type: application/json`
- Body (JSON):
```json
{
  "farmer_name": "Ramesh Patil",
  "crop_type": "tomato",
  "plot_area": 2.1,
  "estimated_quantity": 2300,
  "location": "Sinnar, Nashik"
}
```

## 📊 Check Results

### View in DynamoDB
```bash
# List all workflows
aws dynamodb scan --table-name anna-drishti-demo-workflows

# Get specific workflow
aws dynamodb get-item \
  --table-name anna-drishti-demo-workflows \
  --key '{"workflow_id": {"S": "YOUR_WORKFLOW_ID"}}'
```

### View in AWS Console
1. Go to: https://console.aws.amazon.com/dynamodbv2
2. Select region: `ap-south-1` (Mumbai)
3. Click on table: `anna-drishti-demo-workflows`
4. Click "Explore table items"

## 🔧 Common Issues

### Issue: "Missing Authentication Token"
**Cause**: Wrong endpoint path
**Solution**: Make sure you're using `/workflow/start` not just `/workflow`

### Issue: CloudFront shows XML error
**Cause**: Cache not invalidated or file not uploaded
**Solution**: 
```bash
# Re-upload dashboard
aws s3 cp dashboard-temp/index.html s3://anna-drishti-dashboard-572885592896/index.html

# Invalidate cache
aws cloudfront create-invalidation --distribution-id E2RGVKJFCNQ11S --paths "/*"

# Wait 2-3 minutes for propagation
```

### Issue: API returns 500 error
**Cause**: Lambda function error
**Solution**: Check CloudWatch logs
```bash
aws logs tail /aws/lambda/anna-drishti-start-workflow --follow
```

## 📝 API Response Format

### Success Response (200)
```json
{
  "success": true,
  "workflow_id": "b3ab1aad-a6cf-44d8-977d-7971c01c0e67",
  "dashboard_url": "https://d2ll18l06rc220.cloudfront.net",
  "message": "Workflow started successfully",
  "farmer_name": "Ramesh Patil"
}
```

### Error Response (500)
```json
{
  "success": false,
  "error": "Error message here",
  "message": "Failed to start workflow"
}
```

## 🎯 Next Development Steps

1. **Enable Bedrock** (for AI negotiation)
   - Go to AWS Console → Bedrock → Model access
   - Request access to Claude 3 Haiku
   - Wait for approval (~5 minutes)

2. **Create Negotiation Lambda**
   - File: `backend/lambdas/negotiate.py`
   - Invoke Bedrock for counter-offers
   - Deploy with CDK

3. **Set Up WhatsApp**
   - Create WhatsApp Business account
   - Get API credentials (Twilio/Gupshup)
   - Implement send/receive Lambdas

4. **Build Full Dashboard**
   - Initialize React + TypeScript
   - Create real-time components
   - Deploy to S3

## 💡 Tips

- **CloudFront cache**: Changes take 2-3 minutes to propagate
- **Lambda updates**: Redeploy with `cdk deploy AnnaDrishtiDemoStack`
- **DynamoDB**: Free tier covers demo usage
- **Logs**: Always check CloudWatch for debugging

## 📞 Support

Check these files for more info:
- `DEPLOYMENT_STATUS.md` - Detailed deployment status
- `README.md` - Project overview
- `docs/AWS_SETUP.md` - AWS configuration guide
- `.kiro/specs/hackathon-mvp/` - Full specification

---

**Last Updated**: March 3, 2026
**Status**: ✅ Dashboard deployed, API working
