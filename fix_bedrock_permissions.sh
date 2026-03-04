#!/bin/bash

echo "🔧 Fixing Bedrock Permissions"
echo "================================"
echo ""

# Get current IAM user
echo "📋 Getting your IAM username..."
USERNAME=$(aws sts get-caller-identity --query 'Arn' --output text | cut -d'/' -f2)

if [ -z "$USERNAME" ]; then
    echo "❌ Could not determine IAM username"
    echo "   Are you using an IAM role instead of a user?"
    echo ""
    echo "💡 Solution: Add these permissions to your IAM role/user via AWS Console:"
    echo "   1. Go to: https://console.aws.amazon.com/iam"
    echo "   2. Find your user/role"
    echo "   3. Add policy: AWSMarketplaceFullAccess"
    exit 1
fi

echo "✅ Found username: $USERNAME"
echo ""

# Attach marketplace policy
echo "🔐 Attaching AWS Marketplace permissions..."
aws iam attach-user-policy \
    --user-name "$USERNAME" \
    --policy-arn arn:aws:iam::aws:policy/AWSMarketplaceFullAccess 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Permissions attached successfully!"
    echo ""
    echo "⏳ Waiting 30 seconds for permissions to propagate..."
    sleep 30
    echo ""
    echo "🧪 Testing Bedrock access..."
    python3 check_bedrock.py
else
    echo ""
    echo "❌ Could not attach policy automatically"
    echo ""
    echo "💡 Manual steps:"
    echo "   1. Go to: https://console.aws.amazon.com/iam/home#/users/$USERNAME"
    echo "   2. Click 'Permissions' tab"
    echo "   3. Click 'Add permissions' → 'Attach policies directly'"
    echo "   4. Search for 'AWSMarketplaceFullAccess'"
    echo "   5. Check the box and click 'Add permissions'"
    echo ""
    echo "   Then run: python3 check_bedrock.py"
fi
