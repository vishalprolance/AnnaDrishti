# AWS Cost Analysis - What's Running

## 💰 Current AWS Resources

### Free Tier / No Cost When Idle
These resources cost nothing when not in use:

1. **Lambda Functions** (4 functions)
   - Only charged per invocation
   - No cost when idle
   - ✅ **Keep running** - no need to shut down

2. **API Gateway**
   - Only charged per API call
   - No cost when idle
   - ✅ **Keep running** - no need to shut down

3. **DynamoDB Table**
   - Free tier: 25 GB storage, 25 read/write units
   - Current usage: ~1 MB (well within free tier)
   - ✅ **Keep running** - no cost

4. **CloudWatch Logs**
   - Free tier: 5 GB ingestion, 5 GB storage
   - Current usage: ~10 MB
   - ✅ **Keep running** - no cost

### Minimal Cost (Always Running)
These resources have small ongoing costs:

5. **CloudFront Distribution**
   - Cost: ~$0.01-0.10 per day (₹1-8/day)
   - Free tier: 1 TB data transfer out per month
   - Current usage: Minimal (just dashboard HTML)
   - ✅ **Keep running** - cost is negligible

6. **S3 Bucket** (Dashboard hosting)
   - Cost: ~$0.001 per day (₹0.08/day)
   - Free tier: 5 GB storage, 20,000 GET requests
   - Current usage: ~100 KB
   - ✅ **Keep running** - cost is negligible

## 📊 Total Daily Cost

**Current daily cost: ~₹1-10 per day**

All resources are either:
- Within AWS free tier, OR
- Have negligible cost when idle

## 🎯 Recommendation

**DO NOT shut down anything!**

Reasons:
1. Everything is within free tier or costs pennies
2. Redeploying tomorrow takes 5-10 minutes
3. Your API URLs and CloudFront URLs will stay the same
4. DynamoDB data is preserved
5. No benefit to shutting down

## 💡 What You WOULD Shut Down (If Needed)

If you wanted to minimize costs (not necessary), you could:

```bash
# Delete CloudFront distribution (saves ~₹1-8/day)
aws cloudfront delete-distribution --id E2RGVKJFCNQ11S

# Delete entire stack (removes everything)
cd infrastructure
npm run cdk destroy AnnaDrishtiDemoStack
npm run cdk destroy AnnaDrishtiDashboardStack
```

**But DON'T do this!** The cost is negligible and you'll need everything tomorrow.

## 📅 Tomorrow's Plan

When you continue tomorrow:

1. **Verify payment method** in AWS Console
   - https://console.aws.amazon.com/billing/home#/paymentmethods

2. **Test Bedrock access**
   ```bash
   python3 test_bedrock_direct.py
   ```

3. **Test full workflow**
   ```bash
   python3 test_full_workflow.py
   ```

4. **Continue with dashboard** (if Bedrock works)
   - Build React dashboard
   - Practice demo

## 🔒 Security Note

Your AWS resources are secure:
- API has CORS enabled (only your domains)
- Lambda has minimal IAM permissions
- DynamoDB has encryption at rest
- No public write access anywhere

## 💳 Billing Alert (Optional)

If you want peace of mind, set up a billing alert:

1. Go to: https://console.aws.amazon.com/billing/home#/budgets
2. Click "Create budget"
3. Set alert at $5 (₹400)
4. You'll get email if costs exceed this

Current estimate: You'll spend ~₹30-100 total for the entire hackathon project.

---

**Summary**: Leave everything running. Cost is negligible (~₹1-10/day). Everything will be ready when you continue tomorrow.
