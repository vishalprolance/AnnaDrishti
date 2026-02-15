# Requirements Document: FPO Dashboard

## Introduction

The FPO Dashboard is a React-based web application that provides FPO (Farmer Producer Organization) coordinators with real-time visibility into farmer activities, transaction monitoring, agent execution tracking, and operational oversight. It serves as the central command center for FPO coordinators to manage the Anna Drishti platform, monitor farmer interactions, track sales and processing activities, and intervene when needed.

The dashboard is designed exclusively for FPO coordinators and managers (not individual farmers), provides near-real-time updates with 2-5 second latency, and integrates with multiple backend services including the Backend Foundation & Data Layer, Sell Agent, Process Agent, Market Data Pipeline, Satellite Context Provider, and WhatsApp Integration.

## Glossary

- **FPO_Dashboard**: The web application providing operational oversight for FPO coordinators
- **FPO_Coordinator**: Primary user who manages daily operations for 500+ farmers
- **FPO_Manager**: Secondary user who reviews analytics and makes strategic decisions
- **Sell_Agent**: Backend service that executes sales transactions and negotiations
- **Process_Agent**: Backend service that manages processing diversions
- **Activity_Stream**: Real-time feed of agent actions and farmer interactions
- **Transaction**: A sale, processing diversion, or payment event
- **Farmer_Portfolio**: Collection of farmer profiles, plots, and transaction history
- **Market_Intelligence**: Aggregated data on mandi prices, NDVI trends, and processing capacity
- **Dispute**: A transaction issue requiring coordinator intervention
- **Harvest_Calendar**: Schedule of upcoming harvests across FPO farmers
- **NDVI**: Normalized Difference Vegetation Index (satellite-derived crop health metric)
- **Backend_API**: REST API provided by Backend Foundation & Data Layer
- **WebSocket_Connection**: Persistent connection for real-time activity updates
- **Plot_Boundary_Data**: Geospatial coordinates defining farmer plot boundaries
- **Daily_Analytics**: Performance metrics computed once per day

## Requirements

### Requirement 1: Authentication and Authorization

**User Story:** As an FPO coordinator, I want to securely log in to the dashboard, so that I can access farmer data and operational tools.

#### Acceptance Criteria

1. WHEN an FPO coordinator navigates to the dashboard URL, THE FPO_Dashboard SHALL display an AWS Cognito login page
2. WHEN valid credentials are provided, THE FPO_Dashboard SHALL authenticate the user and establish a session
3. WHEN invalid credentials are provided, THE FPO_Dashboard SHALL display an error message and prevent access
4. WHEN a session expires, THE FPO_Dashboard SHALL redirect the user to the login page
5. THE FPO_Dashboard SHALL restrict access to authenticated FPO coordinators and managers only

### Requirement 2: Real-Time Agent Activity Stream

**User Story:** As an FPO coordinator, I want to see a live stream of agent actions, so that I can monitor farmer interactions in near-real-time.

#### Acceptance Criteria

1. WHEN the dashboard loads, THE FPO_Dashboard SHALL establish a WebSocket connection to the Backend_API
2. WHEN a Sell_Agent or Process_Agent executes an action, THE FPO_Dashboard SHALL display the event in the Activity_Stream within 5 seconds
3. WHEN the WebSocket connection is lost, THE FPO_Dashboard SHALL attempt to reconnect automatically
4. WHEN displaying activity events, THE FPO_Dashboard SHALL show timestamp, agent type, farmer name, and action summary
5. THE FPO_Dashboard SHALL allow filtering the Activity_Stream by agent type, farmer, or time range
6. THE FPO_Dashboard SHALL display the most recent 100 activity events by default

### Requirement 3: Transaction Monitoring

**User Story:** As an FPO coordinator, I want to track sales and processing transactions, so that I can monitor payment status and identify issues.

#### Acceptance Criteria

1. WHEN viewing the transaction monitor, THE FPO_Dashboard SHALL display all transactions from the past 30 days
2. WHEN a transaction is selected, THE FPO_Dashboard SHALL show detailed information including farmer, buyer/processor, quantity, price, payment status, and timestamps
3. THE FPO_Dashboard SHALL allow filtering transactions by status (pending, completed, disputed), farmer, buyer, or date range
4. WHEN a payment is delayed beyond 48 hours, THE FPO_Dashboard SHALL flag the transaction with a warning indicator
5. WHEN a dispute is escalated, THE FPO_Dashboard SHALL display the dispute in a dedicated disputes section
6. THE FPO_Dashboard SHALL allow searching transactions by farmer name, buyer name, or transaction ID within 2 seconds

### Requirement 4: Farmer Portfolio Management

**User Story:** As an FPO coordinator, I want to view farmer profiles and transaction history, so that I can understand individual farmer situations and provide support.

#### Acceptance Criteria

1. WHEN viewing the farmer portfolio, THE FPO_Dashboard SHALL display a list of all farmers managed by the FPO
2. WHEN a farmer is selected, THE FPO_Dashboard SHALL show profile details including name, contact, plot information, and credit readiness status
3. WHEN displaying farmer details, THE FPO_Dashboard SHALL show transaction history for the past 12 months
4. WHERE Plot_Boundary_Data is available, THE FPO_Dashboard SHALL display plot boundaries on a map
5. WHERE Plot_Boundary_Data is unavailable, THE FPO_Dashboard SHALL display plot information in text format without map visualization
6. THE FPO_Dashboard SHALL allow searching farmers by name, phone number, or village within 2 seconds

### Requirement 5: Market Intelligence Dashboard

**User Story:** As an FPO coordinator, I want to visualize market data and crop health trends, so that I can make informed decisions about sales timing and processing.

#### Acceptance Criteria

1. WHEN viewing market intelligence, THE FPO_Dashboard SHALL display current mandi prices for relevant crops
2. WHEN displaying mandi prices, THE FPO_Dashboard SHALL show price trends over the past 30 days using line charts
3. WHERE NDVI data is available, THE FPO_Dashboard SHALL display crop health trends for FPO plots
4. WHEN surplus detection alerts are generated, THE FPO_Dashboard SHALL display them prominently on the market intelligence page
5. THE FPO_Dashboard SHALL display processing capacity information for local processors
6. THE FPO_Dashboard SHALL refresh market intelligence data every 5 minutes

### Requirement 6: Payment Tracking and Dispute Management

**User Story:** As an FPO coordinator, I want to monitor payment status and manage disputes, so that I can ensure farmers receive timely payments and resolve issues.

#### Acceptance Criteria

1. WHEN viewing payment tracking, THE FPO_Dashboard SHALL display all pending payments with expected payment dates
2. WHEN a payment is delayed beyond 48 hours, THE FPO_Dashboard SHALL flag it with a high-priority indicator
3. WHEN viewing a dispute, THE FPO_Dashboard SHALL show dispute details, involved parties, issue description, and current status
4. THE FPO_Dashboard SHALL allow coordinators to add notes to disputes for tracking resolution progress
5. WHEN a dispute is resolved, THE FPO_Dashboard SHALL allow marking it as closed with a resolution summary
6. THE FPO_Dashboard SHALL display payment success rate and average payment time metrics

### Requirement 7: Harvest Calendar and Planning

**User Story:** As an FPO coordinator, I want to view upcoming harvests, so that I can coordinate aggregation and plan sales activities.

#### Acceptance Criteria

1. WHEN viewing the harvest calendar, THE FPO_Dashboard SHALL display upcoming harvests for the next 60 days
2. WHEN displaying harvest information, THE FPO_Dashboard SHALL show farmer name, crop type, plot size, and expected harvest date
3. THE FPO_Dashboard SHALL allow filtering the harvest calendar by crop type, village, or date range
4. WHERE game theory recommendations are available, THE FPO_Dashboard SHALL display suggested aggregation strategies
5. THE FPO_Dashboard SHALL allow coordinators to mark harvests as completed or delayed
6. THE FPO_Dashboard SHALL send notifications for harvests occurring within the next 7 days

### Requirement 8: Insurance and Scheme Alerts

**User Story:** As an FPO coordinator, I want to see crop distress alerts and scheme eligibility notifications, so that I can help farmers access support programs.

#### Acceptance Criteria

1. WHEN crop distress is detected, THE FPO_Dashboard SHALL display an alert with affected farmer, crop, and distress type
2. WHEN a farmer becomes eligible for a government scheme, THE FPO_Dashboard SHALL display a notification with scheme details and application deadline
3. THE FPO_Dashboard SHALL allow filtering alerts by priority (high, medium, low) and type (distress, scheme, other)
4. WHEN an alert is addressed, THE FPO_Dashboard SHALL allow marking it as resolved
5. THE FPO_Dashboard SHALL display the count of unresolved alerts prominently on the dashboard home page
6. THE FPO_Dashboard SHALL retain alert history for 12 months

### Requirement 9: Analytics and Reporting

**User Story:** As an FPO manager, I want to view performance metrics and trends, so that I can assess FPO effectiveness and make strategic decisions.

#### Acceptance Criteria

1. WHEN viewing analytics, THE FPO_Dashboard SHALL display FPO performance metrics including total farmers, total transactions, and total revenue
2. THE FPO_Dashboard SHALL display farmer income trends over the past 12 months using bar or line charts
3. THE FPO_Dashboard SHALL display buyer and processor reliability scores based on payment timeliness and transaction success rates
4. THE FPO_Dashboard SHALL compute and display Daily_Analytics once per day (not real-time)
5. THE FPO_Dashboard SHALL allow exporting analytics data as CSV or PDF reports
6. THE FPO_Dashboard SHALL display year-over-year comparison metrics where applicable

### Requirement 10: Performance and Responsiveness

**User Story:** As an FPO coordinator, I want the dashboard to load quickly and respond promptly, so that I can work efficiently even on slower connections.

#### Acceptance Criteria

1. WHEN the dashboard is accessed on a 4G connection, THE FPO_Dashboard SHALL load the initial page within 3 seconds
2. WHEN searching or filtering data, THE FPO_Dashboard SHALL return results within 2 seconds
3. THE FPO_Dashboard SHALL support at least 10 concurrent FPO coordinator sessions without performance degradation
4. WHEN large datasets are displayed, THE FPO_Dashboard SHALL implement pagination or virtual scrolling to maintain responsiveness
5. THE FPO_Dashboard SHALL cache frequently accessed data to reduce API calls and improve load times

### Requirement 11: Responsive Design and Accessibility

**User Story:** As an FPO coordinator, I want to use the dashboard on tablets and desktops, so that I can work from different devices in the field or office.

#### Acceptance Criteria

1. THE FPO_Dashboard SHALL display correctly on tablet devices (768px width and above)
2. THE FPO_Dashboard SHALL display correctly on desktop devices (1024px width and above)
3. THE FPO_Dashboard SHALL use responsive layouts that adapt to different screen sizes
4. WHERE feasible, THE FPO_Dashboard SHALL follow WCAG 2.1 AA accessibility guidelines for color contrast and keyboard navigation
5. THE FPO_Dashboard SHALL provide text alternatives for data visualizations where possible

### Requirement 12: Error Handling and Graceful Degradation

**User Story:** As an FPO coordinator, I want the dashboard to handle errors gracefully, so that I can continue working even when some services are unavailable.

#### Acceptance Criteria

1. WHEN the Backend_API is unavailable, THE FPO_Dashboard SHALL display a clear error message and retry automatically
2. WHEN the WebSocket_Connection fails, THE FPO_Dashboard SHALL fall back to polling for activity updates every 10 seconds
3. WHERE Plot_Boundary_Data is missing, THE FPO_Dashboard SHALL display plot information without map visualization
4. WHEN data loading fails, THE FPO_Dashboard SHALL display cached data with a staleness indicator
5. IF an API request times out after 10 seconds, THEN THE FPO_Dashboard SHALL display a timeout error and allow manual retry
6. THE FPO_Dashboard SHALL log client-side errors for debugging and monitoring purposes

### Requirement 13: Data Refresh and Synchronization

**User Story:** As an FPO coordinator, I want the dashboard to show current data, so that I can make decisions based on accurate information.

#### Acceptance Criteria

1. WHEN the dashboard is active, THE FPO_Dashboard SHALL refresh the Activity_Stream via WebSocket in near-real-time (2-5 second latency)
2. THE FPO_Dashboard SHALL refresh market intelligence data every 5 minutes
3. THE FPO_Dashboard SHALL refresh transaction and payment data every 30 seconds
4. THE FPO_Dashboard SHALL compute Daily_Analytics once per day at midnight
5. WHEN a user manually triggers a refresh, THE FPO_Dashboard SHALL fetch the latest data from the Backend_API
6. THE FPO_Dashboard SHALL display the last update timestamp for each data section

### Requirement 14: Integration with Backend Services

**User Story:** As a system architect, I want the dashboard to integrate with backend services, so that it can access farmer data, transactions, and agent activity.

#### Acceptance Criteria

1. THE FPO_Dashboard SHALL authenticate API requests using AWS Cognito tokens
2. THE FPO_Dashboard SHALL call the Backend_API REST endpoints for farmer data, transactions, and analytics
3. THE FPO_Dashboard SHALL establish a WebSocket_Connection to API Gateway WebSocket API for real-time updates
4. WHEN API requests fail with 401 Unauthorized, THE FPO_Dashboard SHALL refresh the authentication token and retry
5. THE FPO_Dashboard SHALL handle API rate limiting by implementing exponential backoff
6. THE FPO_Dashboard SHALL validate API responses against expected schemas before rendering data

### Requirement 15: Deployment and Hosting

**User Story:** As a system administrator, I want the dashboard to be deployed on AWS infrastructure, so that it is scalable, secure, and highly available.

#### Acceptance Criteria

1. THE FPO_Dashboard SHALL be deployed as a static site on AWS S3
2. THE FPO_Dashboard SHALL be served via AWS CloudFront for CDN and HTTPS support
3. THE FPO_Dashboard SHALL use CloudFront for caching static assets (JS, CSS, images)
4. THE FPO_Dashboard SHALL configure CloudFront to route API requests to API Gateway
5. THE FPO_Dashboard SHALL implement cache-busting for JavaScript and CSS files on new deployments
6. THE FPO_Dashboard SHALL serve all content over HTTPS only
