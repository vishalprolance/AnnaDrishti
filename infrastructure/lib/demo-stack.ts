import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';

export class DemoStack extends cdk.Stack {
  public readonly apiUrl: string;
  public readonly wsUrl: string;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // DynamoDB Table for workflow state
    const workflowTable = new dynamodb.Table(this, 'WorkflowTable', {
      tableName: 'anna-drishti-demo-workflows',
      partitionKey: {
        name: 'workflow_id',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For demo only
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: false, // Not needed for demo
      },
    });

    // GSI for querying by status
    workflowTable.addGlobalSecondaryIndex({
      indexName: 'status-index',
      partitionKey: {
        name: 'status',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'created_at',
        type: dynamodb.AttributeType.STRING,
      },
    });

    // Lambda Layer for shared code
    const sharedLayer = new lambda.LayerVersion(this, 'SharedLayer', {
      code: lambda.Code.fromAsset('../backend', {
        bundling: {
          image: lambda.Runtime.PYTHON_3_11.bundlingImage,
          command: [
            'bash', '-c',
            'pip install -r requirements.txt -t /asset-output/python && ' +
            'cp -r models /asset-output/python/'
          ],
        },
      }),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_11],
      description: 'Shared dependencies and models for Anna Drishti',
    });

    // IAM Role for Lambda functions
    const lambdaRole = new iam.Role(this, 'LambdaExecutionRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    // Grant DynamoDB permissions
    workflowTable.grantReadWriteData(lambdaRole);

    // Grant Bedrock permissions
    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock:InvokeModel',
        'bedrock:InvokeModelWithResponseStream',
      ],
      resources: ['*'], // Bedrock models don't have specific ARNs
    }));

    // Lambda Functions
    
    // Start Workflow Lambda
    const startWorkflowFn = new lambda.Function(this, 'StartWorkflowFunction', {
      functionName: 'anna-drishti-start-workflow',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'start_workflow.lambda_handler',
      code: lambda.Code.fromAsset('../backend/lambdas'),
      layers: [sharedLayer],
      role: lambdaRole,
      timeout: cdk.Duration.seconds(30),
      environment: {
        WORKFLOW_TABLE_NAME: workflowTable.tableName,
        DASHBOARD_URL: 'https://d2ll18l06rc220.cloudfront.net',
      },
      logGroup: new logs.LogGroup(this, 'StartWorkflowLogGroup', {
        logGroupName: '/aws/lambda/anna-drishti-start-workflow',
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
    });

    // Scan Market Lambda
    const scanMarketFn = new lambda.Function(this, 'ScanMarketFunction', {
      functionName: 'anna-drishti-scan-market',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'scan_market.lambda_handler',
      code: lambda.Code.fromAsset('../backend/lambdas'),
      layers: [sharedLayer],
      role: lambdaRole,
      timeout: cdk.Duration.seconds(30),
      environment: {
        WORKFLOW_TABLE_NAME: workflowTable.tableName,
      },
      logGroup: new logs.LogGroup(this, 'ScanMarketLogGroup', {
        logGroupName: '/aws/lambda/anna-drishti-scan-market',
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
    });

    // Detect Surplus Lambda
    const detectSurplusFn = new lambda.Function(this, 'DetectSurplusFunction', {
      functionName: 'anna-drishti-detect-surplus',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'detect_surplus.lambda_handler',
      code: lambda.Code.fromAsset('../backend/lambdas'),
      layers: [sharedLayer],
      role: lambdaRole,
      timeout: cdk.Duration.seconds(30),
      environment: {
        WORKFLOW_TABLE_NAME: workflowTable.tableName,
      },
      logGroup: new logs.LogGroup(this, 'DetectSurplusLogGroup', {
        logGroupName: '/aws/lambda/anna-drishti-detect-surplus',
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
    });

    // Negotiate Lambda (Bedrock)
    const negotiateFn = new lambda.Function(this, 'NegotiateFunction', {
      functionName: 'anna-drishti-negotiate',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'negotiate.lambda_handler',
      code: lambda.Code.fromAsset('../backend/lambdas'),
      layers: [sharedLayer],
      role: lambdaRole,
      timeout: cdk.Duration.seconds(60), // Longer timeout for Bedrock
      environment: {
        WORKFLOW_TABLE_NAME: workflowTable.tableName,
        BEDROCK_MODEL_ID: 'anthropic.claude-3-haiku-20240307-v1:0',
      },
      logGroup: new logs.LogGroup(this, 'NegotiateLogGroup', {
        logGroupName: '/aws/lambda/anna-drishti-negotiate',
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
    });

    // REST API Gateway
    const api = new apigateway.RestApi(this, 'DemoApi', {
      restApiName: 'Anna Drishti Demo API',
      description: 'API for Anna Drishti hackathon demo',
      deployOptions: {
        stageName: 'demo',
        // Logging disabled - requires CloudWatch Logs role ARN in account settings
        // loggingLevel: apigateway.MethodLoggingLevel.INFO,
        // dataTraceEnabled: true,
      },
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type', 'Authorization'],
      },
    });

    // API Resources
    const workflowResource = api.root.addResource('workflow');
    const startResource = workflowResource.addResource('start');
    const scanResource = workflowResource.addResource('scan');
    const surplusResource = workflowResource.addResource('surplus');
    const negotiateResource = workflowResource.addResource('negotiate');
    
    // POST /workflow/start
    startResource.addMethod('POST', new apigateway.LambdaIntegration(startWorkflowFn));
    
    // POST /workflow/scan
    scanResource.addMethod('POST', new apigateway.LambdaIntegration(scanMarketFn));
    
    // POST /workflow/surplus
    surplusResource.addMethod('POST', new apigateway.LambdaIntegration(detectSurplusFn));
    
    // POST /workflow/negotiate
    negotiateResource.addMethod('POST', new apigateway.LambdaIntegration(negotiateFn));

    // WebSocket API (placeholder for Phase 1)
    // Will be implemented in Hour 33-40
    this.wsUrl = 'wss://placeholder-websocket-url';

    // Export API URL
    this.apiUrl = api.url;

    // CloudFormation Outputs
    new cdk.CfnOutput(this, 'ApiUrl', {
      value: this.apiUrl,
      description: 'REST API URL',
      exportName: 'AnnaDrishtiApiUrl',
    });

    new cdk.CfnOutput(this, 'WorkflowTableName', {
      value: workflowTable.tableName,
      description: 'DynamoDB table for workflows',
      exportName: 'AnnaDrishtiWorkflowTable',
    });

    new cdk.CfnOutput(this, 'LambdaRoleArn', {
      value: lambdaRole.roleArn,
      description: 'IAM role for Lambda functions',
      exportName: 'AnnaDrishtiLambdaRole',
    });

    new cdk.CfnOutput(this, 'SharedLayerArn', {
      value: sharedLayer.layerVersionArn,
      description: 'Lambda layer with shared code',
      exportName: 'AnnaDrishtiSharedLayer',
    });
  }
}
