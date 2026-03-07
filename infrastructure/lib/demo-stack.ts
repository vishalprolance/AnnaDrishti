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

    // Grant SNS permissions for SMS
    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'sns:Publish',
      ],
      resources: ['*'], // SNS SMS doesn't require specific topic ARN
    }));

    // Grant CloudWatch metrics permissions
    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'cloudwatch:PutMetricData',
      ],
      resources: ['*'],
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

    // Negotiate Lambda (OpenAI)
    const negotiateFn = new lambda.Function(this, 'NegotiateFunction', {
      functionName: 'anna-drishti-negotiate',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'negotiate.lambda_handler',
      code: lambda.Code.fromAsset('../backend/lambdas'),
      layers: [sharedLayer],
      role: lambdaRole,
      timeout: cdk.Duration.seconds(60), // Longer timeout for AI API
      environment: {
        WORKFLOW_TABLE_NAME: workflowTable.tableName,
        OPENAI_API_KEY: process.env.OPENAI_API_KEY || '',
        OPENAI_MODEL: 'gpt-4o-mini',
      },
      logGroup: new logs.LogGroup(this, 'NegotiateLogGroup', {
        logGroupName: '/aws/lambda/anna-drishti-negotiate',
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
    });

    // IVR Handler Lambda (for Lex bot)
    const ivrHandlerFn = new lambda.Function(this, 'IVRHandlerFunction', {
      functionName: 'anna-drishti-ivr-handler',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'ivr_handler.lambda_handler',
      code: lambda.Code.fromAsset('../backend/lambdas'),
      layers: [sharedLayer],
      role: lambdaRole,
      timeout: cdk.Duration.seconds(30),
      environment: {
        WORKFLOW_TABLE_NAME: workflowTable.tableName,
        DASHBOARD_URL: 'https://d2ll18l06rc220.cloudfront.net',
      },
      logGroup: new logs.LogGroup(this, 'IVRHandlerLogGroup', {
        logGroupName: '/aws/lambda/anna-drishti-ivr-handler',
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
    });

    // Grant Lex permissions to invoke IVR handler
    ivrHandlerFn.addPermission('LexInvokePermission', {
      principal: new iam.ServicePrincipal('lexv2.amazonaws.com'),
      action: 'lambda:InvokeFunction',
    });

    // List Farmers Lambda (for farmer portfolio)
    const listFarmersFn = new lambda.Function(this, 'ListFarmersFunction', {
      functionName: 'anna-drishti-list-farmers',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'list_farmers.lambda_handler',
      code: lambda.Code.fromAsset('../backend/lambdas'),
      layers: [sharedLayer],
      role: lambdaRole,
      timeout: cdk.Duration.seconds(30),
      environment: {
        WORKFLOW_TABLE_NAME: workflowTable.tableName,
      },
      logGroup: new logs.LogGroup(this, 'ListFarmersLogGroup', {
        logGroupName: '/aws/lambda/anna-drishti-list-farmers',
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
    });

    // Get Farmer Lambda (for farmer detail page)
    const getFarmerFn = new lambda.Function(this, 'GetFarmerFunction', {
      functionName: 'anna-drishti-get-farmer',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'get_farmer.lambda_handler',
      code: lambda.Code.fromAsset('../backend/lambdas'),
      layers: [sharedLayer],
      role: lambdaRole,
      timeout: cdk.Duration.seconds(30),
      environment: {
        WORKFLOW_TABLE_NAME: workflowTable.tableName,
      },
      logGroup: new logs.LogGroup(this, 'GetFarmerLogGroup', {
        logGroupName: '/aws/lambda/anna-drishti-get-farmer',
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
    });

    // Update Payment Lambda (for payment tracking)
    const updatePaymentFn = new lambda.Function(this, 'UpdatePaymentFunction', {
      functionName: 'anna-drishti-update-payment',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'update_payment.lambda_handler',
      code: lambda.Code.fromAsset('../backend/lambdas'),
      layers: [sharedLayer],
      role: lambdaRole,
      timeout: cdk.Duration.seconds(30),
      environment: {
        WORKFLOW_TABLE_NAME: workflowTable.tableName,
      },
      logGroup: new logs.LogGroup(this, 'UpdatePaymentLogGroup', {
        logGroupName: '/aws/lambda/anna-drishti-update-payment',
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
    });

    // Get Payment Metrics Lambda (for payment dashboard)
    const getPaymentMetricsFn = new lambda.Function(this, 'GetPaymentMetricsFunction', {
      functionName: 'anna-drishti-get-payment-metrics',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'get_payment_metrics.lambda_handler',
      code: lambda.Code.fromAsset('../backend/lambdas'),
      layers: [sharedLayer],
      role: lambdaRole,
      timeout: cdk.Duration.seconds(30),
      environment: {
        WORKFLOW_TABLE_NAME: workflowTable.tableName,
      },
      logGroup: new logs.LogGroup(this, 'GetPaymentMetricsLogGroup', {
        logGroupName: '/aws/lambda/anna-drishti-get-payment-metrics',
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
    });

    // Get Satellite Data Lambda (for crop health monitoring)
    const getSatelliteDataFn = new lambda.Function(this, 'GetSatelliteDataFunction', {
      functionName: 'anna-drishti-get-satellite-data',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'get_satellite_data.lambda_handler',
      code: lambda.Code.fromAsset('../backend/lambdas'),
      layers: [sharedLayer],
      role: lambdaRole,
      timeout: cdk.Duration.seconds(60), // Longer timeout for satellite data processing
      environment: {
        WORKFLOW_TABLE_NAME: workflowTable.tableName,
      },
      logGroup: new logs.LogGroup(this, 'GetSatelliteDataLogGroup', {
        logGroupName: '/aws/lambda/anna-drishti-get-satellite-data',
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

    // Farmer Portfolio API Resources
    const farmersResource = api.root.addResource('farmers');
    const farmerResource = farmersResource.addResource('{farmer_name}');
    
    // GET /farmers (list all farmers)
    farmersResource.addMethod('GET', new apigateway.LambdaIntegration(listFarmersFn));
    
    // GET /farmers/{farmer_name} (get specific farmer details)
    farmerResource.addMethod('GET', new apigateway.LambdaIntegration(getFarmerFn));

    // Payment Tracking API Resources
    const paymentsResource = api.root.addResource('payments');
    const updatePaymentResource = paymentsResource.addResource('update');
    const metricsResource = paymentsResource.addResource('metrics');
    
    // POST /payments/update (update payment status)
    updatePaymentResource.addMethod('POST', new apigateway.LambdaIntegration(updatePaymentFn));
    
    // GET /payments/metrics (get payment metrics)
    metricsResource.addMethod('GET', new apigateway.LambdaIntegration(getPaymentMetricsFn));

    // Satellite Data API Resources
    const satelliteResource = api.root.addResource('satellite');
    
    // POST /satellite (get satellite data for workflow)
    satelliteResource.addMethod('POST', new apigateway.LambdaIntegration(getSatelliteDataFn));

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

    new cdk.CfnOutput(this, 'IVRHandlerArn', {
      value: ivrHandlerFn.functionArn,
      description: 'IVR Handler Lambda ARN (for Lex bot)',
      exportName: 'AnnaDrishtiIVRHandler',
    });
  }
}
