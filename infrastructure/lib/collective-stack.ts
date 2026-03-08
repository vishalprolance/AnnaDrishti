import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import { Construct } from 'constructs';

export interface CollectiveStackProps extends cdk.StackProps {
  environment: string;
  enableRds?: boolean; // Optional - can use DynamoDB only for MVP
}

export class CollectiveStack extends cdk.Stack {
  public readonly apiUrl: string;
  public readonly inventoryTableName: string;
  public readonly contributionsTableName: string;
  public readonly reservationsTableName: string;

  constructor(scope: Construct, id: string, props: CollectiveStackProps) {
    super(scope, id, props);

    const { environment, enableRds = false } = props;

    // ========================================
    // DynamoDB Tables for Real-Time Inventory
    // ========================================

    // Collective Inventory Table
    const inventoryTable = new dynamodb.Table(this, 'CollectiveInventoryTable', {
      tableName: `collective-inventory-${environment}`,
      partitionKey: {
        name: 'fpo_id',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'crop_type',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: environment === 'prod' ? cdk.RemovalPolicy.RETAIN : cdk.RemovalPolicy.DESTROY,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: environment === 'prod',
      },
      stream: dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
    });

    // Farmer Contributions Table
    const contributionsTable = new dynamodb.Table(this, 'FarmerContributionsTable', {
      tableName: `farmer-contributions-${environment}`,
      partitionKey: {
        name: 'contribution_id',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: environment === 'prod' ? cdk.RemovalPolicy.RETAIN : cdk.RemovalPolicy.DESTROY,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: environment === 'prod',
      },
    });

    // GSI for querying by farmer_id
    contributionsTable.addGlobalSecondaryIndex({
      indexName: 'farmer-id-index',
      partitionKey: {
        name: 'farmer_id',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'timestamp',
        type: dynamodb.AttributeType.STRING,
      },
    });

    // GSI for querying by fpo_id and crop_type
    contributionsTable.addGlobalSecondaryIndex({
      indexName: 'fpo-crop-index',
      partitionKey: {
        name: 'fpo_id',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'crop_type',
        type: dynamodb.AttributeType.STRING,
      },
    });

    // Reservations Table
    const reservationsTable = new dynamodb.Table(this, 'ReservationsTable', {
      tableName: `reservations-${environment}`,
      partitionKey: {
        name: 'reservation_id',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: environment === 'prod' ? cdk.RemovalPolicy.RETAIN : cdk.RemovalPolicy.DESTROY,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: environment === 'prod',
      },
      timeToLiveAttribute: 'ttl',
    });

    // GSI for querying by society_id
    reservationsTable.addGlobalSecondaryIndex({
      indexName: 'society-id-index',
      partitionKey: {
        name: 'society_id',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'delivery_date',
        type: dynamodb.AttributeType.STRING,
      },
    });

    // GSI for querying by fpo_id and delivery_date
    reservationsTable.addGlobalSecondaryIndex({
      indexName: 'fpo-delivery-index',
      partitionKey: {
        name: 'fpo_id',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'delivery_date',
        type: dynamodb.AttributeType.STRING,
      },
    });

    // ========================================
    // PostgreSQL RDS (Optional - for relational data)
    // ========================================

    let dbSecret: secretsmanager.ISecret | undefined;
    let dbSecurityGroup: ec2.ISecurityGroup | undefined;
    let lambdaSecurityGroup: ec2.ISecurityGroup | undefined;
    let vpc: ec2.IVpc | undefined;
    let dbInstance: rds.DatabaseInstance | undefined;

    if (enableRds) {
      // Create VPC for RDS
      vpc = new ec2.Vpc(this, 'CollectiveVpc', {
        maxAzs: 2,
        natGateways: 1,
        subnetConfiguration: [
          {
            cidrMask: 24,
            name: 'public',
            subnetType: ec2.SubnetType.PUBLIC,
          },
          {
            cidrMask: 24,
            name: 'private',
            subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
          },
          {
            cidrMask: 28,
            name: 'isolated',
            subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
          },
        ],
      });

      // Security group for RDS
      dbSecurityGroup = new ec2.SecurityGroup(this, 'DbSecurityGroup', {
        vpc,
        description: 'Security group for PostgreSQL RDS',
        allowAllOutbound: true,
      });
      
      // Security group for Lambda
      lambdaSecurityGroup = new ec2.SecurityGroup(this, 'LambdaSecurityGroup', {
        vpc,
        description: 'Security group for Lambda functions',
        allowAllOutbound: true,
      });
      
      // Allow Lambda to connect to RDS
      dbSecurityGroup.addIngressRule(
        lambdaSecurityGroup,
        ec2.Port.tcp(5432),
        'Allow Lambda to connect to PostgreSQL'
      );

      // Create database credentials secret
      dbSecret = new secretsmanager.Secret(this, 'DbSecret', {
        secretName: `collective-db-credentials-${environment}`,
        generateSecretString: {
          secretStringTemplate: JSON.stringify({ username: 'collective_admin' }),
          generateStringKey: 'password',
          excludePunctuation: true,
          includeSpace: false,
        },
      });

      // Create PostgreSQL RDS instance
      dbInstance = new rds.DatabaseInstance(this, 'CollectiveDatabase', {
        engine: rds.DatabaseInstanceEngine.postgres({
          version: rds.PostgresEngineVersion.VER_16,
        }),
        instanceType: ec2.InstanceType.of(
          ec2.InstanceClass.T3,
          ec2.InstanceSize.MICRO
        ),
        vpc,
        vpcSubnets: {
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
        },
        securityGroups: [dbSecurityGroup],
        credentials: rds.Credentials.fromSecret(dbSecret),
        databaseName: 'collective_selling',
        allocatedStorage: 20,
        maxAllocatedStorage: 100,
        backupRetention: environment === 'prod' ? cdk.Duration.days(7) : cdk.Duration.days(1),
        deleteAutomatedBackups: environment !== 'prod',
        removalPolicy: environment === 'prod' ? cdk.RemovalPolicy.SNAPSHOT : cdk.RemovalPolicy.DESTROY,
        deletionProtection: environment === 'prod',
      });

      // Output database endpoint
      new cdk.CfnOutput(this, 'DatabaseEndpoint', {
        value: dbInstance.dbInstanceEndpointAddress,
        description: 'PostgreSQL database endpoint',
        exportName: `CollectiveDbEndpoint-${environment}`,
      });
    }

    // ========================================
    // Lambda Layer for Collective Selling Code
    // ========================================

    const collectiveLayer = new lambda.LayerVersion(this, 'CollectiveLayer', {
      code: lambda.Code.fromAsset('../backend', {
        bundling: {
          image: lambda.Runtime.PYTHON_3_11.bundlingImage,
          platform: 'linux/amd64',
          command: [
            'bash', '-c',
            'pip install -r requirements.txt -t /asset-output/python --platform manylinux2014_x86_64 --only-binary=:all: && ' +
            'cp -r collective /asset-output/python/ && ' +
            'cp -r models /asset-output/python/'
          ],
        },
      }),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_11],
      compatibleArchitectures: [lambda.Architecture.X86_64],
      description: 'Collective selling system dependencies and code',
    });

    // ========================================
    // IAM Role for Lambda Functions
    // ========================================

    const lambdaRole = new iam.Role(this, 'CollectiveLambdaRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaVPCAccessExecutionRole'),
      ],
    });

    // Grant DynamoDB permissions
    inventoryTable.grantReadWriteData(lambdaRole);
    contributionsTable.grantReadWriteData(lambdaRole);
    reservationsTable.grantReadWriteData(lambdaRole);

    // Grant RDS permissions if enabled
    if (dbSecret) {
      dbSecret.grantRead(lambdaRole);
    }

    // Grant CloudWatch permissions
    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'cloudwatch:PutMetricData',
        'logs:CreateLogGroup',
        'logs:CreateLogStream',
        'logs:PutLogEvents',
      ],
      resources: ['*'],
    }));

    // ========================================
    // Lambda Functions for API Endpoints
    // ========================================

    const commonEnv: { [key: string]: string } = {
      ENVIRONMENT: environment,
      INVENTORY_TABLE_NAME: inventoryTable.tableName,
      CONTRIBUTIONS_TABLE_NAME: contributionsTable.tableName,
      RESERVATIONS_TABLE_NAME: reservationsTable.tableName,
      FEATURE_FLAG_COLLECTIVE_MODE: 'true',
    };

    if (dbSecret && dbInstance) {
      commonEnv.DB_SECRET_ARN = dbSecret.secretArn;
      commonEnv.POSTGRES_HOST = dbInstance.dbInstanceEndpointAddress;
      commonEnv.POSTGRES_PORT = '5432';
      commonEnv.POSTGRES_DB = 'collective_selling';
      commonEnv.POSTGRES_USER = 'collective_admin';
    }

    // Main API Lambda (FastAPI application)
    const apiFunction = new lambda.Function(this, 'CollectiveApiFunction', {
      functionName: `collective-api-${environment}`,
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'collective.api.lambda_handler.handler',
      code: lambda.Code.fromAsset('../backend'),
      layers: [collectiveLayer],
      role: lambdaRole,
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      architecture: lambda.Architecture.X86_64,
      environment: commonEnv,
      vpc: vpc,
      vpcSubnets: vpc ? { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS } : undefined,
      securityGroups: lambdaSecurityGroup ? [lambdaSecurityGroup] : undefined,
      logGroup: new logs.LogGroup(this, 'ApiLogGroup', {
        logGroupName: `/aws/lambda/collective-api-${environment}`,
        retention: environment === 'prod' ? logs.RetentionDays.ONE_MONTH : logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
    });

    // ========================================
    // API Gateway
    // ========================================

    const api = new apigateway.RestApi(this, 'CollectiveApi', {
      restApiName: `Collective Selling API - ${environment}`,
      description: 'API for collective selling and allocation system',
      deployOptions: {
        stageName: environment,
        throttlingBurstLimit: 100,
        throttlingRateLimit: 50,
        metricsEnabled: true,
        // Logging disabled - requires CloudWatch Logs role ARN in account settings
        // loggingLevel: apigateway.MethodLoggingLevel.INFO,
        // dataTraceEnabled: environment !== 'prod',
      },
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type', 'Authorization', 'X-API-Key'],
      },
    });

    // Lambda integration
    const apiIntegration = new apigateway.LambdaIntegration(apiFunction, {
      proxy: true,
    });

    // Add proxy resource to handle all paths (includes root)
    const proxyResource = api.root.addProxy({
      defaultIntegration: apiIntegration,
      anyMethod: true,
    });

    // ========================================
    // Outputs
    // ========================================

    this.apiUrl = api.url;
    this.inventoryTableName = inventoryTable.tableName;
    this.contributionsTableName = contributionsTable.tableName;
    this.reservationsTableName = reservationsTable.tableName;

    new cdk.CfnOutput(this, 'ApiUrl', {
      value: this.apiUrl,
      description: 'Collective Selling API URL',
      exportName: `CollectiveApiUrl-${environment}`,
    });

    new cdk.CfnOutput(this, 'InventoryTableName', {
      value: inventoryTable.tableName,
      description: 'DynamoDB table for collective inventory',
      exportName: `CollectiveInventoryTable-${environment}`,
    });

    new cdk.CfnOutput(this, 'ContributionsTableName', {
      value: contributionsTable.tableName,
      description: 'DynamoDB table for farmer contributions',
      exportName: `CollectiveContributionsTable-${environment}`,
    });

    new cdk.CfnOutput(this, 'ReservationsTableName', {
      value: reservationsTable.tableName,
      description: 'DynamoDB table for reservations',
      exportName: `CollectiveReservationsTable-${environment}`,
    });

    new cdk.CfnOutput(this, 'LambdaRoleArn', {
      value: lambdaRole.roleArn,
      description: 'IAM role for Lambda functions',
      exportName: `CollectiveLambdaRole-${environment}`,
    });
  }
}
