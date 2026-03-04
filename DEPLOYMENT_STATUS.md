# Anna Drishti - Deployment Status

## ✅ Completed Infrastructure

### AWS Resources Deployed

**Backend Stack (AnnaDrishtiDemoStack)**
- ✅ API Gateway REST API: `https://35t4gu37d5.execute-api.ap-south-1.amazonaws.com/demo/`
- ✅ DynamoDB Table: `anna-drishti-demo-workflows`
- ✅ Lambda Layer: Shared dependencies and models
- ✅ Lambda Function: `anna-drishti-start-workflow`
- ✅ IAM Roles: Lambda execution role with Bedrock permissions
- ✅ CloudWatch Logs: Log groups for Lambda functions

**Dashboard Stack (AnnaDrishtiDashboardStack)**
- ✅ S3 Bucket: `anna-drishti-dashboard-572885592896`
- ✅ CloudFront Distribution: `https://d2ll18l06rc220.cloudfront.net`
- ✅ Origin Access Identity: Configured for secure S3 access

### Implemented Lambda Functions

1. **start_workflow.py** ✅
   - Endpoint: `POST /workflow/start`
   - Creates new workflow in DynamoDB
   - Returns workflow_id and dashboard URL
   - Status: TESTED AND WORKING

2. **scan_market.py** ✅
   - Market data scanner with Agmarknet integration
   - Mock data for demo (4 mandis: Sinnar, Nashik, Pune, Mumbai)
   - Calculates net-to-farmer prices
   - Status: IMPLEMENTED (not yet deployed)

3. **detect_surplus.py** ✅
   - Surplus detection logic
   - Processor capacity data (Sai Agro, Krishi Processing)
   - Recommends fresh vs processing split
   - Status: IMPLEMENTED (not yet deployed)

### Data Models Created

All Python data models in `backend/models/`:
- ✅ `farmer_input.py` - FarmerInput model
- ✅ `market_data.py` - MandiPrice, MarketScanResult
- ✅ `surplus_analysis.py` - SurplusAnalysis, ProcessorCapacity
- ✅ `negotiation.py` - NegotiationMessage, NegotiationResult
- ✅ `workflow.py` - WorkflowState, WorkflowStatus

## 🚧 Remaining Tasks for Hackathon MVP

### Critical Path (Must Have for Demo)

#### 1. Deploy Additional Lambda Functions
```bash
cd infrastructure
cdk deploy AnnaDrishtiDemoStack
```
This will deploy:
- scan_market Lambda
- detect_surplus Lambda

#### 2. Create Bedrock Negotiation Lambda
File: `backend/lambdas/negotiate.py`
- Invoke Bedrock Claude 3 Haiku
- Generate counter-offers with guardrails
- Floor price enforcement (₹24/kg)
- Max 3 message exchanges

#### 3. Create WhatsApp Integration Lambdas
Files needed:
- `backend/lambdas/send_whatsapp.py` - Send messages via WhatsApp API
- `backend/lambdas/handle_whatsapp_webhook.py` - Receive buyer responses

Requirements:
- WhatsApp Business API credentials (Twilio/Gupshup)
- Webhook URL configuration

#### 4. Build React Dashboard
```bash
# Create dashboard directory
npm create vite@latest dashboard -- --template react-ts

# Install dependencies
cd dashboard
npm install react-query recharts tailwindcss

# Build components:
- ActivityStream
- NegotiationChat
- SurplusPanel
- IncomeComparison
- ProcessingImpactViz
- GameTheorySimulation
```

#### 5. Deploy Dashboard to S3
```bash
cd dashboard
npm run build
aws s3 sync dist/ s3://anna-drishti-dashboard-572885592896/
aws cloudfront create-invalidation --distribution-id E2RGVKJFCNQ11S --paths "/*"
```

### Nice to Have (Optional)

- WebSocket API for real-time updates
- Step Functions state machine for workflow orchestration
- EventBridge rules for event publishing
- Reset button API endpoint
- Offline mode support

## 📊 Current Status Summary

**Phase 1 Progress: ~30% Complete**

✅ Completed (Hours 1-8):
- AWS account setup
- CDK infrastructure
- DynamoDB table
- Basic Lambda functions
- Data models
- API Gateway

🚧 In Progress (Hours 9-48):
- Additional Lambda functions
- Bedrock integration
- WhatsApp integration
- React dashboard
- Real-time updates
- Demo polish

## 🔑 Key Information

### API Endpoints

**Base URL**: `https://35t4gu37d5.execute-api.ap-south-1.amazonaws.com/demo`

**Available Endpoints**:
- `POST /workflow/start` - Start new workflow ✅ WORKING

**Test Command**:
```bash
python3 test_api.py
```

### AWS Resources

**Region**: `ap-south-1` (Mumbai)

**Account ID**: `572885592896`

**DynamoDB Table**: `anna-drishti-demo-workflows`

**S3 Bucket**: `anna-drishti-dashboard-572885592896`

**CloudFront URL**: `https://d2ll18l06rc220.cloudfront.net`

### Environment Variables Needed

**Backend** (`backend/.env`):
```
AWS_REGION=ap-south-1
DYNAMODB_TABLE=anna-drishti-demo-workflows
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
WHATSAPP_API_KEY=<your_key>
WHATSAPP_PHONE_NUMBER=<your_number>
```

**Dashboard** (`dashboard/.env`):
```
VITE_API_URL=https://35t4gu37d5.execute-api.ap-south-1.amazonaws.com/demo
VITE_WS_URL=wss://placeholder-websocket-url
VITE_MAPBOX_TOKEN=<your_token>
```

## 🎯 Next Steps to Complete MVP

### Immediate (Next 2-4 hours)

1. **Enable Bedrock Access**
   ```bash
   # Go to AWS Console → Bedrock → Model access
   # Request access to Claude 3 Haiku
   ```

2. **Create Negotiation Lambda**
   - Implement Bedrock invocation
   - Add guardrails and floor price logic
   - Deploy to AWS

3. **Set Up WhatsApp**
   - Create WhatsApp Business account
   - Get API credentials
   - Implement send/receive Lambdas

### Short Term (Next 8-12 hours)

4. **Build Dashboard**
   - Initialize Vite + React + TypeScript
   - Create core components
   - Implement API integration
   - Add mock data for visualization

5. **Deploy Dashboard**
   - Build production bundle
   - Upload to S3
   - Invalidate CloudFront cache
   - Test live URL

### Before Demo (Final 24 hours)

6. **Integration Testing**
   - Test full workflow end-to-end
   - Verify Bedrock negotiation
   - Test WhatsApp integration
   - Check dashboard updates

7. **Demo Preparation**
   - Create demo script
   - Prepare backup video
   - Test on venue WiFi
   - Practice 4-minute presentation

## 💰 Cost Estimate

**Current Spend**: ~₹50 (infrastructure deployment)

**Estimated Total for Hackathon**: ₹100-200
- Lambda: Free tier
- DynamoDB: Free tier
- API Gateway: Free tier
- S3: Free tier
- CloudFront: ~₹50
- Bedrock: ~₹50 (based on usage)

## 🆘 Troubleshooting

### API Returns 500 Error
- Check CloudWatch logs: `/aws/lambda/anna-drishti-start-workflow`
- Verify DynamoDB table exists
- Check IAM permissions

### Lambda Deployment Fails
- Ensure Docker is running (for CDK bundling)
- Check `backend/requirements.txt` is valid
- Verify AWS credentials are configured

### Dashboard Not Loading
- Check S3 bucket permissions
- Verify CloudFront distribution is deployed
- Check browser console for errors

## 📚 Documentation

- **AWS Setup Guide**: `docs/AWS_SETUP.md`
- **README**: `README.md`
- **Spec**: `.kiro/specs/hackathon-mvp/`
- **Tasks**: `.kiro/specs/hackathon-mvp/tasks.md`

## 🎉 Success Criteria

The MVP is ready for demo when:
- ✅ API accepts farmer input
- ⏳ Bedrock negotiation works live
- ⏳ Dashboard shows real-time updates
- ⏳ Processing math is clear
- ⏳ Demo completes in 4 minutes

---

**Last Updated**: March 3, 2026
**Status**: Infrastructure deployed, Lambda functions partially implemented
**Next Milestone**: Complete Bedrock integration and dashboard
