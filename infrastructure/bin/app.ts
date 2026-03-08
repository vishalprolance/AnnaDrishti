#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { DemoStack } from '../lib/demo-stack';
import { DashboardStack } from '../lib/dashboard-stack';
import { CollectiveStack } from '../lib/collective-stack';
import { MonitoringStack } from '../lib/monitoring-stack';

const app = new cdk.App();

// Get environment from context or default to demo
const environment = app.node.tryGetContext('anna-drishti:environment') || 'demo';
const alarmEmail = app.node.tryGetContext('anna-drishti:alarm-email');

// Demo Stack - Backend infrastructure
const demoStack = new DemoStack(app, 'AnnaDrishtiDemoStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'ap-south-1',
  },
  description: 'Anna Drishti Hackathon MVP - Backend Infrastructure',
  tags: {
    Project: 'AnnaDrishti',
    Environment: environment,
    Phase: 'Hackathon-MVP',
  },
});

// Collective Stack - Collective Selling & Allocation
const collectiveStack = new CollectiveStack(app, 'AnnaDrishtiCollectiveStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'ap-south-1',
  },
  description: 'Anna Drishti Collective Selling & Allocation System',
  tags: {
    Project: 'AnnaDrishti',
    Environment: environment,
    Phase: 'Collective-Selling',
  },
  environment: environment,
  enableRds: false, // Set to true to enable PostgreSQL RDS
});

// Monitoring Stack - CloudWatch dashboards and alarms
const monitoringStack = new MonitoringStack(app, 'AnnaDrishtiMonitoringStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'ap-south-1',
  },
  description: 'Anna Drishti Collective Selling - Monitoring & Alerting',
  tags: {
    Project: 'AnnaDrishti',
    Environment: environment,
    Phase: 'Collective-Selling',
  },
  environment: environment,
  apiName: `Collective Selling API - ${environment}`,
  lambdaFunctionName: `collective-api-${environment}`,
  inventoryTableName: collectiveStack.inventoryTableName,
  contributionsTableName: collectiveStack.contributionsTableName,
  reservationsTableName: collectiveStack.reservationsTableName,
  alarmEmail: alarmEmail,
});

// Add dependency
monitoringStack.addDependency(collectiveStack);

// Dashboard Stack - Frontend hosting
const dashboardStack = new DashboardStack(app, 'AnnaDrishtiDashboardStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'ap-south-1',
  },
  description: 'Anna Drishti Hackathon MVP - Dashboard Hosting',
  tags: {
    Project: 'AnnaDrishti',
    Environment: environment,
    Phase: 'Hackathon-MVP',
  },
  apiUrl: demoStack.apiUrl,
  wsUrl: demoStack.wsUrl,
});

app.synth();
