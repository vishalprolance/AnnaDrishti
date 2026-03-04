import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import { Construct } from 'constructs';

export interface DashboardStackProps extends cdk.StackProps {
  apiUrl: string;
  wsUrl: string;
}

export class DashboardStack extends cdk.Stack {
  public readonly dashboardUrl: string;

  constructor(scope: Construct, id: string, props: DashboardStackProps) {
    super(scope, id, props);

    // S3 Bucket for dashboard hosting
    const dashboardBucket = new s3.Bucket(this, 'DashboardBucket', {
      bucketName: `anna-drishti-dashboard-${this.account}`,
      websiteIndexDocument: 'index.html',
      websiteErrorDocument: 'index.html', // SPA routing
      publicReadAccess: false,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For demo only
      autoDeleteObjects: true, // For demo only
    });

    // CloudFront Origin Access Identity
    const originAccessIdentity = new cloudfront.OriginAccessIdentity(this, 'OAI', {
      comment: 'OAI for Anna Drishti Dashboard',
    });

    dashboardBucket.grantRead(originAccessIdentity);

    // CloudFront Distribution
    const distribution = new cloudfront.Distribution(this, 'DashboardDistribution', {
      defaultBehavior: {
        origin: origins.S3BucketOrigin.withOriginAccessIdentity(dashboardBucket, {
          originAccessIdentity,
        }),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
        cachedMethods: cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
        compress: true,
      },
      defaultRootObject: 'index.html',
      errorResponses: [
        {
          httpStatus: 404,
          responseHttpStatus: 200,
          responsePagePath: '/index.html',
          ttl: cdk.Duration.minutes(5),
        },
        {
          httpStatus: 403,
          responseHttpStatus: 200,
          responsePagePath: '/index.html',
          ttl: cdk.Duration.minutes(5),
        },
      ],
      priceClass: cloudfront.PriceClass.PRICE_CLASS_100, // Use only North America and Europe
      comment: 'Anna Drishti Dashboard CDN',
    });

    this.dashboardUrl = `https://${distribution.distributionDomainName}`;

    // CloudFormation Outputs
    new cdk.CfnOutput(this, 'DashboardUrl', {
      value: this.dashboardUrl,
      description: 'Dashboard URL',
      exportName: 'AnnaDrishtiDashboardUrl',
    });

    new cdk.CfnOutput(this, 'DashboardBucketName', {
      value: dashboardBucket.bucketName,
      description: 'S3 bucket for dashboard',
      exportName: 'AnnaDrishtiDashboardBucket',
    });

    new cdk.CfnOutput(this, 'DistributionId', {
      value: distribution.distributionId,
      description: 'CloudFront distribution ID',
      exportName: 'AnnaDrishtiDistributionId',
    });

    // Note: Dashboard deployment will be done manually after build
    // Command: aws s3 sync dashboard/dist s3://bucket-name
    // Then: aws cloudfront create-invalidation --distribution-id ID --paths "/*"
  }
}
