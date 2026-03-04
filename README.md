# Anna Drishti (अन्नदृष्टि) - AI-Assisted Selling for Indian Farmers

> "Your farmer doesn't need another dashboard. They need someone who picks up the phone and gets them a better deal. We built that someone."

## Project Overview

Anna Drishti is an AI-assisted selling and surplus management system for Farmer Producer Organizations (FPOs). It operates via IVR and WhatsApp to:

1. **Sell Agent** - Find the best buyer and negotiate the best price
2. **Process Agent** - Divert surplus to processing before market crashes

## Current Status: Phase 1 - Hackathon MVP (48 Hours)

Building a working demo to win the hackathon. Focus on:
- ✅ Live AI negotiation (AWS Bedrock)
- ✅ Real market data (Agmarknet API)
- ✅ Processing surplus detection
- ✅ Real-time dashboard

## Project Structure

```
anna-drishti/
├── backend/              # Python Lambda functions
│   ├── agents/          # Sell Agent, Process Agent
│   ├── integrations/    # Agmarknet, WhatsApp, Bedrock
│   └── models/          # Data models
├── dashboard/           # React + TypeScript frontend
│   ├── src/
│   │   ├── components/  # UI components
│   │   ├── features/    # Feature modules
│   │   └── services/    # API clients
├── infrastructure/      # AWS CDK
│   ├── lib/
│   │   ├── demo-stack.ts
│   │   └── dashboard-stack.ts
└── .kiro/specs/        # Full specifications
    ├── hackathon-mvp/  # Phase 1 (current)
    └── [8 full specs]  # Phase 3 (production)
```

## Quick Start

### Prerequisites

- AWS Account with admin access
- Node.js 18+ and Python 3.11+
- AWS CLI configured
- AWS CDK installed

### Setup (Hour 1-4)

```bash
# 1. Configure AWS CLI
aws configure
# Enter: Access Key ID, Secret Access Key, Region (ap-south-1), Output (json)

# 2. Install dependencies
npm install -g aws-cdk
pip install aws-cdk-lib constructs

# 3. Bootstrap CDK (first time only)
cd infrastructure
cdk bootstrap

# 4. Install project dependencies
cd ../backend
pip install -r requirements.txt

cd ../dashboard
npm install
```

## Phase 1 Implementation Plan

**Day 1 (Hours 1-24): Core Infrastructure**
- [x] AWS setup and project structure
- [ ] DynamoDB tables
- [ ] Market data scanner (Agmarknet)
- [ ] Surplus detection logic
- [ ] Step Functions workflow

**Day 2 (Hours 25-48): AI & Dashboard**
- [ ] WhatsApp + Bedrock integration
- [ ] Real-time dashboard
- [ ] Processing visualization
- [ ] Game theory simulation
- [ ] Demo polish & testing

## AWS Services Used

- **Step Functions** - Workflow orchestration
- **Lambda** - Agent logic (Python 3.11)
- **Bedrock** - Claude 3 Haiku for negotiation
- **DynamoDB** - State storage
- **API Gateway** - REST + WebSocket
- **S3 + CloudFront** - Dashboard hosting
- **EventBridge** - Event bus for real-time updates

## Demo Flow (12 Minutes)

1. **Problem Setup** (2 min) - Farmer distress, agency gap
2. **Live Demo** (5 min) - Sell Agent negotiation on WhatsApp
3. **Processing Pivot** (2 min) - Crash prevention visualization
4. **Game Theory** (1 min) - Coordination simulation
5. **Close** (2 min) - Roadmap and impact

## Key Metrics

**For One Farmer (Demo Scenario):**
- Nearest mandi: ₹36,800
- Anna Drishti: ₹63,200
- **Difference: +₹26,400** (72% increase)

**For FPO (14 Farmers):**
- Without processing: ₹2.1 crore (crash scenario)
- With processing: ₹3.4 crore (stable prices)
- **Difference: +₹1.3 crore** (62% increase)

## Development Commands

```bash
# Backend
cd backend
python -m pytest                    # Run tests
python -m agents.sell_agent         # Test sell agent locally

# Dashboard
cd dashboard
npm run dev                         # Start dev server
npm run build                       # Build for production
npm run preview                     # Preview production build

# Infrastructure
cd infrastructure
cdk diff                           # Show changes
cdk deploy DemoStack              # Deploy backend
cdk deploy DashboardStack         # Deploy frontend
cdk destroy                       # Clean up resources
```

## Environment Variables

Create `.env` files in each directory:

**backend/.env**
```
AWS_REGION=ap-south-1
DYNAMODB_TABLE=anna-drishti-demo
WHATSAPP_API_KEY=your_key_here
WHATSAPP_PHONE_NUMBER=+91XXXXXXXXXX
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
AGMARKNET_BASE_URL=https://agmarknet.gov.in
DEMO_OFFLINE_MODE=false
```

**dashboard/.env**
```
VITE_API_URL=https://your-api-gateway-url
VITE_WS_URL=wss://your-websocket-url
VITE_MAPBOX_TOKEN=your_mapbox_token
```

## Testing

**Phase 1 (Hackathon):** Manual testing only
- Test each Lambda function individually
- Test Step Functions workflow end-to-end
- Test dashboard with real WebSocket events
- Rehearse full demo (4 minutes)

**Phase 2 (Post-Hackathon):** Basic unit tests
- 50% code coverage target
- Focus on critical paths

**Phase 3 (Production):** Comprehensive testing
- Unit tests + Property-based tests
- Integration tests + E2E tests
- 90% code coverage target

## Deployment

```bash
# Deploy everything
cd infrastructure
cdk deploy --all

# Get dashboard URL
aws cloudformation describe-stacks \
  --stack-name DashboardStack \
  --query 'Stacks[0].Outputs[?OutputKey==`DashboardUrl`].OutputValue' \
  --output text
```

## Demo Checklist

Before going on stage:
- [ ] Reset demo state
- [ ] Test internet connection
- [ ] Test WhatsApp on team phone
- [ ] Verify AWS services are running
- [ ] Load dashboard on presentation laptop
- [ ] Have backup video ready
- [ ] Practice narration (4 minutes)

## Troubleshooting

**WhatsApp not sending:**
- Check API credentials in Secrets Manager
- Verify webhook is registered
- Test with WhatsApp sandbox first

**Bedrock not responding:**
- Verify model access is enabled
- Check IAM permissions
- Test with sample prompt in console

**Dashboard not updating:**
- Check WebSocket connection status
- Verify EventBridge rules are active
- Check CloudWatch logs for errors

**Offline mode:**
- Set `DEMO_OFFLINE_MODE=true`
- Uses cached market data
- Simulates WhatsApp messages

## Phase Roadmap

**Phase 1: Hackathon MVP** (48 hours) ← **YOU ARE HERE**
- Goal: Win the demo
- Scope: ~50 tasks
- Testing: Manual only

**Phase 2: Post-Hackathon** (2 weeks)
- Goal: Real integrations
- Add: IVR, Satellite API, Auth
- Testing: Basic unit tests

**Phase 3: Production** (3 months)
- Goal: 1 FPO pilot (500 farmers)
- Scope: All 8 full specs
- Testing: Comprehensive

## Contributing

This is a hackathon project. After Phase 1, we'll open for contributions.

## License

MIT License - See LICENSE file

## Contact

For questions during hackathon: [Your contact info]

---

**Built with ❤️ for Indian farmers**
