# OpenAI Setup Guide

## Overview

The negotiation Lambda has been switched from AWS Bedrock to OpenAI GPT-4o-mini due to Bedrock payment verification issues.

---

## Step 1: Get OpenAI API Key

### Option A: If you already have an OpenAI account
1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Give it a name (e.g., "Anna Drishti Negotiation")
4. Copy the API key (starts with `sk-...`)
5. **IMPORTANT**: Save it securely - you won't see it again!

### Option B: If you need to create an account
1. Go to https://platform.openai.com/signup
2. Sign up with email or Google/Microsoft account
3. Verify your email
4. Add payment method (required for API access)
5. Go to https://platform.openai.com/api-keys
6. Click "Create new secret key"
7. Copy the API key (starts with `sk-...`)

---

## Step 2: Set Environment Variable

### On Your Local Machine (for deployment)

**macOS/Linux**:
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

**To make it permanent**, add to `~/.zshrc` or `~/.bashrc`:
```bash
echo 'export OPENAI_API_KEY="sk-your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

**Windows (PowerShell)**:
```powershell
$env:OPENAI_API_KEY="sk-your-api-key-here"
```

**Windows (Command Prompt)**:
```cmd
set OPENAI_API_KEY=sk-your-api-key-here
```

---

## Step 3: Deploy Lambda with API Key

Once you've set the environment variable, deploy the updated Lambda:

```bash
cd infrastructure
npx cdk deploy AnnaDrishtiDemoStack --require-approval never
```

The CDK will automatically pick up the `OPENAI_API_KEY` environment variable and add it to the Lambda function.

---

## Step 4: Verify Deployment

Check that the API key is set in the Lambda:

```bash
aws lambda get-function-configuration \
  --function-name anna-drishti-negotiate \
  --query 'Environment.Variables.OPENAI_API_KEY' \
  --output text
```

You should see your API key (partially masked).

---

## Step 5: Test AI Negotiation

Run the test script to verify AI negotiation is working:

```bash
python3 test_full_workflow.py
```

You should see:
```
✅ Negotiation completed
Offer: ₹XX.XX/kg
Message: "I can offer ₹XX.XX/kg for this quality produce..."
```

---

## Model Configuration

**Model**: GPT-4o-mini
- **Why**: Cost-effective, fast, good quality
- **Cost**: $0.15 per 1M input tokens, $0.60 per 1M output tokens
- **Typical negotiation**: ~$0.0001 per request (₹0.008)

**Alternative Models** (if you want to change):
- `gpt-4o`: Higher quality, more expensive ($2.50/$10 per 1M tokens)
- `gpt-3.5-turbo`: Cheaper, lower quality ($0.50/$1.50 per 1M tokens)

To change model, update `infrastructure/lib/demo-stack.ts`:
```typescript
OPENAI_MODEL: 'gpt-4o',  // or 'gpt-3.5-turbo'
```

---

## Cost Estimate

### GPT-4o-mini Pricing
- **Input**: $0.15 per 1M tokens (~$0.000045 per negotiation)
- **Output**: $0.60 per 1M tokens (~$0.000060 per negotiation)
- **Total**: ~$0.0001 per negotiation (₹0.008)

### Monthly Estimate
- **100 negotiations/day**: $0.30/month (₹25/month)
- **500 negotiations/day**: $1.50/month (₹125/month)
- **1000 negotiations/day**: $3/month (₹250/month)

**Very affordable** - Much cheaper than Bedrock!

---

## Security Best Practices

### DO:
✅ Store API key in environment variables
✅ Use AWS Secrets Manager for production (optional)
✅ Rotate API keys periodically
✅ Monitor usage on OpenAI dashboard
✅ Set usage limits on OpenAI account

### DON'T:
❌ Commit API key to Git
❌ Share API key publicly
❌ Hardcode API key in code
❌ Use same key for multiple projects

---

## Troubleshooting

### Error: "OpenAI API key not configured"
**Solution**: Set the `OPENAI_API_KEY` environment variable before deploying

### Error: "Incorrect API key provided"
**Solution**: Check that your API key is correct and starts with `sk-`

### Error: "You exceeded your current quota"
**Solution**: Add payment method to OpenAI account or increase quota

### Error: "Rate limit exceeded"
**Solution**: Wait a few seconds and retry. The Lambda has automatic retry logic.

### Error: "Connection timeout"
**Solution**: Check internet connectivity. Lambda has 30-second timeout for OpenAI API.

---

## Monitoring

### Check OpenAI Usage
1. Go to https://platform.openai.com/usage
2. View API usage by day/month
3. Monitor costs in real-time

### Check Lambda Logs
```bash
aws logs tail /aws/lambda/anna-drishti-negotiate --follow
```

### Check CloudWatch Metrics
- `OpenAIInvocationSuccess` - Successful API calls
- `OpenAIInvocationFailed` - Failed API calls
- `NegotiationLatency` - Response time

---

## Migration from Bedrock

### What Changed
- ✅ Switched from AWS Bedrock to OpenAI
- ✅ Using GPT-4o-mini instead of Claude 4.5 Haiku
- ✅ Same API interface (no frontend changes needed)
- ✅ Same negotiation logic and guardrails
- ✅ Same prompt engineering

### What Stayed the Same
- ✅ Floor price enforcement (₹24/kg)
- ✅ Max exchanges (3 rounds)
- ✅ Negotiation messages format
- ✅ DynamoDB storage
- ✅ CloudWatch metrics
- ✅ Error handling

### Benefits of OpenAI
- ✅ No AWS payment verification needed
- ✅ Faster setup (just need API key)
- ✅ Cheaper than Bedrock
- ✅ More flexible (can switch models easily)
- ✅ Better documentation

---

## Next Steps

1. **Get OpenAI API key** from https://platform.openai.com/api-keys
2. **Set environment variable**: `export OPENAI_API_KEY="sk-..."`
3. **Deploy Lambda**: `cd infrastructure && npx cdk deploy AnnaDrishtiDemoStack`
4. **Test negotiation**: `python3 test_full_workflow.py`
5. **Monitor usage**: https://platform.openai.com/usage

---

## Support

### OpenAI Support
- Documentation: https://platform.openai.com/docs
- Community: https://community.openai.com
- Status: https://status.openai.com

### Anna Drishti Support
- Check Lambda logs: `aws logs tail /aws/lambda/anna-drishti-negotiate --follow`
- Check CloudWatch metrics: AWS Console → CloudWatch → Metrics → AnnaDrishti/Negotiation
- Test API: `python3 test_full_workflow.py`

---

**Last Updated**: March 7, 2026  
**Status**: Ready for deployment (waiting for API key)
