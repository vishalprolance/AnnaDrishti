# AWS Setup Guide for Anna Drishti Hackathon MVP

## Prerequisites

- AWS Account (create at https://aws.amazon.com if you don't have one)
- Credit card for AWS account verification
- Terminal/Command Prompt access

## Step 1: Create AWS Account (if needed)

1. Go to https://aws.amazon.com
2. Click "Create an AWS Account"
3. Follow the signup process
4. Verify your email and phone number
5. Add payment method (free tier available)

## Step 2: Create IAM User

**Why:** Don't use root account for development

1. Log into AWS Console: https://console.aws.amazon.com
2. Search for "IAM" in the top search bar
3. Click "Users" in left sidebar
4. Click "Create user"
5. User name: `anna-drishti-dev`
6. Click "Next"
7. Select "Attach policies directly"
8. Search and select: `AdministratorAccess` (for hackathon speed)
9. Click "Next" → "Create user"

## Step 3: Create Access Keys

1. Click on the user you just created (`anna-drishti-dev`)
2. Go to "Security credentials" tab
3. Scroll to "Access keys" section
4. Click "Create access key"
5. Select "Command Line Interface (CLI)"
6. Check "I understand..." checkbox
7. Click "Next" → "Create access key"
8. **IMPORTANT:** Copy both:
   - Access key ID (starts with `AKIA...`)
   - Secret access key (long random string)
9. Click "Download .csv file" as backup
10. Click "Done"

## Step 4: Install AWS CLI

### macOS
```bash
# Using Homebrew
brew install awscli

# Or download installer
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
```

### Linux
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### Windows
Download and run: https://awscli.amazonaws.com/AWSCLIV2.msi

### Verify Installation
```bash
aws --version
# Should show: aws-cli/2.x.x ...
```

## Step 5: Configure AWS CLI

```bash
aws configure
```

Enter the following when prompted:
```
AWS Access Key ID: [paste your access key ID]
AWS Secret Access Key: [paste your secret access key]
Default region name: ap-south-1
Default output format: json
```

**Region Choice:**
- `ap-south-1` (Mumbai) - Recommended for India
- `us-east-1` (N. Virginia) - Alternative if Mumbai has issues

### Verify Configuration
```bash
aws sts get-caller-identity
```

Should return:
```json
{
    "UserId": "AIDAXXXXXXXXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/anna-drishti-dev"
}
```

## Step 6: Enable Required AWS Services

### Enable Bedrock (for AI negotiation)

1. Go to AWS Console → Search "Bedrock"
2. Click "Get started"
3. In left sidebar, click "Model access"
4. Click "Manage model access"
5. Find "Claude" section
6. Check "Claude 3 Haiku"
7. Click "Request model access"
8. Wait 2-5 minutes for approval (usually instant)

### Verify Bedrock Access
```bash
aws bedrock list-foundation-models --region ap-south-1
```

Should show Claude models in the list.

## Step 7: Install AWS CDK

```bash
# Install CDK globally
npm install -g aws-cdk

# Verify installation
cdk --version
# Should show: 2.x.x
```

## Step 8: Bootstrap CDK

**What this does:** Sets up S3 bucket and IAM roles for CDK deployments

```bash
cd infrastructure
cdk bootstrap aws://AKIAYKYVENNAJEUEFRNZ/ap-south-1
```

Replace `ACCOUNT-ID` with your AWS account ID (from step 5 verification).

Or let CDK detect it automatically:
```bash
cdk bootstrap
```

Should see:
```
✅  Environment aws://123456789012/ap-south-1 bootstrapped.
```

## Step 9: Set Up Environment Variables

Create `backend/.env`:
```bash
cd backend
cat > .env << 'EOF'
AWS_REGION=ap-south-1
DYNAMODB_TABLE=anna-drishti-demo
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
AGMARKNET_BASE_URL=https://agmarknet.gov.in
DEMO_OFFLINE_MODE=false
EOF
```

Create `dashboard/.env`:
```bash
cd ../dashboard
cat > .env << 'EOF'
VITE_API_URL=https://placeholder-will-update-after-deploy
VITE_WS_URL=wss://placeholder-will-update-after-deploy
VITE_MAPBOX_TOKEN=pk.placeholder
EOF
```

## Step 10: Verify Everything Works

```bash
# Test AWS access
aws s3 ls

# Test CDK
cd infrastructure
cdk ls

# Should show: DemoStack, DashboardStack
```

## Troubleshooting

### "Unable to locate credentials"
```bash
# Check if credentials are configured
cat ~/.aws/credentials

# Should show:
# [default]
# aws_access_key_id = AKIA...
# aws_secret_access_key = ...
```

### "Access Denied" errors
- Verify IAM user has AdministratorAccess policy
- Check you're using the correct AWS account

### Bedrock "Model not found"
- Ensure you requested access to Claude 3 Haiku
- Wait 5-10 minutes after requesting access
- Try different region: `us-east-1` has faster approval

### CDK Bootstrap fails
```bash
# Try with explicit account and region
cdk bootstrap aws://$(aws sts get-caller-identity --query Account --output text)/ap-south-1
```

## Cost Estimates (Hackathon)

**Free Tier Eligible:**
- Lambda: 1M requests/month free
- DynamoDB: 25GB storage free
- API Gateway: 1M requests/month free
- S3: 5GB storage free

**Paid Services:**
- Bedrock Claude 3 Haiku: ~₹0.0003/1K tokens (~₹50 for hackathon)
- Step Functions: ₹0.025/1K state transitions (~₹10 for hackathon)

**Total Estimated Cost: ₹100-200 for 48-hour hackathon**

## Security Best Practices

**For Hackathon (Speed):**
- ✅ Use IAM user (not root)
- ✅ Store credentials in `~/.aws/credentials`
- ✅ Add `.env` to `.gitignore`

**For Production (Phase 3):**
- Use IAM roles instead of access keys
- Enable MFA on IAM users
- Use AWS Secrets Manager for sensitive data
- Implement least-privilege IAM policies

## Next Steps

Once AWS is configured:
1. ✅ Mark task 1.1 as complete
2. → Move to task 1.2: Initialize project structure
3. → Continue with Hour 1-4 tasks

## Quick Reference

```bash
# Check AWS identity
aws sts get-caller-identity

# List S3 buckets
aws s3 ls

# Check Bedrock models
aws bedrock list-foundation-models --region ap-south-1

# CDK commands
cdk ls                    # List stacks
cdk diff                  # Show changes
cdk deploy               # Deploy stack
cdk destroy              # Delete stack

# View CloudWatch logs
aws logs tail /aws/lambda/function-name --follow
```

## Support

If you encounter issues:
1. Check AWS Service Health Dashboard: https://status.aws.amazon.com
2. Review CloudWatch logs in AWS Console
3. Check IAM permissions
4. Try different AWS region

---

**Ready to build!** Proceed to task 1.2 in the implementation plan.
