# Enable AWS Bedrock Access (Updated)

## ✨ Good News!

AWS Bedrock models are now **automatically enabled** when first invoked. However, for Anthropic models (Claude), first-time users need to submit use case details.

## Quick Steps

### Option 1: Submit Use Case via Playground (Easiest)

1. **Go to Bedrock Playground**
   - Open: https://console.aws.amazon.com/bedrock
   - Region: `ap-south-1` (Mumbai)
   - Click "Playgrounds" in left sidebar
   - Click "Chat"

2. **Select Claude Model**
   - In the playground, select "Anthropic" as provider
   - Select "Claude 3 Haiku" model
   - Try to send a test message

3. **Fill Use Case Form**
   - You'll be prompted to fill out use case details
   - Fill in:
     - **Use case**: Agricultural technology / Farmer assistance
     - **Description**: AI-powered negotiation agent for helping Indian farmers get better prices for their produce
     - **Company**: Your company/personal name
     - **Email**: Your email
   - Submit the form

4. **Wait for Approval**
   - Usually instant or takes 5-15 minutes
   - You'll receive an email confirmation
   - Try the playground again to verify

### Option 2: Submit via API Call

Just run the test - it will trigger the form submission:

```bash
python3 test_full_workflow.py
```

If you see the error about use case details, go to the Bedrock console and you'll see a prompt to fill the form.

## Verify Access

After submitting the form, test again:

```bash
python3 test_full_workflow.py
```

You should see successful AI negotiation with counter-offers!

## What Changed?

**Old Process:**
- Manual model access request
- Wait for approval
- Enable each model individually

**New Process:**
- Models auto-enabled on first use
- Only Anthropic requires use case form (one-time)
- Instant access after form submission

## Troubleshooting

### "Model use case details have not been submitted"
✅ **Solution**: Go to Bedrock Playground → Try Claude → Fill form when prompted

### Form already submitted but still getting error
✅ **Solution**: Wait 5-10 minutes, then try again

### Want to use different region
✅ **Solution**: Try `us-east-1` (usually faster approval)

## Cost

Claude 3 Haiku pricing:
- Input: $0.00025 per 1K tokens (~₹0.02)
- Output: $0.00125 per 1K tokens (~₹0.10)

For hackathon demo (~100 negotiations):
- Estimated cost: ~₹50-100

## Next Steps

Once form is submitted and approved:
1. ✅ Test full workflow with AI negotiation
2. ✅ Verify 3-round negotiation works
3. ✅ Check floor price enforcement (₹24/kg)
4. Build React dashboard
5. Practice demo

---

**Status**: Waiting for use case form submission
**ETA**: Instant to 15 minutes after submission
**Action**: Go to Bedrock Playground and try Claude 3 Haiku
