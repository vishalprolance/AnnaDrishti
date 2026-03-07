# IVR Implementation - Next Steps

## ✅ Completed

1. **IVR Handler Lambda** - Deployed successfully
   - Function ARN: `arn:aws:lambda:ap-south-1:572885592896:function:anna-drishti-ivr-handler`
   - Handles Lex bot input
   - Creates workflows in DynamoDB
   - Sends SMS notifications
   - Production-grade error handling

2. **IAM Permissions** - Configured
   - DynamoDB read/write
   - SNS publish (for SMS)
   - CloudWatch metrics
   - Lex invoke permissions

---

## 🔄 Manual Steps Required (AWS Console)

### Step 1: Set Up Amazon Connect Instance (15 mins)

**Go to**: AWS Console → Amazon Connect

1. **Create instance**:
   - Instance alias: `anna-drishti-ivr`
   - Identity management: Store users in Amazon Connect
   - Create admin user
   - Enable incoming calls
   - Use default S3 bucket

2. **Claim phone number**:
   - Go to: Channels → Phone numbers
   - Click "Claim a number"
   - Country: India (+91)
   - Type: Toll-free or Local
   - Save the number: **+91-XXXX-XXXXXX**

---

### Step 2: Create Lex Bot (30 mins)

**Go to**: AWS Console → Amazon Lex V2

1. **Create bot**:
   - Name: `AnnaDrishtiFarmerBot`
   - Language: Hindi (hi_IN)
   - IAM role: Create new

2. **Create intent**: `CollectFarmerInfo`

3. **Add sample utterances** (Hindi):
   ```
   मैं अपनी फसल बेचना चाहता हूं
   मुझे बाजार की कीमत चाहिए
   मेरे पास टमाटर है
   मैं किसान हूं
   ```

4. **Add slots**:

   **farmer_name**:
   - Type: AMAZON.FirstName
   - Prompt: "आपका नाम क्या है?"
   - Required: Yes

   **crop_type**:
   - Type: Custom (create new)
   - Values: टमाटर, प्याज, मिर्च
   - Prompt: "आप कौन सी फसल बेचना चाहते हैं?"
   - Required: Yes

   **quantity**:
   - Type: AMAZON.Number
   - Prompt: "कितने किलो है?"
   - Required: Yes

   **plot_area**:
   - Type: AMAZON.Number
   - Prompt: "आपके खेत का क्षेत्रफल कितना है? एकड़ में बताएं।"
   - Required: Yes

   **location**:
   - Type: AMAZON.City
   - Prompt: "आप कहां से हैं?"
   - Required: Yes

5. **Confirmation prompt**:
   ```
   तो {farmer_name}, आपके पास {quantity} किलो {crop_type} है, {plot_area} एकड़ में, {location} से। क्या यह सही है?
   ```

6. **Fulfillment**:
   - Lambda function: `anna-drishti-ivr-handler`
   - ARN: `arn:aws:lambda:ap-south-1:572885592896:function:anna-drishti-ivr-handler`

7. **Build bot** (takes 2-3 minutes)

8. **Create alias**:
   - Name: "Production"
   - Associate with Lambda

---

### Step 3: Create Contact Flow in Amazon Connect (20 mins)

**Go to**: Connect instance → Routing → Contact flows

1. **Create contact flow**: `AnnaDrishtiFarmerFlow`

2. **Add blocks**:

   a. **Set voice**:
      - Language: Hindi (hi-IN)
      - Voice: Aditi

   b. **Play prompt**:
      - Text: "नमस्ते! Anna Drishti में आपका स्वागत है।"
      - Interpret as: Text

   c. **Get customer input**:
      - Type: Lex bot
      - Bot: AnnaDrishtiFarmerBot
      - Alias: Production
      - Intent: CollectFarmerInfo
      - Session attributes:
        - phone_number: $.CustomerEndpoint.Address

   d. **Play prompt** (success):
      - Text: "धन्यवाद! हम जल्द ही आपसे संपर्क करेंगे।"

   e. **Disconnect**

3. **Save and Publish**

4. **Assign phone number to flow**:
   - Go to: Channels → Phone numbers
   - Select your claimed number
   - Contact flow: AnnaDrishtiFarmerFlow
   - Save

---

### Step 4: Enable SNS SMS (10 mins)

**Go to**: AWS Console → SNS → Text messaging (SMS)

1. **Set spending limit**: $10/month
2. **Default sender ID**: ANNADRI
3. **Default message type**: Transactional
4. **Verify**: Send test SMS to your number

---

## 🧪 Testing the IVR

### Test Call Flow

1. **Call the phone number**: +91-XXXX-XXXXXX
2. **Listen to greeting** in Hindi
3. **Provide information**:
   - Name: "Ramesh"
   - Crop: "टमाटर"
   - Quantity: "2300"
   - Plot area: "2.1"
   - Location: "Sinnar"
4. **Confirm**: "हां"
5. **Receive SMS** with workflow link
6. **Check DynamoDB** for new workflow

### Test Commands

```bash
# Check DynamoDB for IVR workflows
aws dynamodb scan \
  --table-name anna-drishti-demo-workflows \
  --filter-expression "source = :source" \
  --expression-attribute-values '{":source":{"S":"ivr"}}' \
  --region ap-south-1

# Check Lambda logs
aws logs tail /aws/lambda/anna-drishti-ivr-handler --follow --region ap-south-1

# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AnnaDrishti/IVR \
  --metric-name IVRWorkflowCreated \
  --start-time 2026-03-05T00:00:00Z \
  --end-time 2026-03-06T00:00:00Z \
  --period 3600 \
  --statistics Sum \
  --region ap-south-1
```

---

## 📊 Cost Estimate

- **Amazon Connect**: $0.018/min = ~₹1.5/min
- **Lex**: $0.00075/request = ~₹0.06/request
- **Lambda**: Free tier (1M requests/month)
- **SNS SMS**: ₹0.50/SMS (India)

**Per farmer call**: ~₹5-10 (2-3 min call + SMS)
**100 calls/day**: ~₹500-1000/day = ~₹15,000-30,000/month

---

## 📝 Implementation Checklist

- [x] IVR Handler Lambda deployed
- [x] IAM permissions configured
- [x] CloudWatch metrics enabled
- [ ] Amazon Connect instance created
- [ ] Phone number claimed
- [ ] Lex bot created and built
- [ ] Contact flow created
- [ ] Phone number assigned to flow
- [ ] SNS SMS enabled
- [ ] End-to-end test completed

---

## 🚀 Next Steps After IVR

Once IVR is working:

1. **Farmer Portfolio View** (1-2 days)
   - Multi-farmer management dashboard
   - Transaction history
   - Search functionality

2. **Payment Tracking** (1 day)
   - Payment status tracker
   - Delayed payment alerts
   - Payment metrics

3. **Satellite Integration** (2-3 days)
   - Copernicus Hub integration
   - NDVI calculation
   - Crop health visualization

4. **Unit Tests** (1-2 days)
   - Test coverage for all Lambda functions
   - CI/CD pipeline

5. **Authentication** (1-2 days)
   - AWS Cognito setup
   - Login page
   - JWT protection

---

## 📚 Reference Documentation

- **IVR Setup Guide**: `docs/IVR_SETUP_GUIDE.md`
- **Lambda Code**: `backend/lambdas/ivr_handler.py`
- **CDK Stack**: `infrastructure/lib/demo-stack.ts`
- **Phase 2 Status**: `PHASE_2_STATUS.md`

---

**Ready to set up Amazon Connect and Lex?** Follow the manual steps above!
