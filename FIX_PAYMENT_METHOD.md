# Fix AWS Payment Method for Bedrock

## Issue

AWS Bedrock requires a valid payment instrument (credit/debit card) to be added to your account, even though Claude 3 Haiku usage will be minimal and likely within free tier.

**Error**: `INVALID_PAYMENT_INSTRUMENT: A valid payment instrument must be provided`

## Solution: Add Payment Method

### Step 1: Add Credit/Debit Card

1. **Go to AWS Billing Console**
   ```
   https://console.aws.amazon.com/billing/home#/paymentmethods
   ```

2. **Add Payment Method**
   - Click "Add a payment method"
   - Enter your credit/debit card details
   - Click "Verify and add"

3. **Set as Default** (if you have multiple cards)
   - Select the card you just added
   - Click "Make default"

### Step 2: Verify Account Status

1. **Check Account Status**
   ```
   https://console.aws.amazon.com/billing/home#/account
   ```

2. **Ensure**:
   - Payment method is verified ✅
   - Account is in good standing ✅
   - No outstanding payments ✅

### Step 3: Wait and Test

After adding payment method:

```bash
# Wait 2-3 minutes for AWS to process
sleep 180

# Test Bedrock access
python3 check_bedrock.py
```

## Cost Estimate

Don't worry about costs - Bedrock usage for this hackathon will be minimal:

**Claude 3 Haiku Pricing:**
- Input: $0.00025 per 1K tokens (~₹0.02)
- Output: $0.00125 per 1K tokens (~₹0.10)

**For 100 negotiations (hackathon demo):**
- ~50K input tokens = ₹1
- ~30K output tokens = ₹3
- **Total: ~₹4-5**

**For development/testing (500 calls):**
- **Total: ~₹20-25**

**AWS Free Tier:**
- First 2 months: 200K input tokens free
- First 2 months: 100K output tokens free
- Your usage will likely be FREE!

## Alternative: Use Different AWS Account

If you can't add a payment method to this account:

1. **Create New AWS Account**
   - Go to: https://aws.amazon.com/free
   - Sign up with different email
   - Add payment method during signup

2. **Deploy to New Account**
   ```bash
   # Configure new AWS credentials
   aws configure --profile new-account
   
   # Deploy infrastructure
   cd infrastructure
   AWS_PROFILE=new-account cdk deploy --all
   ```

3. **Update Test Scripts**
   ```bash
   # Add to test scripts
   export AWS_PROFILE=new-account
   python3 test_full_workflow.py
   ```

## Troubleshooting

### "Payment method not verified"
- Check your email for verification link
- Wait 5-10 minutes after adding card
- Try a different card if verification fails

### "Account suspended"
- Check for outstanding payments
- Contact AWS support: https://console.aws.amazon.com/support

### "Still getting payment error after adding card"
- Wait 5 minutes for AWS to process
- Clear AWS CLI cache: `rm -rf ~/.aws/cli/cache`
- Try again: `python3 check_bedrock.py`

## Next Steps

Once payment method is added:

1. ✅ Run: `python3 check_bedrock.py`
2. ✅ Should see: "SUCCESS! Bedrock is working!"
3. ✅ Test full workflow: `python3 test_full_workflow.py`
4. ✅ Build React dashboard
5. ✅ Practice demo

---

**Action Required**: Add payment method to AWS account
**Cost Impact**: ~₹4-5 for hackathon (likely FREE with free tier)
**Time**: 5 minutes to add card + 2-3 minutes to process
