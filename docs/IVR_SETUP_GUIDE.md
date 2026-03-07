# IVR Implementation Guide - Amazon Connect + Lex

## Overview

Build a phone-based IVR system where farmers can call and provide their information in Hindi/Marathi. The system will:
1. Answer the call
2. Collect farmer information (name, crop, quantity, plot area, location)
3. Create a workflow in DynamoDB
4. Send SMS with workflow link

---

## Architecture

```
Farmer Call → Amazon Connect → Lex Bot (Hindi) → Lambda (IVR Handler) → DynamoDB
                                                      ↓
                                                   SNS (SMS)
```

---

## Step 1: Set Up Amazon Connect Instance (15 mins)

### 1.1 Create Connect Instance

```bash
# Go to AWS Console → Amazon Connect
# Click "Create instance"
```

**Configuration**:
- Instance alias: `anna-drishti-ivr`
- Identity management: Store users in Amazon Connect
- Administrator: Create new admin user
- Telephony: Enable incoming calls
- Data storage: Use default S3 bucket
- Data streaming: Skip for now
- Tags: `Project=AnnaDrishti, Environment=Production`

### 1.2 Claim Phone Number

```bash
# In Connect instance → Channels → Phone numbers
# Click "Claim a number"
```

**Configuration**:
- Country: India (+91)
- Type: DID (Direct Inward Dialing)
- Number type: Toll-free (if available) or Local
- Description: "Anna Drishti Farmer Hotline"

**Save this number** - farmers will call this!

---

## Step 2: Create Lex Bot for Hindi (30 mins)

### 2.1 Create Bot

```bash
# Go to AWS Console → Amazon Lex V2
# Click "Create bot"
```

**Configuration**:
- Bot name: `AnnaDrishtiFarmerBot`
- Description: "Collects farmer information in Hindi"
- IAM role: Create new role
- COPPA: No
- Idle session timeout: 5 minutes
- Language: Hindi (hi_IN)

### 2.2 Create Intent: CollectFarmerInfo

**Intent name**: `CollectFarmerInfo`

**Sample utterances** (Hindi):
```
मैं अपनी फसल बेचना चाहता हूं
मुझे बाजार की कीमत चाहिए
मेरे पास टमाटर है
मैं किसान हूं
```

**Slots**:

1. **farmer_name**
   - Slot type: AMAZON.FirstName
   - Prompt: "आपका नाम क्या है?" (What is your name?)
   - Required: Yes

2. **crop_type**
   - Slot type: Custom (create new)
   - Values: टमाटर (tomato), प्याज (onion), मिर्च (chili)
   - Prompt: "आप कौन सी फसल बेचना चाहते हैं?" (Which crop do you want to sell?)
   - Required: Yes

3. **quantity**
   - Slot type: AMAZON.Number
   - Prompt: "कितने किलो है?" (How many kilograms?)
   - Required: Yes

4. **plot_area**
   - Slot type: AMAZON.Number
   - Prompt: "आपके खेत का क्षेत्रफल कितना है? एकड़ में बताएं।" (What is your plot area in acres?)
   - Required: Yes

5. **location**
   - Slot type: AMAZON.City
   - Prompt: "आप कहां से हैं?" (Where are you from?)
   - Required: Yes

**Confirmation prompt**:
```
तो {farmer_name}, आपके पास {quantity} किलो {crop_type} है, {plot_area} एकड़ में, {location} से। क्या यह सही है?
```

**Fulfillment**: AWS Lambda function (we'll create this next)

### 2.3 Build and Test Bot

```bash
# Click "Build" button
# Wait for build to complete (2-3 minutes)
# Test in the console with: "मैं अपनी फसल बेचना चाहता हूं"
```

---

## Step 3: Create Lambda Function for IVR (20 mins)

We'll create `backend/lambdas/ivr_handler.py` - this processes Lex bot input.

---

## Step 4: Connect Everything (20 mins)

### 4.1 Add Lambda to Lex Bot

```bash
# In Lex Bot → Aliases → Create alias
# Alias name: "Production"
# Associate with Lambda: Select ivr_handler function
```

### 4.2 Create Contact Flow in Amazon Connect

```bash
# In Connect instance → Routing → Contact flows
# Click "Create contact flow"
```

**Flow name**: `AnnaDrishtiFarmerFlow`

**Flow steps**:
1. **Set voice**: Hindi (hi-IN) - Aditi voice
2. **Play prompt**: "नमस्ते! Anna Drishti में आपका स्वागत है।" (Welcome to Anna Drishti)
3. **Get customer input** → Lex bot
   - Bot: AnnaDrishtiFarmerBot
   - Alias: Production
   - Intent: CollectFarmerInfo
4. **Play prompt**: "धन्यवाद! हम जल्द ही आपसे संपर्क करेंगे।" (Thank you! We'll contact you soon)
5. **Disconnect**

**Save and Publish**

### 4.3 Assign Phone Number to Flow

```bash
# In Connect → Channels → Phone numbers
# Select your claimed number
# Contact flow: AnnaDrishtiFarmerFlow
# Save
```

---

## Step 5: Set Up SNS for SMS (10 mins)

### 5.1 Create SNS Topic

```bash
aws sns create-topic --name anna-drishti-farmer-sms --region ap-south-1
```

### 5.2 Enable SMS in SNS

```bash
# Go to AWS Console → SNS → Text messaging (SMS)
# Set spending limit: $10/month
# Default sender ID: ANNADRI
# Default message type: Transactional
```

---

## Testing the IVR

### Test Call Flow

1. **Call the phone number** from your mobile
2. **Listen to greeting** in Hindi
3. **Provide information**:
   - Name: "Ramesh"
   - Crop: "टमाटर" (tomato)
   - Quantity: "2300"
   - Plot area: "2.1"
   - Location: "Sinnar"
4. **Confirm**: "हां" (yes)
5. **Receive SMS** with workflow link
6. **Check DynamoDB** for new workflow entry

### Test Commands

```bash
# Check DynamoDB for IVR workflows
aws dynamodb scan \
  --table-name anna-drishti-demo-workflows \
  --filter-expression "source = :source" \
  --expression-attribute-values '{":source":{"S":"ivr"}}' \
  --region ap-south-1

# Check CloudWatch logs for Lambda
aws logs tail /aws/lambda/ivr_handler --follow --region ap-south-1
```

---

## Cost Estimate

- **Amazon Connect**: $0.018/min = ~₹1.5/min
- **Lex**: $0.00075/request = ~₹0.06/request
- **Lambda**: Free tier (1M requests/month)
- **SNS SMS**: ₹0.50/SMS (India)

**Per farmer call**: ~₹5-10 (2-3 min call + SMS)

---

## Next Steps

1. Create Lambda function (`ivr_handler.py`)
2. Deploy Lambda with CDK
3. Set up Connect instance
4. Create Lex bot
5. Test end-to-end flow
6. Add error handling and monitoring

Ready to create the Lambda function?
