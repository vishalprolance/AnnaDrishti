#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { DemoStack } from '../lib/demo-stack';
import { DashboardStack } from '../lib/dashboard-stack';

const app = new cdk.App();

// Get environment from context or default to demo
const environment = app.node.tryGetContext('anna-drishti:environment') || 'demo';

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
