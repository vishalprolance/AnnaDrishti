import * as cdk from 'aws-cdk-lib';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as subscriptions from 'aws-cdk-lib/aws-sns-subscriptions';
import * as actions from 'aws-cdk-lib/aws-cloudwatch-actions';
import { Construct } from 'constructs';

export interface MonitoringStackProps extends cdk.StackProps {
  environment: string;
  apiName: string;
  lambdaFunctionName: string;
  inventoryTableName: string;
  contributionsTableName: string;
  reservationsTableName: string;
  alarmEmail?: string;
}

export class MonitoringStack extends cdk.Stack {
  public readonly alarmTopic: sns.Topic;
  public readonly dashboard: cloudwatch.Dashboard;

  constructor(scope: Construct, id: string, props: MonitoringStackProps) {
    super(scope, id, props);

    const {
      environment,
      apiName,
      lambdaFunctionName,
      inventoryTableName,
      contributionsTableName,
      reservationsTableName,
      alarmEmail,
    } = props;

    // ========================================
    // SNS Topic for Alarms
    // ========================================

    this.alarmTopic = new sns.Topic(this, 'AlarmTopic', {
      topicName: `collective-alarms-${environment}`,
      displayName: 'Collective Selling System Alarms',
    });

    // Subscribe email if provided
    if (alarmEmail) {
      this.alarmTopic.addSubscription(
        new subscriptions.EmailSubscription(alarmEmail)
      );
    }

    // ========================================
    // CloudWatch Dashboard
    // ========================================

    this.dashboard = new cloudwatch.Dashboard(this, 'CollectiveDashboard', {
      dashboardName: `collective-selling-${environment}`,
    });

    // ========================================
    // API Gateway Metrics
    // ========================================

    const apiRequestsMetric = new cloudwatch.Metric({
      namespace: 'AWS/ApiGateway',
      metricName: 'Count',
      dimensionsMap: {
        ApiName: apiName,
      },
      statistic: 'Sum',
      period: cdk.Duration.minutes(5),
    });

    const api4xxMetric = new cloudwatch.Metric({
      namespace: 'AWS/ApiGateway',
      metricName: '4XXError',
      dimensionsMap: {
        ApiName: apiName,
      },
      statistic: 'Sum',
      period: cdk.Duration.minutes(5),
    });

    const api5xxMetric = new cloudwatch.Metric({
      namespace: 'AWS/ApiGateway',
      metricName: '5XXError',
      dimensionsMap: {
        ApiName: apiName,
      },
      statistic: 'Sum',
      period: cdk.Duration.minutes(5),
    });

    const apiLatencyMetric = new cloudwatch.Metric({
      namespace: 'AWS/ApiGateway',
      metricName: 'Latency',
      dimensionsMap: {
        ApiName: apiName,
      },
      statistic: 'Average',
      period: cdk.Duration.minutes(5),
    });

    // API Gateway Alarms
    const api5xxAlarm = new cloudwatch.Alarm(this, 'Api5xxAlarm', {
      alarmName: `collective-api-5xx-${environment}`,
      metric: api5xxMetric,
      threshold: 10,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      alarmDescription: 'API Gateway 5xx errors exceeded threshold',
    });
    api5xxAlarm.addAlarmAction(new actions.SnsAction(this.alarmTopic));

    const apiLatencyAlarm = new cloudwatch.Alarm(this, 'ApiLatencyAlarm', {
      alarmName: `collective-api-latency-${environment}`,
      metric: apiLatencyMetric,
      threshold: 2000, // 2 seconds
      evaluationPeriods: 2,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      alarmDescription: 'API Gateway latency exceeded threshold',
    });
    apiLatencyAlarm.addAlarmAction(new actions.SnsAction(this.alarmTopic));

    // ========================================
    // Lambda Metrics
    // ========================================

    const lambdaInvocationsMetric = new cloudwatch.Metric({
      namespace: 'AWS/Lambda',
      metricName: 'Invocations',
      dimensionsMap: {
        FunctionName: lambdaFunctionName,
      },
      statistic: 'Sum',
      period: cdk.Duration.minutes(5),
    });

    const lambdaErrorsMetric = new cloudwatch.Metric({
      namespace: 'AWS/Lambda',
      metricName: 'Errors',
      dimensionsMap: {
        FunctionName: lambdaFunctionName,
      },
      statistic: 'Sum',
      period: cdk.Duration.minutes(5),
    });

    const lambdaThrottlesMetric = new cloudwatch.Metric({
      namespace: 'AWS/Lambda',
      metricName: 'Throttles',
      dimensionsMap: {
        FunctionName: lambdaFunctionName,
      },
      statistic: 'Sum',
      period: cdk.Duration.minutes(5),
    });

    const lambdaDurationMetric = new cloudwatch.Metric({
      namespace: 'AWS/Lambda',
      metricName: 'Duration',
      dimensionsMap: {
        FunctionName: lambdaFunctionName,
      },
      statistic: 'Average',
      period: cdk.Duration.minutes(5),
    });

    const lambdaConcurrentExecutionsMetric = new cloudwatch.Metric({
      namespace: 'AWS/Lambda',
      metricName: 'ConcurrentExecutions',
      dimensionsMap: {
        FunctionName: lambdaFunctionName,
      },
      statistic: 'Maximum',
      period: cdk.Duration.minutes(5),
    });

    // Lambda Alarms
    const lambdaErrorsAlarm = new cloudwatch.Alarm(this, 'LambdaErrorsAlarm', {
      alarmName: `collective-lambda-errors-${environment}`,
      metric: lambdaErrorsMetric,
      threshold: 5,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      alarmDescription: 'Lambda function errors exceeded threshold',
    });
    lambdaErrorsAlarm.addAlarmAction(new actions.SnsAction(this.alarmTopic));

    const lambdaThrottlesAlarm = new cloudwatch.Alarm(this, 'LambdaThrottlesAlarm', {
      alarmName: `collective-lambda-throttles-${environment}`,
      metric: lambdaThrottlesMetric,
      threshold: 1,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      alarmDescription: 'Lambda function throttles detected',
    });
    lambdaThrottlesAlarm.addAlarmAction(new actions.SnsAction(this.alarmTopic));

    const lambdaDurationAlarm = new cloudwatch.Alarm(this, 'LambdaDurationAlarm', {
      alarmName: `collective-lambda-duration-${environment}`,
      metric: lambdaDurationMetric,
      threshold: 5000, // 5 seconds
      evaluationPeriods: 2,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      alarmDescription: 'Lambda function duration exceeded threshold',
    });
    lambdaDurationAlarm.addAlarmAction(new actions.SnsAction(this.alarmTopic));

    // ========================================
    // DynamoDB Metrics
    // ========================================

    const createDynamoDbMetrics = (tableName: string, tableLabel: string) => {
      const readCapacityMetric = new cloudwatch.Metric({
        namespace: 'AWS/DynamoDB',
        metricName: 'ConsumedReadCapacityUnits',
        dimensionsMap: {
          TableName: tableName,
        },
        statistic: 'Sum',
        period: cdk.Duration.minutes(5),
      });

      const writeCapacityMetric = new cloudwatch.Metric({
        namespace: 'AWS/DynamoDB',
        metricName: 'ConsumedWriteCapacityUnits',
        dimensionsMap: {
          TableName: tableName,
        },
        statistic: 'Sum',
        period: cdk.Duration.minutes(5),
      });

      const userErrorsMetric = new cloudwatch.Metric({
        namespace: 'AWS/DynamoDB',
        metricName: 'UserErrors',
        dimensionsMap: {
          TableName: tableName,
        },
        statistic: 'Sum',
        period: cdk.Duration.minutes(5),
      });

      const systemErrorsMetric = new cloudwatch.Metric({
        namespace: 'AWS/DynamoDB',
        metricName: 'SystemErrors',
        dimensionsMap: {
          TableName: tableName,
        },
        statistic: 'Sum',
        period: cdk.Duration.minutes(5),
      });

      // DynamoDB Alarms
      const userErrorsAlarm = new cloudwatch.Alarm(this, `${tableLabel}UserErrorsAlarm`, {
        alarmName: `collective-dynamodb-${tableLabel.toLowerCase()}-user-errors-${environment}`,
        metric: userErrorsMetric,
        threshold: 10,
        evaluationPeriods: 1,
        comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
        alarmDescription: `DynamoDB ${tableLabel} user errors exceeded threshold`,
      });
      userErrorsAlarm.addAlarmAction(new actions.SnsAction(this.alarmTopic));

      const systemErrorsAlarm = new cloudwatch.Alarm(this, `${tableLabel}SystemErrorsAlarm`, {
        alarmName: `collective-dynamodb-${tableLabel.toLowerCase()}-system-errors-${environment}`,
        metric: systemErrorsMetric,
        threshold: 1,
        evaluationPeriods: 1,
        comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
        alarmDescription: `DynamoDB ${tableLabel} system errors detected`,
      });
      systemErrorsAlarm.addAlarmAction(new actions.SnsAction(this.alarmTopic));

      return {
        readCapacityMetric,
        writeCapacityMetric,
        userErrorsMetric,
        systemErrorsMetric,
      };
    };

    const inventoryMetrics = createDynamoDbMetrics(inventoryTableName, 'Inventory');
    const contributionsMetrics = createDynamoDbMetrics(contributionsTableName, 'Contributions');
    const reservationsMetrics = createDynamoDbMetrics(reservationsTableName, 'Reservations');

    // ========================================
    // Dashboard Widgets
    // ========================================

    // API Gateway widgets
    this.dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'API Gateway - Requests',
        left: [apiRequestsMetric],
        width: 12,
      }),
      new cloudwatch.GraphWidget({
        title: 'API Gateway - Errors',
        left: [api4xxMetric, api5xxMetric],
        width: 12,
      })
    );

    this.dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'API Gateway - Latency',
        left: [apiLatencyMetric],
        width: 24,
      })
    );

    // Lambda widgets
    this.dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'Lambda - Invocations & Errors',
        left: [lambdaInvocationsMetric],
        right: [lambdaErrorsMetric, lambdaThrottlesMetric],
        width: 12,
      }),
      new cloudwatch.GraphWidget({
        title: 'Lambda - Duration',
        left: [lambdaDurationMetric],
        width: 12,
      })
    );

    this.dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'Lambda - Concurrent Executions',
        left: [lambdaConcurrentExecutionsMetric],
        width: 24,
      })
    );

    // DynamoDB widgets
    this.dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'DynamoDB - Read Capacity',
        left: [
          inventoryMetrics.readCapacityMetric,
          contributionsMetrics.readCapacityMetric,
          reservationsMetrics.readCapacityMetric,
        ],
        width: 12,
      }),
      new cloudwatch.GraphWidget({
        title: 'DynamoDB - Write Capacity',
        left: [
          inventoryMetrics.writeCapacityMetric,
          contributionsMetrics.writeCapacityMetric,
          reservationsMetrics.writeCapacityMetric,
        ],
        width: 12,
      })
    );

    this.dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'DynamoDB - Errors',
        left: [
          inventoryMetrics.userErrorsMetric,
          contributionsMetrics.userErrorsMetric,
          reservationsMetrics.userErrorsMetric,
        ],
        right: [
          inventoryMetrics.systemErrorsMetric,
          contributionsMetrics.systemErrorsMetric,
          reservationsMetrics.systemErrorsMetric,
        ],
        width: 24,
      })
    );

    // ========================================
    // Outputs
    // ========================================

    new cdk.CfnOutput(this, 'AlarmTopicArn', {
      value: this.alarmTopic.topicArn,
      description: 'SNS topic for alarms',
      exportName: `CollectiveAlarmTopic-${environment}`,
    });

    new cdk.CfnOutput(this, 'DashboardUrl', {
      value: `https://console.aws.amazon.com/cloudwatch/home?region=${this.region}#dashboards:name=${this.dashboard.dashboardName}`,
      description: 'CloudWatch dashboard URL',
      exportName: `CollectiveDashboardUrl-${environment}`,
    });
  }
}
