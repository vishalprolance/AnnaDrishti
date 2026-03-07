# AWS Account Setup for Teammate

## Overview

This guide helps your teammate connect to the **same AWS account** where Anna Drishti is already deployed.

**AWS Account ID**: `572885592896`  
**Region**: `ap-south-1` (Mumbai)  
**Stack Name**: `AnnaDrishtiDemoStack`

---

## Option 1: IAM User Credentials (Recommended)

### Step 1: Create IAM User (You do this)

1. Go to AWS Console → IAM → Users
2. Click "Create user"
3. Username: `anna-drishti-developer` (or your teammate's name)
4. Click "Next"

### Step 2: Set Permissions

**Option A: Administrator Access (Full Access)**
- Attach policy: `AdministratorAccess`
- Use this if your teammate needs full control

**Option B: Limited Access (Recommended)**
- Create custom policy with these permissions:
  - Lambda: Full access
  - DynamoDB: Full access
  - API Gateway: Full access
  - CloudFormation: Full access
  - S3: Full access
  - CloudFront: Full access
  - CloudWatch: Full access
  - IAM: Read access (for viewing roles)

**Custom Policy JSON**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:*",
        "dynamodb:*",
        "apigateway:*",
        "cloudformation:*",
        "s3:*",
        "cloudfront:*",
        "logs:*",
        "cloudwatch:*",
        "iam:GetRole",
        "iam:GetRolePolicy",
        "iam:ListRoles",
        "iam:PassRole"
      ],
      "Resource": "*"
    }
  ]
}
```

### Step 3: Create Access Keys

1. Click on the user you just created
2. Go to "Security credentials" tab
3. Click "Create access key"
4. Choose "Command Line Interface (CLI)"
5. Click "Next" → "Create access key"
6. **IMPORTANT**: Download the CSV file or copy the credentials
   - Access Key ID: `AKIA...`
   - Secret Access Key: `wJalrXUtn...`
7. **Send these credentials securely** to your teammate (use encrypted channel)

---

## Option 2: AWS SSO (Single Sign-On)

If your organization uses AWS SSO:

1. Go to AWS SSO console
2. Add your teammate's email
3. Assign permission set (e.g., PowerUserAccess)
4. Your teammate will receive an email invitation
5. They follow the link to set up their account

---

## Teammate Setup Instructions

### Step 1: Install AWS CLI

**macOS**:
```bash
brew install awscli
```

**Linux**:
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**Windows**:
Download from: https://aws.amazon.com/cli/

### Step 2: Configure AWS CLI

```bash
aws configure
```

**Enter the following**:
```
AWS Access Key ID: AKIA... (from Step 3 above)
AWS Secret Access Key: wJalrXUtn... (from Step 3 above)
Default region name: ap-south-1
Default output format: json
```

### Step 3: Verify Access

```bash
# Check AWS account
aws sts get-caller-identity
```

**Expected Output**:
```json
{
    "UserId": "AIDA...",
    "Account": "572885592896",
    "Arn": "arn:aws:iam::572885592896:user/anna-drishti-developer"
}
```

**Verify you see Account ID: 572885592896** ✅

### Step 4: Test Access to Resources

```bash
# List Lambda functions
aws lambda list-functions --region ap-south-1

# Check DynamoDB table
aws dynamodb describe-table --table-name anna-drishti-demo-workflows --region ap-south-1

# List S3 buckets
aws s3 ls

# Check CloudFormation stack
aws cloudformation describe-stacks --stack-name AnnaDrishtiDemoStack --region ap-south-1
```

**If all commands work, you're connected!** ✅

---

## Option 3: AWS CLI Profiles (Multiple Accounts)

If your teammate already has AWS credentials for another account, use profiles:

### Step 1: Configure Named Profile

```bash
aws configure --profile anna-drishti
```

**Enter**:
```
AWS Access Key ID: AKIA...
AWS Secret Access Key: wJalrXUtn...
Default region name: ap-south-1
Default output format: json
```

### Step 2: Use Profile in Commands

```bash
# Use profile in commands
aws lambda list-functions --profile anna-drishti --region ap-south-1

# Or set as default for session
export AWS_PROFILE=anna-drishti

# Now all commands use this profile
aws lambda list-functions --region ap-south-1
```

### Step 3: Configure CDK to Use Profile

**Option A: Environment Variable**
```bash
export AWS_PROFILE=anna-drishti
cd infrastructure
npx cdk deploy AnnaDrishtiDemoStack
```

**Option B: CDK Context**
```bash
cd infrastructure
npx cdk deploy AnnaDrishtiDemoStack --profile anna-drishti
```

---

## Credentials File Location

AWS credentials are stored in:

**macOS/Linux**: `~/.aws/credentials`
**Windows**: `C:\Users\USERNAME\.aws\credentials`

**Example `~/.aws/credentials`**:
```ini
[default]
aws_access_key_id = AKIA...
aws_secret_access_key = wJalrXUtn...

[anna-drishti]
aws_access_key_id = AKIA...
aws_secret_access_key = wJalrXUtn...
```

**Example `~/.aws/config`**:
```ini
[default]
region = ap-south-1
output = json

[profile anna-drishti]
region = ap-south-1
output = json
```

---

## Security Best Practices

### DO ✅
- Use IAM users with limited permissions (not root account)
- Enable MFA (Multi-Factor Authentication) for IAM users
- Rotate access keys every 90 days
- Use AWS SSO if available
- Store credentials securely (use password manager)
- Use named profiles for multiple accounts

### DON'T ❌
- Share root account credentials
- Commit credentials to Git
- Use access keys with AdministratorAccess unless necessary
- Share credentials over unencrypted channels (email, Slack)
- Leave unused access keys active

---

## Troubleshooting

### Issue: "Unable to locate credentials"
**Solution**: Run `aws configure` and enter credentials

### Issue: "Access Denied" errors
**Solution**: Check IAM permissions. User needs permissions for Lambda, DynamoDB, etc.

### Issue: "Region not found"
**Solution**: Make sure region is set to `ap-south-1`:
```bash
aws configure set region ap-south-1
```

### Issue: "Stack not found"
**Solution**: Verify you're in the correct region:
```bash
aws cloudformation describe-stacks --stack-name AnnaDrishtiDemoStack --region ap-south-1
```

### Issue: Wrong AWS account
**Solution**: Check which account you're using:
```bash
aws sts get-caller-identity
```
Should show Account: `572885592896`

---

## Quick Setup Script

Create a file `setup_aws.sh`:

```bash
#!/bin/bash

echo "=========================================="
echo "Anna Drishti - AWS Account Setup"
echo "=========================================="
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not installed"
    echo "Install from: https://aws.amazon.com/cli/"
    exit 1
fi

echo "✅ AWS CLI installed"
echo ""

# Configure AWS
echo "Configuring AWS credentials..."
echo "Enter your AWS Access Key ID:"
read -r access_key
echo "Enter your AWS Secret Access Key:"
read -rs secret_key
echo ""

# Set credentials
aws configure set aws_access_key_id "$access_key"
aws configure set aws_secret_access_key "$secret_key"
aws configure set region ap-south-1
aws configure set output json

echo "✅ AWS credentials configured"
echo ""

# Verify
echo "Verifying AWS account..."
account_id=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)

if [ "$account_id" = "572885592896" ]; then
    echo "✅ Connected to correct AWS account: $account_id"
    echo ""
    echo "Testing access to resources..."
    
    # Test Lambda
    if aws lambda list-functions --region ap-south-1 --max-items 1 &> /dev/null; then
        echo "✅ Lambda access: OK"
    else
        echo "❌ Lambda access: DENIED"
    fi
    
    # Test DynamoDB
    if aws dynamodb describe-table --table-name anna-drishti-demo-workflows --region ap-south-1 &> /dev/null; then
        echo "✅ DynamoDB access: OK"
    else
        echo "❌ DynamoDB access: DENIED"
    fi
    
    # Test S3
    if aws s3 ls &> /dev/null; then
        echo "✅ S3 access: OK"
    else
        echo "❌ S3 access: DENIED"
    fi
    
    echo ""
    echo "=========================================="
    echo "✅ Setup complete!"
    echo "=========================================="
    echo ""
    echo "You can now deploy with:"
    echo "  cd infrastructure"
    echo "  npx cdk deploy AnnaDrishtiDemoStack"
    
else
    echo "❌ Wrong AWS account: $account_id"
    echo "Expected: 572885592896"
    echo ""
    echo "Please check your credentials and try again."
    exit 1
fi
```

Make it executable:
```bash
chmod +x setup_aws.sh
```

Run it:
```bash
./setup_aws.sh
```

---

## Environment Variables Method (Alternative)

Instead of `aws configure`, you can use environment variables:

```bash
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="wJalrXUtn..."
export AWS_DEFAULT_REGION="ap-south-1"
```

**To make permanent**, add to `~/.zshrc` or `~/.bashrc`:
```bash
echo 'export AWS_ACCESS_KEY_ID="AKIA..."' >> ~/.zshrc
echo 'export AWS_SECRET_ACCESS_KEY="wJalrXUtn..."' >> ~/.zshrc
echo 'export AWS_DEFAULT_REGION="ap-south-1"' >> ~/.zshrc
source ~/.zshrc
```

---

## Summary

**For your teammate to use the same AWS account**:

1. **You create IAM user** with appropriate permissions
2. **You generate access keys** for the user
3. **You send credentials securely** to your teammate
4. **Teammate runs** `aws configure` with the credentials
5. **Teammate verifies** with `aws sts get-caller-identity`
6. **Teammate can now deploy** with `npx cdk deploy`

**Account ID to verify**: `572885592896`  
**Region**: `ap-south-1`  
**Stack**: `AnnaDrishtiDemoStack`

---

## Next Steps After Setup

Once AWS is configured:

1. Clone repository: `git clone <repo-url>`
2. Install dependencies: `npm install` (in infrastructure folder)
3. Set OpenAI API key: `export OPENAI_API_KEY="sk-..."`
4. Deploy: `npx cdk deploy AnnaDrishtiDemoStack`
5. Test: `python3 test_full_workflow.py`

---

**Last Updated**: March 7, 2026  
**AWS Account**: 572885592896  
**Region**: ap-south-1 (Mumbai)
