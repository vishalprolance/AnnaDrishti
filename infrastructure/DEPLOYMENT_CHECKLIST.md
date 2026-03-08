# Deployment Checklist

Use this checklist to ensure a successful deployment of the Collective Selling & Allocation system.

## Pre-Deployment

### AWS Account Setup
- [ ] AWS account created and active
- [ ] AWS CLI installed and configured
- [ ] AWS credentials configured (`aws configure`)
- [ ] Verify account access: `aws sts get-caller-identity`
- [ ] Sufficient permissions for CDK deployment

### Development Environment
- [ ] Node.js 18+ installed
- [ ] Python 3.11+ installed
- [ ] AWS CDK CLI installed: `npm install -g aws-cdk`
- [ ] Git repository cloned
- [ ] Dependencies installed: `npm install`

### Configuration
- [ ] Environment file created (`.env`)
- [ ] Environment variables configured
- [ ] Configuration file reviewed (`config/staging.json` or `config/production.json`)
- [ ] Alarm email configured (optional)

### Code Review
- [ ] All tests passing locally
- [ ] Code reviewed and approved
- [ ] No sensitive data in code
- [ ] Environment-specific configurations verified

## Deployment

### CDK Bootstrap (First Time Only)
- [ ] CDK bootstrapped: `npm run cdk bootstrap`
- [ ] Bootstrap stack created successfully
- [ ] S3 bucket for CDK assets created

### Build and Validate
- [ ] TypeScript compiled: `npm run build`
- [ ] No compilation errors
- [ ] CDK synth successful: `npm run cdk synth`
- [ ] Review generated CloudFormation templates

### Deploy Stacks
- [ ] Collective Stack deployed: `npm run cdk deploy AnnaDrishtiCollectiveStack`
- [ ] Deployment completed without errors
- [ ] Stack outputs captured
- [ ] Monitoring Stack deployed: `npm run cdk deploy AnnaDrishtiMonitoringStack`
- [ ] Monitoring deployment completed

### Verify Resources
- [ ] DynamoDB tables created and active
- [ ] Lambda function deployed and active
- [ ] API Gateway created with correct endpoints
- [ ] CloudWatch log groups created
- [ ] IAM roles created with correct permissions
- [ ] (Optional) RDS instance created and accessible

## Post-Deployment

### Smoke Tests
- [ ] Health endpoint responding: `curl $API_URL/health`
- [ ] Root endpoint responding: `curl $API_URL/`
- [ ] Inventory endpoint accessible
- [ ] Societies endpoint accessible
- [ ] Processing partners endpoint accessible
- [ ] All smoke tests passing: `./scripts/smoke-test.sh staging`

### Monitoring Setup
- [ ] CloudWatch dashboard accessible
- [ ] Alarms configured and active
- [ ] SNS topic created
- [ ] Email subscription confirmed (if configured)
- [ ] Test alarm notification

### Environment Variables
- [ ] Lambda environment variables exported
- [ ] Backend `.env` file created
- [ ] Environment variables verified in Lambda console

### API Testing
- [ ] Test POST /api/societies (create society)
- [ ] Test GET /api/societies (list societies)
- [ ] Test POST /api/processing-partners (create partner)
- [ ] Test GET /api/processing-partners (list partners)
- [ ] Test POST /api/inventory/contributions (add contribution)
- [ ] Test GET /api/inventory/{fpo_id}/{crop_type} (query inventory)

### Database Verification
- [ ] DynamoDB tables accessible
- [ ] Test write to inventory table
- [ ] Test read from inventory table
- [ ] (Optional) RDS accessible from Lambda
- [ ] (Optional) Database schema initialized

### Logging and Monitoring
- [ ] CloudWatch logs streaming
- [ ] Log retention configured correctly
- [ ] Metrics appearing in dashboard
- [ ] No errors in logs
- [ ] Alarms in OK state

## Documentation

### Update Documentation
- [ ] API URL documented
- [ ] Stack outputs documented
- [ ] Environment variables documented
- [ ] Deployment notes added

### Team Communication
- [ ] Deployment announcement sent
- [ ] API documentation shared
- [ ] Dashboard URL shared
- [ ] Known issues documented

## Rollback Plan

### Prepare Rollback
- [ ] Previous stack version identified
- [ ] Rollback procedure documented
- [ ] Rollback tested in staging (if applicable)

### Rollback Steps (if needed)
- [ ] Stop incoming traffic
- [ ] Rollback stack: `aws cloudformation rollback-stack --stack-name AnnaDrishtiCollectiveStack`
- [ ] Verify rollback successful
- [ ] Test previous version
- [ ] Notify team of rollback

## Production Deployment (Additional Steps)

### Pre-Production
- [ ] Staging deployment successful
- [ ] All tests passing in staging
- [ ] Performance testing completed
- [ ] Security review completed
- [ ] Backup strategy defined

### Production Configuration
- [ ] Production configuration reviewed
- [ ] RDS enabled (if required)
- [ ] Deletion protection enabled
- [ ] Point-in-time recovery enabled
- [ ] Appropriate throttling limits set

### Production Deployment
- [ ] Maintenance window scheduled
- [ ] Stakeholders notified
- [ ] Deploy to production
- [ ] Verify production deployment
- [ ] Monitor for 24 hours

### Post-Production
- [ ] Production smoke tests passed
- [ ] Performance metrics normal
- [ ] No errors in logs
- [ ] Alarms configured and tested
- [ ] Backup verified
- [ ] Disaster recovery plan documented

## Troubleshooting

### Common Issues

#### Deployment Fails
- [ ] Check AWS credentials
- [ ] Verify CDK bootstrap
- [ ] Review CloudFormation events
- [ ] Check IAM permissions

#### Lambda Errors
- [ ] Check Lambda logs
- [ ] Verify environment variables
- [ ] Test function directly
- [ ] Check IAM role permissions

#### API Gateway Issues
- [ ] Verify API deployment
- [ ] Check CORS configuration
- [ ] Test with curl/Postman
- [ ] Review API Gateway logs

#### DynamoDB Issues
- [ ] Check table status
- [ ] Verify table names
- [ ] Check IAM permissions
- [ ] Review DynamoDB metrics

## Sign-Off

### Deployment Team
- [ ] Developer: _____________________ Date: _______
- [ ] Reviewer: _____________________ Date: _______
- [ ] DevOps: _______________________ Date: _______

### Approval
- [ ] Technical Lead: ________________ Date: _______
- [ ] Product Owner: ________________ Date: _______

## Notes

Add any deployment-specific notes, issues encountered, or lessons learned:

```
[Add notes here]
```

## Next Steps

After successful deployment:
1. Monitor system for 24-48 hours
2. Gather performance metrics
3. Collect user feedback
4. Plan next iteration
5. Update documentation based on learnings
