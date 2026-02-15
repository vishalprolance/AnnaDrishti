# Implementation Plan: FPO Dashboard

## Overview

This implementation plan breaks down the FPO Dashboard into incremental development phases, starting with foundational infrastructure (authentication, API integration, state management) and progressively building feature modules. Each phase includes implementation tasks followed by property-based tests to validate correctness early.

The dashboard is built with React 18, TypeScript 5, React Query for server state, Zustand for client state, and shadcn/ui components. Testing uses Vitest + React Testing Library for unit tests, fast-check for property-based tests, and Playwright for E2E tests.

## Tasks

- [ ] 1. Project Setup and Infrastructure
  - Initialize Vite + React + TypeScript project with recommended configuration
  - Install core dependencies: React Query, Zustand, React Router, Tailwind CSS, shadcn/ui
  - Install testing dependencies: Vitest, React Testing Library, fast-check, Playwright
  - Configure TypeScript with strict mode and path aliases
  - Set up Tailwind CSS with shadcn/ui configuration
  - Create folder structure: features/, shared/, services/, stores/
  - Configure ESLint and Prettier for code quality
  - Set up Git hooks for pre-commit linting and type checking
  - _Requirements: 15.1, 15.5_

- [ ] 2. Authentication Module
  - [ ] 2.1 Implement AWS Cognito authentication service
    - Create CognitoAuthService with login, logout, refreshToken, getAccessToken methods
    - Integrate AWS Amplify for Cognito hosted UI
    - Implement token storage in memory (not localStorage for security)
    - Handle token expiration and automatic refresh
    - _Requirements: 1.1, 1.2, 1.4_


  - [ ]* 2.2 Write property test for invalid credentials rejection
    - **Property 2: Invalid Credentials Rejection**
    - **Validates: Requirements 1.3**

  - [ ] 2.3 Create AuthProvider React context
    - Implement AuthProvider component with AuthState (user, isAuthenticated, isLoading, error)
    - Provide login, logout, and token refresh functions via context
    - Handle authentication state persistence across page reloads
    - _Requirements: 1.2, 1.4_

  - [ ] 2.4 Implement ProtectedRoute component
    - Create route guard that checks authentication status
    - Redirect unauthenticated users to login page
    - Preserve intended destination for post-login redirect
    - _Requirements: 1.5_

  - [ ]* 2.5 Write property test for protected route access control
    - **Property 3: Protected Route Access Control**
    - **Validates: Requirements 1.5**

  - [ ] 2.6 Create LoginPage component
    - Integrate Cognito hosted UI for login
    - Handle authentication callback and token exchange
    - Display authentication errors to users
    - _Requirements: 1.1, 1.3_

  - [ ]* 2.7 Write unit tests for authentication flow
    - Test login success and failure scenarios
    - Test session expiration and redirect
    - Test token refresh on 401 errors

- [ ] 3. API Integration Layer
  - [ ] 3.1 Create REST API client
    - Implement RESTClient class with get, post, put, delete methods
    - Add authentication token to all requests via interceptor
    - Configure base URL and default headers
    - Implement request/response logging for debugging
    - _Requirements: 14.1, 14.2_

  - [ ]* 3.2 Write property test for authentication token inclusion
    - **Property 1: Authentication Token Inclusion**
    - **Validates: Requirements 14.1**

  - [ ] 3.3 Implement error handling and retry logic
    - Handle 401 Unauthorized with token refresh and retry
    - Handle 429 Rate Limiting with exponential backoff
    - Handle network errors with automatic retry (max 3 attempts)
    - Handle timeouts (10 second threshold)
    - _Requirements: 12.1, 12.5, 14.4, 14.5_

  - [ ]* 3.4 Write property test for token refresh on 401
    - **Property 45: Token Refresh on 401 Unauthorized**
    - **Validates: Requirements 14.4**

  - [ ]* 3.5 Write property test for exponential backoff on rate limiting
    - **Property 46: Exponential Backoff for Rate Limiting**
    - **Validates: Requirements 14.5**

  - [ ]* 3.6 Write property test for API error handling
    - **Property 39: API Error Handling**
    - **Validates: Requirements 12.1**

  - [ ]* 3.7 Write property test for API timeout handling
    - **Property 41: API Timeout Handling**
    - **Validates: Requirements 12.5**

  - [ ] 3.8 Implement API response validation
    - Create Zod schemas for all API response types
    - Validate responses before returning data
    - Handle validation failures gracefully
    - _Requirements: 14.6_

  - [ ]* 3.9 Write property test for API response schema validation
    - **Property 47: API Response Schema Validation**
    - **Validates: Requirements 14.6**

  - [ ] 3.10 Create WebSocket client
    - Implement WebSocketClient class with connect, disconnect, onMessage, onError methods
    - Add authentication token to WebSocket connection
    - Implement automatic reconnection with exponential backoff
    - Implement fallback to polling when WebSocket fails repeatedly
    - _Requirements: 2.1, 2.3, 12.2_

  - [ ]* 3.11 Write unit tests for WebSocket reconnection
    - Test automatic reconnection on connection loss
    - Test fallback to polling after repeated failures
    - Test message handling and error handling

- [ ] 4. State Management Setup
  - [ ] 4.1 Configure React Query
    - Set up QueryClient with default options (stale time, cache time, retry logic)
    - Create QueryClientProvider wrapper
    - Configure devtools for development
    - _Requirements: 10.5, 13.2, 13.3_

  - [ ]* 4.2 Write property test for data caching behavior
    - **Property 36: Data Caching Behavior**
    - **Validates: Requirements 10.5**

  - [ ] 4.3 Create Zustand store for UI state
    - Define UIState interface (sidebarOpen, activeModule, theme, notifications)
    - Implement actions for updating UI state
    - Add persistence for user preferences (theme)
    - _Requirements: 11.1, 11.2_

  - [ ] 4.4 Implement error logging service
    - Create error logger that captures errors with context
    - Log to console in development, send to monitoring service in production
    - Include error message, stack trace, user action, timestamp
    - _Requirements: 12.6_

  - [ ]* 4.5 Write property test for client-side error logging
    - **Property 42: Client-Side Error Logging**
    - **Validates: Requirements 12.6**

- [ ] 5. Shared UI Components
  - [ ] 5.1 Set up shadcn/ui components
    - Install and configure shadcn/ui CLI
    - Add core components: Button, Input, Select, Card, Table, Dialog, Alert, Badge
    - Customize theme colors and typography
    - _Requirements: 11.1, 11.2_

  - [ ] 5.2 Create DataTable component
    - Implement reusable table with sorting, filtering, and pagination
    - Support column configuration and custom cell renderers
    - Implement virtual scrolling for large datasets
    - _Requirements: 10.4_

  - [ ]* 5.3 Write property test for pagination with large datasets
    - **Property 35: Pagination for Large Datasets**
    - **Validates: Requirements 10.4**

  - [ ] 5.4 Create SearchBar component
    - Implement debounced search input (300ms delay)
    - Support placeholder text and clear button
    - Emit search events to parent components
    - _Requirements: 3.6, 4.6_

  - [ ] 5.5 Create DateRangePicker component
    - Implement date range selection with calendar UI
    - Support preset ranges (last 7 days, last 30 days, last 12 months)
    - Validate date ranges (start date before end date)
    - _Requirements: 3.3, 7.3_

  - [ ] 5.6 Create ErrorBoundary component
    - Catch rendering errors in child components
    - Display fallback UI with error message
    - Provide "Try Again" button to reset error state
    - Log errors with context
    - _Requirements: 12.1_

  - [ ] 5.7 Create LoadingState and EmptyState components
    - Implement consistent loading indicators (skeleton screens)
    - Implement consistent empty state messaging
    - Support custom messages and actions
    - _Requirements: 12.4_

- [ ] 6. Checkpoint - Ensure infrastructure is working
  - Verify authentication flow works end-to-end
  - Verify API client makes authenticated requests
  - Verify WebSocket client connects and receives messages
  - Verify React Query caching works correctly
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 7. Activity Stream Module
  - [ ] 7.1 Create ActivityEvent type and API integration
    - Define ActivityEvent interface (id, timestamp, agentType, farmerId, farmerName, actionType, actionSummary, metadata)
    - Create API endpoint functions for fetching activity history
    - Create WebSocket message handler for real-time events
    - _Requirements: 2.2, 2.4_

  - [ ] 7.2 Implement ActivityStream component
    - Display list of activity events with infinite scroll
    - Establish WebSocket connection on mount
    - Handle incoming WebSocket messages and update state
    - Display connection status indicator
    - Limit display to most recent 100 events by default
    - _Requirements: 2.1, 2.2, 2.6_

  - [ ] 7.3 Create ActivityCard component
    - Display individual activity event with timestamp, agent type, farmer name, action summary
    - Format timestamp as relative time (e.g., "2 minutes ago")
    - Use color coding for agent types (sell vs process)
    - _Requirements: 2.4_

  - [ ]* 7.4 Write property test for activity event field completeness
    - **Property 4: Activity Event Field Completeness**
    - **Validates: Requirements 2.4**

  - [ ] 7.5 Implement ActivityFilters component
    - Add filters for agent type (sell, process, all)
    - Add filter for specific farmer (searchable dropdown)
    - Add filter for time range (last hour, last 24 hours, last 7 days, custom)
    - Apply filters to activity stream
    - _Requirements: 2.5_

  - [ ]* 7.6 Write property test for activity stream filtering correctness
    - **Property 5: Activity Stream Filtering Correctness**
    - **Validates: Requirements 2.5**

  - [ ]* 7.7 Write unit tests for activity stream
    - Test WebSocket connection establishment
    - Test event display and ordering
    - Test 100 event limit
    - Test filter application

- [ ] 8. Transaction Monitoring Module
  - [ ] 8.1 Create Transaction and Dispute types
    - Define Transaction interface (id, type, farmerId, farmerName, buyerOrProcessorId, buyerOrProcessorName, cropType, quantity, pricePerUnit, totalAmount, paymentStatus, paymentDueDate, paymentCompletedDate, createdAt, updatedAt)
    - Define Dispute interface (id, transactionId, farmerId, farmerName, issueType, issueDescription, status, notes, createdAt, resolvedAt, resolutionSummary)
    - Define DisputeNote interface (id, authorId, authorName, content, createdAt)
    - _Requirements: 3.2, 6.3_

  - [ ] 8.2 Create API integration for transactions
    - Implement fetchTransactions with date range filtering (default: last 30 days)
    - Implement fetchTransactionById for detail view
    - Implement fetchDisputes for dispute list
    - Implement addDisputeNote mutation
    - Implement resolveDispute mutation
    - _Requirements: 3.1, 3.2, 3.5, 6.1, 6.4, 6.5_

  - [ ]* 8.3 Write property test for API endpoint correctness
    - **Property 44: API Endpoint Correctness**
    - **Validates: Requirements 14.2**

  - [ ] 8.3 Implement TransactionList component
    - Display transactions in DataTable with sorting and pagination
    - Show transaction summary: farmer, buyer/processor, crop, quantity, amount, payment status
    - Apply 30-day date filter by default
    - Highlight delayed payments (>48 hours overdue) with warning indicator
    - _Requirements: 3.1, 3.4_

  - [ ]* 8.4 Write property test for transaction date range filtering
    - **Property 6: Transaction Date Range Filtering**
    - **Validates: Requirements 3.1**

  - [ ]* 8.5 Write property test for payment delay flagging
    - **Property 9: Payment Delay Flagging**
    - **Validates: Requirements 3.4, 6.2**

  - [ ] 8.6 Implement TransactionFilters component
    - Add filter for payment status (pending, completed, delayed, disputed)
    - Add filter for farmer (searchable dropdown)
    - Add filter for buyer/processor (searchable dropdown)
    - Add date range filter
    - _Requirements: 3.3_

  - [ ]* 8.7 Write property test for multi-dimensional transaction filtering
    - **Property 8: Multi-Dimensional Transaction Filtering**
    - **Validates: Requirements 3.3**

  - [ ] 8.8 Implement TransactionDetail component
    - Display all transaction fields in detail view
    - Show payment timeline (created, due, completed dates)
    - Display dispute information if applicable
    - Provide link to farmer profile
    - _Requirements: 3.2_

  - [ ]* 8.9 Write property test for transaction detail field completeness
    - **Property 7: Transaction Detail Field Completeness**
    - **Validates: Requirements 3.2**

  - [ ] 8.10 Implement SearchBar for transactions
    - Search by farmer name, buyer name, or transaction ID
    - Debounce search input (300ms)
    - Display search results in real-time
    - _Requirements: 3.6_

  - [ ]* 8.11 Write property test for search result correctness
    - **Property 11: Search Result Correctness**
    - **Validates: Requirements 3.6, 4.6**

  - [ ] 8.12 Implement DisputeManager component
    - Display list of disputes with status indicators
    - Show dispute details (parties, issue, status, notes)
    - Allow adding notes to disputes
    - Allow marking disputes as resolved with resolution summary
    - _Requirements: 3.5, 6.3, 6.4, 6.5_

  - [ ]* 8.13 Write property test for dispute visibility
    - **Property 10: Dispute Visibility**
    - **Validates: Requirements 3.5**

  - [ ]* 8.14 Write property test for dispute note addition
    - **Property 19: Dispute Note Addition**
    - **Validates: Requirements 6.4**

  - [ ]* 8.15 Write property test for dispute resolution state update
    - **Property 20: Dispute Resolution State Update**
    - **Validates: Requirements 6.5**

- [ ] 9. Checkpoint - Ensure transaction monitoring works
  - Verify transactions load and display correctly
  - Verify filtering and searching work correctly
  - Verify delayed payments are flagged
  - Verify dispute management works end-to-end
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 10. Farmer Portfolio Module
  - [ ] 10.1 Create Farmer, Plot, and NDVIReading types
    - Define Farmer interface (id, name, phoneNumber, village, fpoId, creditReadiness, plots, createdAt, updatedAt)
    - Define Plot interface (id, farmerId, plotNumber, cropType, areaInAcres, boundaryData, ndviData)
    - Define NDVIReading interface (date, value, source)
    - _Requirements: 4.2_

  - [ ] 10.2 Create API integration for farmers
    - Implement fetchFarmers for farmer list
    - Implement fetchFarmerById for farmer detail
    - Implement fetchFarmerTransactionHistory with 12-month filter
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ] 10.3 Implement FarmerList component
    - Display farmers in DataTable with sorting and pagination
    - Show farmer summary: name, village, plot count, credit readiness
    - Implement search by name, phone number, or village
    - _Requirements: 4.1, 4.6_

  - [ ]* 10.4 Write property test for farmer list completeness
    - **Property 12: Farmer List Completeness**
    - **Validates: Requirements 4.1**

  - [ ] 10.5 Implement FarmerProfile component
    - Display all farmer fields (name, contact, village, credit readiness)
    - Show list of plots with crop types and areas
    - Display transaction history for past 12 months
    - Provide navigation to transaction details
    - _Requirements: 4.2, 4.3_

  - [ ]* 10.6 Write property test for farmer profile field completeness
    - **Property 13: Farmer Profile Field Completeness**
    - **Validates: Requirements 4.2**

  - [ ]* 10.7 Write property test for farmer transaction history date filtering
    - **Property 14: Farmer Transaction History Date Filtering**
    - **Validates: Requirements 4.3**

  - [ ] 10.8 Implement PlotMap component with Mapbox GL JS
    - Initialize Mapbox map with appropriate zoom and center
    - Render plot boundaries as polygons when boundaryData is available
    - Display plot information on hover (plot number, crop type, area)
    - Handle missing boundaryData gracefully (show text info instead)
    - _Requirements: 4.4, 4.5_

  - [ ]* 10.9 Write property test for graceful degradation with missing data
    - **Property 15: Graceful Degradation for Missing Data**
    - **Validates: Requirements 4.4, 4.5, 5.3, 7.4, 12.3**

  - [ ]* 10.10 Write unit tests for farmer portfolio
    - Test farmer list rendering and search
    - Test farmer profile display
    - Test plot map rendering with and without boundary data
    - Test transaction history filtering

- [ ] 11. Payment Tracking Module
  - [ ] 11.1 Create Payment and PaymentMetrics types
    - Define Payment interface (id, transactionId, farmerId, farmerName, amount, dueDate, completedDate, status, paymentMethod, upiTransactionId)
    - Define PaymentMetrics interface (totalPayments, completedPayments, delayedPayments, successRate, averagePaymentTimeHours)
    - _Requirements: 6.1, 6.6_

  - [ ] 11.2 Create API integration for payments
    - Implement fetchPendingPayments
    - Implement fetchPaymentMetrics
    - _Requirements: 6.1, 6.6_

  - [ ] 11.3 Implement PaymentTracker component
    - Display list of pending payments with due dates
    - Flag payments delayed beyond 48 hours with high-priority indicator
    - Show payment method and transaction IDs
    - Sort by due date (earliest first)
    - _Requirements: 6.1, 6.2_

  - [ ] 11.4 Implement PaymentMetrics component
    - Display payment success rate as percentage
    - Display average payment time in hours/days
    - Show total, completed, and delayed payment counts
    - Visualize metrics with charts (Recharts)
    - _Requirements: 6.6_

  - [ ]* 11.5 Write property test for payment metrics calculation
    - **Property 18: Payment Metrics Calculation**
    - **Validates: Requirements 6.6**

  - [ ]* 11.6 Write unit tests for payment tracking
    - Test pending payment display
    - Test delayed payment flagging
    - Test metrics calculation and display

- [ ] 12. Market Intelligence Module
  - [ ] 12.1 Create market data types
    - Define MandiPrice interface (cropType, mandiName, pricePerQuintal, date, source)
    - Define SurplusAlert interface (id, cropType, estimatedSurplus, affectedFarmers, recommendedAction, createdAt)
    - Define ProcessorCapacity interface (processorId, processorName, cropTypes, currentCapacity, maxCapacity, availabilityStatus)
    - _Requirements: 5.1, 5.4, 5.5_

  - [ ] 12.2 Create API integration for market intelligence
    - Implement fetchMandiPrices with date range (default: last 30 days)
    - Implement fetchNDVITrends for FPO plots
    - Implement fetchSurplusAlerts
    - Implement fetchProcessorCapacity
    - Configure automatic refresh every 5 minutes
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ] 12.3 Implement MandiPriceChart component
    - Display price trends as line chart (Recharts)
    - Show prices for last 30 days by default
    - Support filtering by crop type
    - Display current price and price change percentage
    - _Requirements: 5.1, 5.2_

  - [ ]* 12.4 Write property test for market data visualization completeness
    - **Property 16: Market Data Visualization Completeness**
    - **Validates: Requirements 5.1, 5.2, 5.5**

  - [ ] 12.5 Implement NDVITrendChart component
    - Display NDVI trends as line chart
    - Show crop health status (healthy, moderate, poor) based on NDVI values
    - Handle missing NDVI data gracefully
    - _Requirements: 5.3_

  - [ ] 12.6 Implement SurplusAlerts component
    - Display surplus alerts prominently with alert styling
    - Show crop type, estimated surplus, affected farmers, recommended action
    - Sort by creation date (newest first)
    - _Requirements: 5.4_

  - [ ]* 12.7 Write property test for alert display completeness
    - **Property 17: Alert Display Completeness**
    - **Validates: Requirements 5.4, 8.1, 8.2**

  - [ ] 12.8 Implement ProcessingCapacity component
    - Display processor capacity as progress bars or gauges
    - Show processor name, crop types, current/max capacity, availability status
    - Use color coding for availability (green: available, yellow: limited, red: full)
    - _Requirements: 5.5_

  - [ ]* 12.9 Write unit tests for market intelligence
    - Test mandi price chart rendering
    - Test NDVI trend chart with and without data
    - Test surplus alert display
    - Test processor capacity visualization

- [ ] 13. Checkpoint - Ensure market intelligence works
  - Verify mandi prices load and display correctly
  - Verify NDVI trends display when available
  - Verify surplus alerts are prominent
  - Verify processor capacity displays correctly
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 14. Harvest Calendar Module
  - [ ] 14.1 Create Harvest type
    - Define Harvest interface (id, farmerId, farmerName, plotId, cropType, areaInAcres, expectedHarvestDate, estimatedYield, status, gameTheoryRecommendation)
    - _Requirements: 7.2_

  - [ ] 14.2 Create API integration for harvests
    - Implement fetchUpcomingHarvests with 60-day filter
    - Implement updateHarvestStatus mutation
    - _Requirements: 7.1, 7.5_

  - [ ] 14.3 Implement HarvestCalendar component
    - Display harvests in calendar view (month grid)
    - Show harvest count per day
    - Allow clicking on day to see harvest details
    - Filter to show only harvests within next 60 days
    - _Requirements: 7.1_

  - [ ]* 14.4 Write property test for harvest calendar date filtering
    - **Property 21: Harvest Calendar Date Filtering**
    - **Validates: Requirements 7.1**

  - [ ] 14.5 Implement HarvestList component
    - Display harvests in list view with sorting
    - Show farmer name, crop type, plot size, expected date, status
    - Display game theory recommendations when available
    - Allow filtering by crop type, village, date range
    - _Requirements: 7.2, 7.3, 7.4_

  - [ ]* 14.6 Write property test for harvest information field completeness
    - **Property 22: Harvest Information Field Completeness**
    - **Validates: Requirements 7.2**

  - [ ]* 14.7 Write property test for harvest calendar filtering correctness
    - **Property 23: Harvest Calendar Filtering Correctness**
    - **Validates: Requirements 7.3**

  - [ ] 14.8 Implement harvest status update functionality
    - Add action buttons to mark harvest as completed or delayed
    - Update harvest status via API mutation
    - Show success/error feedback
    - Refresh harvest list after update
    - _Requirements: 7.5_

  - [ ]* 14.9 Write property test for harvest status update
    - **Property 24: Harvest Status Update**
    - **Validates: Requirements 7.5**

  - [ ] 14.10 Implement harvest notifications
    - Generate notifications for harvests within next 7 days
    - Display notification count in UI
    - Show notification list with harvest details
    - _Requirements: 7.6_

  - [ ]* 14.11 Write property test for harvest notification generation
    - **Property 25: Harvest Notification Generation**
    - **Validates: Requirements 7.6**

  - [ ]* 14.12 Write unit tests for harvest calendar
    - Test calendar view rendering
    - Test list view filtering
    - Test status update flow
    - Test notification generation

- [ ] 15. Insurance and Scheme Alerts Module
  - [ ] 15.1 Create Alert type
    - Define Alert interface (id, type, priority, farmerId, farmerName, title, description, actionRequired, deadline, status, createdAt, resolvedAt)
    - _Requirements: 8.1, 8.2_

  - [ ] 15.2 Create API integration for alerts
    - Implement fetchAlerts with 12-month retention filter
    - Implement resolveAlert mutation
    - _Requirements: 8.4, 8.6_

  - [ ] 15.3 Implement AlertList component
    - Display alerts in prioritized list (high → medium → low)
    - Show alert type icon, title, farmer name, priority badge
    - Filter alerts by priority and type
    - Display unresolved alert count prominently
    - _Requirements: 8.1, 8.2, 8.3, 8.5_

  - [ ]* 15.4 Write property test for alert filtering correctness
    - **Property 26: Alert Filtering Correctness**
    - **Validates: Requirements 8.3**

  - [ ]* 15.5 Write property test for unresolved alert count
    - **Property 28: Unresolved Alert Count**
    - **Validates: Requirements 8.5**

  - [ ] 15.6 Implement AlertDetail component
    - Display full alert information (type, priority, farmer, description, action required, deadline)
    - Show alert status and timestamps
    - Provide "Mark as Resolved" button
    - _Requirements: 8.1, 8.2, 8.4_

  - [ ]* 15.7 Write property test for alert resolution state update
    - **Property 27: Alert Resolution State Update**
    - **Validates: Requirements 8.4**

  - [ ]* 15.8 Write property test for alert history retention
    - **Property 29: Alert History Retention**
    - **Validates: Requirements 8.6**

  - [ ]* 15.9 Write unit tests for alerts module
    - Test alert list rendering and filtering
    - Test alert detail display
    - Test alert resolution flow
    - Test unresolved count calculation

- [ ] 16. Analytics and Reporting Module
  - [ ] 16.1 Create analytics types
    - Define FPOMetrics interface (totalFarmers, activeFarmers, totalTransactions, totalRevenue, averageFarmerIncome, computedAt)
    - Define IncomeData interface (month, averageIncome, totalIncome, farmerCount)
    - Define ReliabilityScore interface (entityId, entityName, entityType, paymentTimeliness, transactionSuccessRate, overallScore, transactionCount)
    - _Requirements: 9.1, 9.2, 9.3_

  - [ ] 16.2 Create API integration for analytics
    - Implement fetchFPOMetrics (computed daily)
    - Implement fetchIncomeData with 12-month filter
    - Implement fetchReliabilityScores
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [ ] 16.3 Implement AnalyticsDashboard component
    - Display FPO metrics in card layout (total farmers, transactions, revenue)
    - Show key performance indicators with trend indicators
    - Display last computed timestamp
    - _Requirements: 9.1, 9.4_

  - [ ]* 16.4 Write property test for FPO metrics calculation
    - **Property 30: FPO Metrics Calculation**
    - **Validates: Requirements 9.1**

  - [ ] 16.5 Implement IncomeChart component
    - Display farmer income trends as bar or line chart (Recharts)
    - Show data for past 12 months
    - Display average income and total income
    - Support year-over-year comparison
    - _Requirements: 9.2, 9.6_

  - [ ]* 16.6 Write property test for income trend date range
    - **Property 31: Income Trend Date Range**
    - **Validates: Requirements 9.2**

  - [ ]* 16.7 Write property test for year-over-year comparison calculation
    - **Property 34: Year-Over-Year Comparison Calculation**
    - **Validates: Requirements 9.6**

  - [ ] 16.8 Implement ReliabilityScores component
    - Display buyer and processor reliability scores in table
    - Show payment timeliness, transaction success rate, overall score
    - Sort by overall score (highest first)
    - Use color coding for score ranges (green: >80, yellow: 60-80, red: <60)
    - _Requirements: 9.3_

  - [ ]* 16.9 Write property test for reliability score calculation
    - **Property 32: Reliability Score Calculation**
    - **Validates: Requirements 9.3**

  - [ ] 16.10 Implement ReportExporter component
    - Add export buttons for CSV and PDF formats
    - Generate CSV with proper formatting (headers, data rows)
    - Generate PDF with charts and tables
    - Trigger file download on export
    - _Requirements: 9.5_

  - [ ]* 16.11 Write property test for analytics export format correctness
    - **Property 33: Analytics Export Format Correctness**
    - **Validates: Requirements 9.5**

  - [ ]* 16.12 Write unit tests for analytics module
    - Test metrics display
    - Test income chart rendering
    - Test reliability scores display
    - Test CSV and PDF export

- [ ] 17. Checkpoint - Ensure all feature modules work
  - Verify harvest calendar displays and updates correctly
  - Verify alerts display and resolve correctly
  - Verify analytics display and export correctly
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 18. Dashboard Layout and Navigation
  - [ ] 18.1 Implement main layout component
    - Create AppLayout with header, sidebar, and main content area
    - Implement responsive sidebar (collapsible on tablet)
    - Add navigation menu with links to all feature modules
    - Display FPO coordinator name and logout button in header
    - _Requirements: 11.1, 11.2_

  - [ ] 18.2 Implement routing with React Router
    - Set up routes for all feature modules (activity stream, transactions, farmers, market intelligence, payments, harvests, alerts, analytics)
    - Implement protected routes with authentication guard
    - Add 404 page for unknown routes
    - Implement navigation state management (active module)
    - _Requirements: 1.5_

  - [ ] 18.3 Implement dashboard home page
    - Display overview cards with key metrics (unresolved alerts, pending payments, upcoming harvests)
    - Show recent activity stream (last 10 events)
    - Display quick links to feature modules
    - _Requirements: 8.5_

  - [ ] 18.4 Implement notification system
    - Display notification count badge in header
    - Show notification dropdown with recent notifications
    - Support notification types (info, success, warning, error)
    - Allow marking notifications as read
    - _Requirements: 7.6_

  - [ ]* 18.5 Write unit tests for layout and navigation
    - Test sidebar navigation
    - Test route protection
    - Test notification display
    - Test responsive behavior

- [ ] 19. Accessibility Implementation
  - [ ] 19.1 Implement keyboard navigation
    - Ensure all interactive elements are keyboard accessible (Tab, Enter, Arrow keys)
    - Add visible focus indicators for all focusable elements
    - Implement keyboard shortcuts for common actions (e.g., Ctrl+K for search)
    - Test tab order for logical navigation flow
    - _Requirements: 11.4_

  - [ ]* 19.2 Write property test for keyboard navigation support
    - **Property 37: Keyboard Navigation Support**
    - **Validates: Requirements 11.4**

  - [ ] 19.3 Add ARIA attributes
    - Add ARIA labels to buttons, links, and form inputs
    - Add ARIA roles to custom components (e.g., role="navigation" for sidebar)
    - Add ARIA live regions for dynamic content (activity stream, notifications)
    - Add ARIA descriptions for complex interactions
    - _Requirements: 11.4_

  - [ ] 19.4 Implement text alternatives for visualizations
    - Add alt text to all images
    - Add ARIA labels to charts describing the data
    - Provide data tables as alternatives to charts
    - Add screen reader announcements for data updates
    - _Requirements: 11.5_

  - [ ]* 19.5 Write property test for data visualization text alternatives
    - **Property 38: Data Visualization Text Alternatives**
    - **Validates: Requirements 11.5**

  - [ ] 19.6 Verify color contrast
    - Ensure all text meets WCAG AA contrast ratios (4.5:1 for normal text, 3:1 for large text)
    - Test with color contrast checker tools
    - Adjust colors if needed to meet standards
    - _Requirements: 11.4_

  - [ ]* 19.7 Run accessibility tests with axe-core
    - Test all pages with axe-core
    - Fix any accessibility violations
    - Document any exceptions or limitations

- [ ] 20. Error Handling and Resilience
  - [ ] 20.1 Implement cached data fallback
    - When API requests fail, display cached data with staleness indicator
    - Show "Last updated: X minutes ago" timestamp
    - Provide manual refresh button
    - _Requirements: 12.4_

  - [ ]* 20.2 Write property test for cached data fallback
    - **Property 40: Cached Data Fallback**
    - **Validates: Requirements 12.4**

  - [ ] 20.3 Implement WebSocket fallback to polling
    - Detect repeated WebSocket connection failures (3+ failures in 5 minutes)
    - Fall back to polling activity updates every 10 seconds
    - Display connection mode indicator (WebSocket vs Polling)
    - Attempt to reconnect to WebSocket periodically
    - _Requirements: 12.2_

  - [ ] 20.4 Implement last update timestamp display
    - Add "Last updated" timestamp to all data sections
    - Update timestamp on successful data fetch
    - Use relative time format (e.g., "Updated 2 minutes ago")
    - _Requirements: 13.6_

  - [ ]* 20.5 Write property test for last update timestamp display
    - **Property 43: Last Update Timestamp Display**
    - **Validates: Requirements 13.6**

  - [ ]* 20.6 Write unit tests for error handling
    - Test API error display and retry
    - Test cached data fallback
    - Test WebSocket fallback to polling
    - Test timeout handling

- [ ] 21. Performance Optimization
  - [ ] 21.1 Implement code splitting
    - Use React.lazy() for feature modules
    - Implement route-based code splitting
    - Add loading fallbacks for lazy-loaded components
    - _Requirements: 10.1_

  - [ ] 21.2 Implement component memoization
    - Use React.memo() for expensive components (charts, maps, large lists)
    - Use useMemo() for expensive calculations
    - Use useCallback() for event handlers passed to child components
    - _Requirements: 10.1_

  - [ ] 21.3 Implement virtual scrolling for large lists
    - Use react-window for activity stream (100+ events)
    - Use react-window for transaction list (100+ transactions)
    - Use react-window for farmer list (500+ farmers)
    - _Requirements: 10.4_

  - [ ] 21.4 Optimize images and assets
    - Compress images and use WebP format
    - Implement lazy loading for images
    - Use responsive images with srcset
    - _Requirements: 10.1_

  - [ ] 21.5 Configure build optimization
    - Enable Vite build optimizations (minification, tree shaking)
    - Configure code splitting for optimal chunk sizes
    - Implement cache-busting with content hashes in filenames
    - _Requirements: 15.5_

  - [ ]* 21.6 Run Lighthouse performance audit
    - Test dashboard load time on simulated 4G connection
    - Verify load time is under 3 seconds
    - Fix any performance issues identified

- [ ] 22. Responsive Design Implementation
  - [ ] 22.1 Implement tablet layout (768px+)
    - Adjust sidebar to collapsible drawer on tablet
    - Optimize table layouts for tablet width
    - Adjust chart sizes for tablet screens
    - Test all pages on tablet viewport
    - _Requirements: 11.1_

  - [ ] 22.2 Implement desktop layout (1024px+)
    - Use full-width sidebar on desktop
    - Optimize multi-column layouts for desktop
    - Maximize chart and table sizes for desktop screens
    - Test all pages on desktop viewport
    - _Requirements: 11.2_

  - [ ]* 22.3 Write unit tests for responsive rendering
    - Test component rendering at tablet width (768px)
    - Test component rendering at desktop width (1024px)
    - Verify no layout breaks at different viewports

- [ ] 23. Integration Testing
  - [ ]* 23.1 Write integration tests for authentication flow
    - Test login with valid credentials
    - Test login with invalid credentials
    - Test session expiration and redirect
    - Test token refresh on 401 errors

  - [ ]* 23.2 Write integration tests for activity stream
    - Test WebSocket connection and message handling
    - Test activity event display and filtering
    - Test fallback to polling on WebSocket failure

  - [ ]* 23.3 Write integration tests for transaction monitoring
    - Test transaction list loading and filtering
    - Test transaction search
    - Test dispute management workflow

  - [ ]* 23.4 Write integration tests for farmer portfolio
    - Test farmer list loading and search
    - Test farmer profile display
    - Test plot map rendering with and without boundary data

  - [ ]* 23.5 Write integration tests for analytics
    - Test metrics calculation and display
    - Test chart rendering
    - Test CSV and PDF export

- [ ] 24. End-to-End Testing with Playwright
  - [ ]* 24.1 Write E2E test for authentication flow
    - Test FPO coordinator login
    - Test session management
    - Test logout

  - [ ]* 24.2 Write E2E test for activity stream workflow
    - Test activity stream loads and displays events
    - Test filtering by agent type and farmer
    - Test real-time updates (mock WebSocket)

  - [ ]* 24.3 Write E2E test for transaction monitoring workflow
    - Test transaction list loads
    - Test filtering and searching
    - Test viewing transaction details
    - Test dispute management

  - [ ]* 24.4 Write E2E test for farmer portfolio workflow
    - Test farmer list loads
    - Test searching for farmer
    - Test viewing farmer profile
    - Test viewing transaction history

  - [ ]* 24.5 Write E2E test for analytics workflow
    - Test analytics dashboard loads
    - Test viewing charts and metrics
    - Test exporting data as CSV

  - [ ]* 24.6 Write E2E test for error scenarios
    - Test network failure handling
    - Test API error handling
    - Test cached data fallback

- [ ] 25. Deployment Configuration
  - [ ] 25.1 Configure AWS S3 bucket for static hosting
    - Create S3 bucket with appropriate name
    - Enable static website hosting
    - Configure bucket policy for public read access
    - Set up CORS configuration for API requests
    - _Requirements: 15.1_

  - [ ] 25.2 Configure AWS CloudFront distribution
    - Create CloudFront distribution pointing to S3 bucket
    - Configure custom domain and SSL certificate
    - Set up cache behaviors for static assets (long cache) and HTML (short cache)
    - Configure CloudFront to route /api/* requests to API Gateway
    - Enable HTTPS only (redirect HTTP to HTTPS)
    - _Requirements: 15.2, 15.3, 15.4, 15.6_

  - [ ] 25.3 Create deployment script
    - Write script to build production bundle
    - Upload build artifacts to S3
    - Invalidate CloudFront cache for updated files
    - Verify deployment success
    - _Requirements: 15.1, 15.5_

  - [ ] 25.4 Set up CI/CD pipeline
    - Configure GitHub Actions or similar for automated deployment
    - Run tests before deployment
    - Deploy to staging environment first
    - Deploy to production after manual approval
    - _Requirements: 15.1_

- [ ] 26. Final Checkpoint - End-to-End Verification
  - Run full test suite (unit, property, integration, E2E)
  - Verify all 47 correctness properties pass
  - Test dashboard on tablet and desktop devices
  - Test with real backend API (if available) or comprehensive mocks
  - Verify performance meets requirements (load time <3s on 4G)
  - Verify accessibility with screen reader
  - Deploy to staging environment and perform manual testing
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each property test references a specific correctness property from the design document
- Checkpoints ensure incremental validation and early error detection
- Property tests use fast-check with minimum 100 iterations per test
- Integration tests use MSW (Mock Service Worker) for API mocking
- E2E tests use Playwright for cross-browser testing
- All tests should pass before proceeding to deployment
