# Design Document: Hackathon MVP

## Overview

This is a **48-hour hackathon MVP** designed to demonstrate Anna Drishti's core value proposition through a live, working demo. The system focuses on **demo impact over production completeness**, with clear labeling of what's real vs. simulated.

### Design Philosophy

1. **Demo-Driven**: Every component serves the 12-minute stage presentation
2. **Real Where It Matters**: Live AI negotiation, real market data, actual AWS services
3. **Simulated Where Smart**: Pre-loaded satellite data, mock processor capacity
4. **Honest Labeling**: Clear badges showing what's live vs. simulated
5. **Fail-Safe**: Fallbacks for every external dependency

## Architecture

The system uses AWS Step Functions to orchestrate a demo workflow, with Lambda functions for agent logic, Bedrock for AI negotiation, and a React dashboard for real-time visualization.

## Key Components

1. **Farmer Input Form** - Web form to trigger demo
2. **Market Scanner** - Real Agmarknet API calls
3. **Surplus Detector** - Processing diversion logic
4. **WhatsApp Negotiation** - Live Bedrock + WhatsApp Business API
5. **Real-Time Dashboard** - WebSocket updates
6. **Processing Visualization** - Counter-factual comparison
7. **Game Theory Simulation** - Pre-computed coordination demo

## AWS Services

- Step Functions (orchestration)
- Lambda (agent logic)
- Bedrock Claude 3 Haiku (negotiation)
- DynamoDB (state)
- API Gateway (REST + WebSocket)
- S3 + CloudFront (dashboard)
- EventBridge (events)

## Demo Flow

1. Submit farmer input → 2. Scan markets → 3. Detect surplus → 4. Negotiate on WhatsApp → 5. Show income comparison → 6. Visualize processing impact → 7. Demo game theory

Total time: ~4 minutes for full workflow
