# Design Document: FPO Dashboard

## Overview

The FPO Dashboard is a React-based single-page application (SPA) that provides FPO coordinators with comprehensive operational oversight of the Anna Drishti platform. The application follows a modern React architecture using TypeScript for type safety, React Query for server state management, Zustand for client state, and shadcn/ui components for a consistent UI.

The dashboard integrates with multiple backend services via REST APIs and maintains a persistent WebSocket connection for real-time activity updates. It is deployed as a static site on AWS S3 with CloudFront for global CDN distribution and HTTPS termination.

### Key Design Principles

1. **Progressive Enhancement**: Core functionality works without WebSocket; real-time updates enhance the experience
2. **Graceful Degradation**: Missing data (e.g., plot boundaries) doesn't break the UI
3. **Performance First**: Lazy loading, code splitting, and aggressive caching for fast load times
4. **Accessibility**: WCAG 2.1 AA compliance where feasible, keyboard navigation, screen reader support
5. **Mobile-Responsive**: Tablet and desktop optimized (not phone-optimized)
6. **Type Safety**: Full TypeScript coverage for compile-time error detection

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FPO Dashboard (React SPA)                │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Auth       │  │  Activity    │  │ Transaction  │      │
│  │   Module     │  │  Stream      │  │  Monitor     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Farmer     │  │   Market     │  │  Analytics   │      │
│  │  Portfolio   │  │ Intelligence │  │   Module     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         State Management Layer                       │    │
│  │  ┌──────────────┐         ┌──────────────┐         │    │
│  │  │ React Query  │         │   Zustand    │         │    │
│  │  │(Server State)│         │(Client State)│         │    │
│  │  └──────────────┘         └──────────────┘         │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         API Integration Layer                        │    │
│  │  ┌──────────────┐         ┌──────────────┐         │    │
│  │  │  REST API    │         │  WebSocket   │         │    │
│  │  │   Client     │         │   Client     │         │    │
│  │  └──────────────┘         └──────────────┘         │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    AWS Infrastructure                        │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  CloudFront  │  │  API Gateway │  │  API Gateway │      │
│  │     (CDN)    │  │   (REST)     │  │  (WebSocket) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                 │                   │              │
│         ▼                 ▼                   ▼              │
│  ┌──────────────┐  ┌──────────────────────────────────┐    │
│  │      S3      │  │   Backend Foundation & Data Layer│    │
│  │ (Static Site)│  │   (Farmer, Transaction, Agent    │    │
│  └──────────────┘  │    Activity APIs)                │    │
│                     └──────────────────────────────────┘    │
│                                                               │
│  ┌──────────────┐                                            │
│  │   Cognito    │                                            │
│  │    (Auth)    │                                            │
│  └──────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

### Component Architecture

The application follows a feature-based folder structure with shared components:

```
src/
├── features/
│   ├── auth/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── services/
│   ├── activity-stream/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── types/
│   ├── transactions/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── types/
│   ├── farmers/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── types/
│   ├── market-intelligence/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── types/
│   ├── analytics/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── types/
│   └── harvest-calendar/
│       ├── components/
│       ├── hooks/
│       └── types/
├── shared/
│   ├── components/
│   ├── hooks/
│   ├── utils/
│   └── types/
├── services/
│   ├── api/
│   │   ├── rest-client.ts
│   │   └── websocket-client.ts
│   └── auth/
│       └── cognito-auth.ts
└── stores/
    └── ui-store.ts
```

## Components and Interfaces

### Core Components

#### 1. Authentication Module

**Purpose**: Handle AWS Cognito authentication and session management

**Components**:
- `LoginPage`: Cognito-hosted UI integration
- `AuthProvider`: React context for auth state
- `ProtectedRoute`: Route guard for authenticated pages

**Key Interfaces**:

```typescript
interface AuthState {
  user: CognitoUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

interface AuthService {
  login(): Promise<void>;
  logout(): Promise<void>;
  refreshToken(): Promise<string>;
  getAccessToken(): Promise<string>;
}
```

#### 2. Activity Stream Module

**Purpose**: Display real-time agent activity feed via WebSocket

**Components**:
- `ActivityStream`: Main container with WebSocket connection
- `ActivityCard`: Individual activity event display
- `ActivityFilters`: Filter by agent type, farmer, time range

**Key Interfaces**:

```typescript
interface ActivityEvent {
  id: string;
  timestamp: string;
  agentType: 'sell' | 'process';
  farmerId: string;
  farmerName: string;
  actionType: string;
  actionSummary: string;
  metadata: Record<string, unknown>;
}

interface WebSocketClient {
  connect(url: string, token: string): void;
  disconnect(): void;
  onMessage(handler: (event: ActivityEvent) => void): void;
  onError(handler: (error: Error) => void): void;
  onReconnect(handler: () => void): void;
}
```

#### 3. Transaction Monitor Module

**Purpose**: Track sales, processing, payments, and disputes

**Components**:
- `TransactionList`: Paginated transaction table
- `TransactionDetail`: Detailed transaction view
- `TransactionFilters`: Filter by status, farmer, buyer, date
- `DisputeManager`: Dispute tracking and resolution

**Key Interfaces**:

```typescript
interface Transaction {
  id: string;
  type: 'sale' | 'processing';
  farmerId: string;
  farmerName: string;
  buyerOrProcessorId: string;
  buyerOrProcessorName: string;
  cropType: string;
  quantity: number;
  pricePerUnit: number;
  totalAmount: number;
  paymentStatus: 'pending' | 'completed' | 'delayed' | 'disputed';
  paymentDueDate: string;
  paymentCompletedDate?: string;
  createdAt: string;
  updatedAt: string;
}

interface Dispute {
  id: string;
  transactionId: string;
  farmerId: string;
  farmerName: string;
  issueType: string;
  issueDescription: string;
  status: 'open' | 'in_progress' | 'resolved';
  notes: DisputeNote[];
  createdAt: string;
  resolvedAt?: string;
  resolutionSummary?: string;
}

interface DisputeNote {
  id: string;
  authorId: string;
  authorName: string;
  content: string;
  createdAt: string;
}
```

#### 4. Farmer Portfolio Module

**Purpose**: View farmer profiles, plots, and transaction history

**Components**:
- `FarmerList`: Searchable farmer directory
- `FarmerProfile`: Detailed farmer information
- `PlotMap`: Mapbox GL JS visualization of plot boundaries
- `TransactionHistory`: Farmer-specific transaction timeline

**Key Interfaces**:

```typescript
interface Farmer {
  id: string;
  name: string;
  phoneNumber: string;
  village: string;
  fpoId: string;
  creditReadiness: 'ready' | 'not_ready' | 'pending_review';
  plots: Plot[];
  createdAt: string;
  updatedAt: string;
}

interface Plot {
  id: string;
  farmerId: string;
  plotNumber: string;
  cropType: string;
  areaInAcres: number;
  boundaryData?: GeoJSON.Polygon;
  ndviData?: NDVIReading[];
}

interface NDVIReading {
  date: string;
  value: number;
  source: string;
}
```

#### 5. Market Intelligence Module

**Purpose**: Visualize mandi prices, NDVI trends, and processing capacity

**Components**:
- `MandiPriceChart`: Line chart of price trends (Recharts)
- `NDVITrendChart`: Crop health visualization
- `SurplusAlerts`: Surplus detection notifications
- `ProcessingCapacity`: Processor availability dashboard

**Key Interfaces**:

```typescript
interface MandiPrice {
  cropType: string;
  mandiName: string;
  pricePerQuintal: number;
  date: string;
  source: string;
}

interface SurplusAlert {
  id: string;
  cropType: string;
  estimatedSurplus: number;
  affectedFarmers: number;
  recommendedAction: string;
  createdAt: string;
}

interface ProcessorCapacity {
  processorId: string;
  processorName: string;
  cropTypes: string[];
  currentCapacity: number;
  maxCapacity: number;
  availabilityStatus: 'available' | 'limited' | 'full';
}
```

#### 6. Payment Tracking Module

**Purpose**: Monitor payment status and flag delays

**Components**:
- `PaymentTracker`: List of pending payments
- `PaymentMetrics`: Success rate and average time charts
- `DelayedPaymentAlerts`: High-priority payment delays

**Key Interfaces**:

```typescript
interface Payment {
  id: string;
  transactionId: string;
  farmerId: string;
  farmerName: string;
  amount: number;
  dueDate: string;
  completedDate?: string;
  status: 'pending' | 'completed' | 'delayed';
  paymentMethod: 'upi' | 'bank_transfer' | 'cash';
  upiTransactionId?: string;
}

interface PaymentMetrics {
  totalPayments: number;
  completedPayments: number;
  delayedPayments: number;
  successRate: number;
  averagePaymentTimeHours: number;
}
```

#### 7. Harvest Calendar Module

**Purpose**: View upcoming harvests and coordinate aggregation

**Components**:
- `HarvestCalendar`: Calendar view of upcoming harvests
- `HarvestList`: List view with filtering
- `AggregationRecommendations`: Game theory suggestions

**Key Interfaces**:

```typescript
interface Harvest {
  id: string;
  farmerId: string;
  farmerName: string;
  plotId: string;
  cropType: string;
  areaInAcres: number;
  expectedHarvestDate: string;
  estimatedYield: number;
  status: 'upcoming' | 'in_progress' | 'completed' | 'delayed';
  gameTheoryRecommendation?: string;
}
```

#### 8. Insurance and Scheme Alerts Module

**Purpose**: Surface crop distress and scheme eligibility notifications

**Components**:
- `AlertList`: Prioritized alert feed
- `AlertDetail`: Detailed alert information
- `AlertFilters`: Filter by type and priority

**Key Interfaces**:

```typescript
interface Alert {
  id: string;
  type: 'crop_distress' | 'scheme_eligibility' | 'other';
  priority: 'high' | 'medium' | 'low';
  farmerId: string;
  farmerName: string;
  title: string;
  description: string;
  actionRequired: string;
  deadline?: string;
  status: 'unresolved' | 'in_progress' | 'resolved';
  createdAt: string;
  resolvedAt?: string;
}
```

#### 9. Analytics Module

**Purpose**: Display FPO performance metrics and trends

**Components**:
- `AnalyticsDashboard`: Overview of key metrics
- `IncomeChart`: Farmer income trends (Recharts)
- `ReliabilityScores`: Buyer/processor reliability ratings
- `ReportExporter`: CSV/PDF export functionality

**Key Interfaces**:

```typescript
interface FPOMetrics {
  totalFarmers: number;
  activeFarmers: number;
  totalTransactions: number;
  totalRevenue: number;
  averageFarmerIncome: number;
  computedAt: string;
}

interface IncomeData {
  month: string;
  averageIncome: number;
  totalIncome: number;
  farmerCount: number;
}

interface ReliabilityScore {
  entityId: string;
  entityName: string;
  entityType: 'buyer' | 'processor';
  paymentTimeliness: number;
  transactionSuccessRate: number;
  overallScore: number;
  transactionCount: number;
}
```

### Shared Components

#### UI Components (shadcn/ui)

- `Button`, `Input`, `Select`, `Checkbox`, `Radio`
- `Card`, `Table`, `Dialog`, `Sheet`, `Tabs`
- `Alert`, `Badge`, `Skeleton`, `Spinner`
- `Dropdown`, `Popover`, `Tooltip`

#### Custom Shared Components

- `DataTable`: Reusable table with sorting, filtering, pagination
- `SearchBar`: Debounced search input
- `DateRangePicker`: Date range selection
- `ErrorBoundary`: Error handling wrapper
- `LoadingState`: Consistent loading indicators
- `EmptyState`: Consistent empty state messaging

## Data Models

### API Response Models

All API responses follow a consistent envelope format:

```typescript
interface APIResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
  metadata?: {
    page?: number;
    pageSize?: number;
    totalCount?: number;
    timestamp: string;
  };
}
```

### WebSocket Message Models

```typescript
interface WebSocketMessage {
  type: 'activity_event' | 'ping' | 'error';
  payload: ActivityEvent | PingPayload | ErrorPayload;
  timestamp: string;
}

interface PingPayload {
  message: string;
}

interface ErrorPayload {
  code: string;
  message: string;
}
```

### Client State Models

```typescript
interface UIState {
  sidebarOpen: boolean;
  activeModule: string;
  theme: 'light' | 'dark';
  notifications: Notification[];
}

interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  createdAt: string;
  read: boolean;
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Authentication Token Inclusion

*For any* API request made by the dashboard, the request headers should include a valid AWS Cognito authentication token.

**Validates: Requirements 14.1**

### Property 2: Invalid Credentials Rejection

*For any* invalid credential combination (wrong username, wrong password, malformed input), the authentication system should reject the login attempt and display an error message without granting access.

**Validates: Requirements 1.3**

### Property 3: Protected Route Access Control

*For any* protected route in the dashboard, attempting to access it without valid authentication should result in redirection to the login page.

**Validates: Requirements 1.5**

### Property 4: Activity Event Field Completeness

*For any* activity event displayed in the activity stream, the rendered output should contain all required fields: timestamp, agent type, farmer name, and action summary.

**Validates: Requirements 2.4**

### Property 5: Activity Stream Filtering Correctness

*For any* set of activity events and any filter criteria (agent type, farmer, or time range), all filtered results should match the specified criteria and no matching events should be excluded.

**Validates: Requirements 2.5**

### Property 6: Transaction Date Range Filtering

*For any* set of transactions with various dates, when viewing the transaction monitor, only transactions from the past 30 days should be displayed.

**Validates: Requirements 3.1**

### Property 7: Transaction Detail Field Completeness

*For any* transaction, when displayed in detail view, the rendered output should contain all required fields: farmer, buyer/processor, quantity, price, payment status, and timestamps.

**Validates: Requirements 3.2**

### Property 8: Multi-Dimensional Transaction Filtering

*For any* set of transactions and any combination of filter criteria (status, farmer, buyer, date range), all filtered results should match all specified criteria.

**Validates: Requirements 3.3**

### Property 9: Payment Delay Flagging

*For any* transaction where payment is delayed beyond 48 hours from the due date, the transaction should be flagged with a warning indicator.

**Validates: Requirements 3.4, 6.2**

### Property 10: Dispute Visibility

*For any* transaction with an escalated dispute, the dispute should appear in the dedicated disputes section with all required details.

**Validates: Requirements 3.5**

### Property 11: Search Result Correctness

*For any* searchable collection (transactions, farmers) and any search query, all results should match the query in at least one searchable field (name, phone, ID), and no matching items should be excluded.

**Validates: Requirements 3.6, 4.6**

### Property 12: Farmer List Completeness

*For any* set of farmers managed by the FPO, the farmer portfolio view should display all farmers without omission.

**Validates: Requirements 4.1**

### Property 13: Farmer Profile Field Completeness

*For any* farmer, when displayed in profile view, the rendered output should contain all required fields: name, contact, plot information, and credit readiness status.

**Validates: Requirements 4.2**

### Property 14: Farmer Transaction History Date Filtering

*For any* farmer with transaction history, the farmer detail view should display only transactions from the past 12 months.

**Validates: Requirements 4.3**

### Property 15: Graceful Degradation for Missing Data

*For any* data entity with optional fields (plot boundary data, NDVI data, game theory recommendations), the UI should render successfully without the optional data, displaying alternative representations or omitting optional sections without errors.

**Validates: Requirements 4.4, 4.5, 5.3, 7.4, 12.3**

### Property 16: Market Data Visualization Completeness

*For any* set of mandi prices, NDVI readings, or processor capacity data, the market intelligence dashboard should display all provided data points in the appropriate visualizations.

**Validates: Requirements 5.1, 5.2, 5.5**

### Property 17: Alert Display Completeness

*For any* surplus alert, crop distress alert, or scheme eligibility notification, the rendered output should contain all required fields specific to that alert type.

**Validates: Requirements 5.4, 8.1, 8.2**

### Property 18: Payment Metrics Calculation

*For any* set of payment records, the calculated payment success rate should equal (completed payments / total payments) and average payment time should equal the mean of (completed date - due date) for all completed payments.

**Validates: Requirements 6.6**

### Property 19: Dispute Note Addition

*For any* dispute, adding a note should result in the note appearing in the dispute's notes array with correct author, content, and timestamp.

**Validates: Requirements 6.4**

### Property 20: Dispute Resolution State Update

*For any* open dispute, marking it as resolved with a resolution summary should update the dispute status to "resolved", set the resolved timestamp, and store the resolution summary.

**Validates: Requirements 6.5**

### Property 21: Harvest Calendar Date Filtering

*For any* set of harvests with various expected dates, the harvest calendar should display only harvests with expected dates within the next 60 days from the current date.

**Validates: Requirements 7.1**

### Property 22: Harvest Information Field Completeness

*For any* harvest displayed in the calendar, the rendered output should contain all required fields: farmer name, crop type, plot size, and expected harvest date.

**Validates: Requirements 7.2**

### Property 23: Harvest Calendar Filtering Correctness

*For any* set of harvests and any filter criteria (crop type, village, date range), all filtered results should match the specified criteria.

**Validates: Requirements 7.3**

### Property 24: Harvest Status Update

*For any* harvest, marking it as completed or delayed should update the harvest status field to the specified value.

**Validates: Requirements 7.5**

### Property 25: Harvest Notification Generation

*For any* set of harvests, notifications should be generated for all and only those harvests with expected dates within the next 7 days.

**Validates: Requirements 7.6**

### Property 26: Alert Filtering Correctness

*For any* set of alerts and any filter criteria (priority, type), all filtered results should match the specified criteria.

**Validates: Requirements 8.3**

### Property 27: Alert Resolution State Update

*For any* unresolved alert, marking it as resolved should update the alert status to "resolved" and set the resolved timestamp.

**Validates: Requirements 8.4**

### Property 28: Unresolved Alert Count

*For any* set of alerts, the displayed unresolved alert count should equal the number of alerts with status "unresolved" or "in_progress".

**Validates: Requirements 8.5**

### Property 29: Alert History Retention

*For any* set of alerts with various creation dates, only alerts created within the past 12 months should be displayed or accessible.

**Validates: Requirements 8.6**

### Property 30: FPO Metrics Calculation

*For any* set of farmers, transactions, and revenue data, the displayed FPO metrics should correctly calculate: total farmers (count of farmers), total transactions (count of transactions), total revenue (sum of transaction amounts), and average farmer income (total revenue / total farmers).

**Validates: Requirements 9.1**

### Property 31: Income Trend Date Range

*For any* set of income data, the income trend chart should display data for the past 12 months only.

**Validates: Requirements 9.2**

### Property 32: Reliability Score Calculation

*For any* buyer or processor with transaction history, the reliability score should be calculated based on payment timeliness (percentage of on-time payments) and transaction success rate (percentage of completed transactions).

**Validates: Requirements 9.3**

### Property 33: Analytics Export Format Correctness

*For any* analytics data, exporting as CSV should produce valid CSV format with headers and data rows, and exporting as PDF should produce a valid PDF document.

**Validates: Requirements 9.5**

### Property 34: Year-Over-Year Comparison Calculation

*For any* metric with data spanning multiple years, the year-over-year comparison should correctly calculate the percentage change between the current year and previous year values.

**Validates: Requirements 9.6**

### Property 35: Pagination for Large Datasets

*For any* dataset exceeding 100 items, the UI should implement pagination or virtual scrolling, displaying a subset of items rather than rendering all items simultaneously.

**Validates: Requirements 10.4**

### Property 36: Data Caching Behavior

*For any* API endpoint marked as cacheable, making repeated requests for the same data should use cached data for subsequent requests within the cache validity period, reducing actual API calls.

**Validates: Requirements 10.5**

### Property 37: Keyboard Navigation Support

*For any* interactive element (buttons, links, form inputs, dropdowns), the element should be accessible via keyboard navigation (Tab, Enter, Arrow keys) and have appropriate focus indicators.

**Validates: Requirements 11.4**

### Property 38: Data Visualization Text Alternatives

*For any* chart or data visualization, the component should include text alternatives (ARIA labels, alt text, or data tables) describing the visualized information.

**Validates: Requirements 11.5**

### Property 39: API Error Handling

*For any* API request that fails with a network error or server error (5xx), the dashboard should display a clear error message and provide a retry mechanism.

**Validates: Requirements 12.1**

### Property 40: Cached Data Fallback

*For any* API request that fails when cached data is available, the dashboard should display the cached data with a staleness indicator rather than showing an empty state.

**Validates: Requirements 12.4**

### Property 41: API Timeout Handling

*For any* API request that exceeds the 10-second timeout threshold, the dashboard should abort the request, display a timeout error message, and provide a manual retry option.

**Validates: Requirements 12.5**

### Property 42: Client-Side Error Logging

*For any* JavaScript error, network error, or API error that occurs in the dashboard, the error should be logged with relevant context (error message, stack trace, user action, timestamp) for debugging purposes.

**Validates: Requirements 12.6**

### Property 43: Last Update Timestamp Display

*For any* data section in the dashboard (activity stream, transactions, market intelligence), the UI should display the timestamp of the last data update.

**Validates: Requirements 13.6**

### Property 44: API Endpoint Correctness

*For any* data fetch operation (farmers, transactions, analytics), the dashboard should call the correct Backend API REST endpoint with the correct HTTP method and request parameters.

**Validates: Requirements 14.2**

### Property 45: Token Refresh on 401 Unauthorized

*For any* API request that fails with 401 Unauthorized status, the dashboard should attempt to refresh the authentication token and retry the original request once.

**Validates: Requirements 14.4**

### Property 46: Exponential Backoff for Rate Limiting

*For any* API request that fails with 429 Too Many Requests status, the dashboard should implement exponential backoff, waiting progressively longer between retry attempts.

**Validates: Requirements 14.5**

### Property 47: API Response Schema Validation

*For any* API response received, the dashboard should validate the response structure against the expected schema before attempting to render the data, rejecting invalid responses.

**Validates: Requirements 14.6**

## Error Handling

### Error Categories

The dashboard handles four categories of errors:

1. **Authentication Errors**: Invalid credentials, expired sessions, token refresh failures
2. **Network Errors**: Connection failures, timeouts, DNS resolution failures
3. **API Errors**: 4xx client errors, 5xx server errors, rate limiting, invalid responses
4. **Client Errors**: JavaScript exceptions, rendering errors, state management errors

### Error Handling Strategies

#### Authentication Errors

- **Invalid Credentials**: Display user-friendly error message, allow retry
- **Expired Session**: Automatically redirect to login page, preserve intended destination
- **Token Refresh Failure**: Log out user, redirect to login page with error message

#### Network Errors

- **Connection Failure**: Display error message, attempt automatic reconnection with exponential backoff
- **Timeout**: Display timeout message, provide manual retry button
- **WebSocket Disconnection**: Automatically attempt reconnection, fall back to polling if reconnection fails repeatedly

#### API Errors

- **400 Bad Request**: Display validation error messages from API response
- **401 Unauthorized**: Attempt token refresh, retry request once, log out if refresh fails
- **403 Forbidden**: Display access denied message, log error for investigation
- **404 Not Found**: Display "resource not found" message, suggest alternative actions
- **429 Too Many Requests**: Implement exponential backoff, display rate limit message
- **500 Server Error**: Display generic error message, log error details, provide retry option
- **Invalid Response Schema**: Log validation error, display generic error message, use cached data if available

#### Client Errors

- **JavaScript Exceptions**: Catch with Error Boundary, display fallback UI, log error with stack trace
- **Rendering Errors**: Display component-level error message, prevent full page crash
- **State Management Errors**: Reset affected state to default, log error, allow user to continue

### Error Recovery Mechanisms

1. **Automatic Retry**: Network errors and 5xx errors trigger automatic retry with exponential backoff (max 3 attempts)
2. **Cached Data Fallback**: When fresh data fetch fails, display cached data with staleness indicator
3. **Graceful Degradation**: Missing optional data (plot boundaries, NDVI) doesn't break UI, alternative representations shown
4. **Manual Retry**: All error states include manual retry button for user-initiated recovery
5. **Error Logging**: All errors logged to console (development) and monitoring service (production) with context

### Error Boundary Implementation

```typescript
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

class ErrorBoundary extends React.Component<Props, ErrorBoundaryState> {
  // Catches rendering errors in child components
  // Displays fallback UI
  // Logs error details
  // Provides "Try Again" button to reset error state
}
```

## Testing Strategy

### Testing Approach

The FPO Dashboard employs a comprehensive testing strategy combining unit tests, property-based tests, integration tests, and end-to-end tests. This multi-layered approach ensures both specific behavior correctness and general system reliability.

### Unit Testing

**Framework**: Vitest + React Testing Library

**Scope**: Individual components, hooks, utility functions, and services

**Focus Areas**:
- Component rendering with various props
- User interaction handling (clicks, form submissions)
- Conditional rendering logic
- Error state handling
- Loading state handling
- Edge cases (empty data, missing optional fields)

**Example Unit Tests**:
- Login form validation with invalid inputs
- Activity card rendering with missing optional fields
- Date range picker with boundary dates
- Error boundary fallback UI display
- WebSocket reconnection on connection loss

**Balance**: Unit tests focus on specific examples and edge cases. Avoid writing excessive unit tests for scenarios better covered by property tests. Prioritize:
- Integration points between components
- Specific error conditions
- UI interaction flows
- Component lifecycle behavior

### Property-Based Testing

**Framework**: fast-check (JavaScript property-based testing library)

**Configuration**: Minimum 100 iterations per property test

**Scope**: Universal properties that should hold across all valid inputs

**Tagging Convention**: Each property test must include a comment tag:
```typescript
// Feature: fpo-dashboard, Property 5: Activity Stream Filtering Correctness
```

**Focus Areas**:
- Data transformation correctness (filtering, sorting, mapping)
- Calculation accuracy (metrics, scores, aggregations)
- State mutation correctness (updates, additions, deletions)
- Validation logic (input validation, schema validation)
- Error handling patterns (retry logic, fallback behavior)

**Example Property Tests**:
- For any set of transactions and filter criteria, filtered results match criteria (Property 8)
- For any payment data, success rate calculation is correct (Property 18)
- For any API error, error handling displays message and provides retry (Property 39)
- For any search query, all matching results are returned (Property 11)
- For any date range, only items within range are displayed (Property 6)

**Generator Strategy**:
- Create custom generators for domain objects (Farmer, Transaction, Alert, etc.)
- Generate edge cases (empty arrays, null values, boundary dates)
- Generate realistic data distributions (common crop types, typical price ranges)
- Combine generators for complex scenarios (farmer with plots and transactions)

### Integration Testing

**Framework**: Vitest + React Testing Library + MSW (Mock Service Worker)

**Scope**: Feature modules with mocked API interactions

**Focus Areas**:
- API integration correctness (correct endpoints, parameters, headers)
- State management integration (React Query + Zustand)
- WebSocket message handling
- Authentication flow (login, token refresh, logout)
- Multi-component workflows (search → filter → detail view)

**Example Integration Tests**:
- Fetch farmers from API, display in list, search, view detail
- Receive WebSocket activity event, display in stream, filter by agent type
- API returns 401, refresh token, retry request, succeed
- Load transaction list, apply filters, verify API called with correct parameters
- Add dispute note, verify optimistic update, verify API call, handle success/failure

### End-to-End Testing

**Framework**: Playwright

**Scope**: Critical user journeys through the full application

**Focus Areas**:
- Authentication flow (login, session management, logout)
- Core workflows (view farmers, monitor transactions, track payments)
- Real-time updates (WebSocket activity stream)
- Error scenarios (network failures, API errors)
- Cross-browser compatibility (Chrome, Firefox, Safari)

**Example E2E Tests**:
- FPO coordinator logs in, views activity stream, sees new events appear
- Coordinator searches for farmer, views profile, sees transaction history
- Coordinator filters transactions by status, views disputed transaction, adds note
- Network disconnects, error message appears, network reconnects, data refreshes
- Coordinator exports analytics as CSV, file downloads successfully

### Accessibility Testing

**Framework**: axe-core + Playwright

**Scope**: WCAG 2.1 AA compliance verification

**Focus Areas**:
- Color contrast ratios
- Keyboard navigation
- Screen reader compatibility (ARIA labels, roles, live regions)
- Focus management
- Form labels and error messages

**Example Accessibility Tests**:
- All interactive elements are keyboard accessible
- All images and charts have text alternatives
- Form inputs have associated labels
- Error messages are announced to screen readers
- Focus indicators are visible

### Performance Testing

**Framework**: Lighthouse CI + Playwright

**Scope**: Load time, runtime performance, bundle size

**Focus Areas**:
- Initial page load time (target: <3s on 4G)
- Time to interactive
- Bundle size (target: <500KB gzipped)
- Lazy loading effectiveness
- Memory usage during long sessions

**Example Performance Tests**:
- Dashboard loads within 3 seconds on simulated 4G connection
- Large transaction list (1000+ items) renders without jank
- Activity stream handles 100+ events without memory leaks
- Code splitting reduces initial bundle size

### Test Coverage Goals

- **Unit Test Coverage**: 80%+ line coverage for business logic
- **Property Test Coverage**: All 47 correctness properties implemented
- **Integration Test Coverage**: All API endpoints and WebSocket messages
- **E2E Test Coverage**: All critical user journeys (login, view data, perform actions)
- **Accessibility Test Coverage**: All pages and interactive components

### Continuous Integration

All tests run on every pull request:
1. Unit tests (fast feedback, <2 minutes)
2. Property tests (comprehensive coverage, <5 minutes)
3. Integration tests (API mocking, <3 minutes)
4. E2E tests (critical paths only, <10 minutes)
5. Accessibility tests (automated checks, <2 minutes)
6. Performance tests (Lighthouse, <3 minutes)

Total CI pipeline: <25 minutes for full test suite

### Testing Best Practices

1. **Test Behavior, Not Implementation**: Focus on user-visible behavior and API contracts
2. **Avoid Test Duplication**: Use property tests for general cases, unit tests for specific examples
3. **Mock External Dependencies**: Use MSW for API mocking, mock WebSocket in tests
4. **Test Error Paths**: Verify error handling, not just happy paths
5. **Keep Tests Fast**: Unit and property tests should run in seconds, not minutes
6. **Maintain Test Data Generators**: Reusable generators for consistent test data
7. **Document Complex Tests**: Add comments explaining test intent and setup
8. **Run Tests Locally**: Ensure all tests pass before pushing to CI

## Implementation Notes

### Technology Stack

- **React 18**: UI framework with concurrent features
- **TypeScript 5**: Type safety and developer experience
- **Vite**: Build tool for fast development and optimized production builds
- **React Query (TanStack Query)**: Server state management, caching, and synchronization
- **Zustand**: Lightweight client state management
- **React Router**: Client-side routing
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: Accessible component library built on Radix UI
- **Recharts**: Composable charting library
- **Mapbox GL JS**: Interactive map visualization
- **AWS Amplify**: Cognito authentication integration
- **date-fns**: Date manipulation and formatting
- **zod**: Runtime schema validation
- **fast-check**: Property-based testing

### Code Organization

**Feature-Based Structure**: Each feature module is self-contained with components, hooks, types, and services.

**Shared Code**: Common components, hooks, utilities, and types are in the `shared/` directory.

**Service Layer**: API clients and authentication services are in the `services/` directory, providing a clean abstraction over external dependencies.

**Type Safety**: All API responses, component props, and state are fully typed with TypeScript interfaces.

### State Management Strategy

**Server State (React Query)**:
- Farmer data, transaction data, analytics data
- Automatic caching with configurable stale time
- Background refetching for fresh data
- Optimistic updates for mutations
- Query invalidation on data changes

**Client State (Zustand)**:
- UI state (sidebar open/closed, active module)
- User preferences (theme, notification settings)
- Transient state (form inputs, filter selections)
- WebSocket connection status

**Local Component State (useState)**:
- Component-specific UI state (dropdown open, modal visible)
- Form state (input values, validation errors)
- Temporary state (loading indicators, error messages)

### Performance Optimizations

1. **Code Splitting**: Lazy load feature modules with React.lazy()
2. **Route-Based Splitting**: Each route loads only required code
3. **Component Memoization**: Use React.memo() for expensive components
4. **Virtual Scrolling**: Implement virtual scrolling for large lists (react-window)
5. **Image Optimization**: Lazy load images, use WebP format, responsive images
6. **Bundle Optimization**: Tree shaking, minification, compression
7. **Caching Strategy**: Aggressive caching with React Query, service worker for offline support
8. **Debouncing**: Debounce search inputs and filter changes
9. **Pagination**: Paginate large datasets (100 items per page)
10. **WebSocket Throttling**: Throttle high-frequency WebSocket messages

### Security Considerations

1. **Authentication**: AWS Cognito for secure authentication and session management
2. **Authorization**: Token-based API authorization, tokens stored in memory (not localStorage)
3. **HTTPS Only**: All traffic over HTTPS, enforced by CloudFront
4. **XSS Prevention**: React's built-in XSS protection, sanitize user-generated content
5. **CSRF Protection**: Token-based authentication eliminates CSRF risk
6. **Content Security Policy**: Strict CSP headers to prevent injection attacks
7. **Dependency Security**: Regular dependency audits, automated vulnerability scanning
8. **Sensitive Data**: No sensitive data in client-side logs or error messages

### Deployment Strategy

1. **Build**: Vite builds optimized production bundle with code splitting and minification
2. **Upload**: Deploy build artifacts to S3 bucket
3. **Invalidate**: Invalidate CloudFront cache for updated files
4. **Rollback**: Keep previous build artifacts for quick rollback if needed
5. **Monitoring**: CloudWatch for error tracking, performance monitoring
6. **Versioning**: Semantic versioning for releases, git tags for deployments

### Development Workflow

1. **Local Development**: Vite dev server with hot module replacement
2. **API Mocking**: MSW for local API mocking during development
3. **Type Checking**: TypeScript compiler in watch mode
4. **Linting**: ESLint for code quality, Prettier for formatting
5. **Testing**: Vitest in watch mode for rapid feedback
6. **Storybook**: Component development and documentation (optional)
7. **Git Hooks**: Pre-commit hooks for linting and type checking

### Monitoring and Observability

1. **Error Tracking**: Sentry or CloudWatch for client-side error tracking
2. **Performance Monitoring**: Real User Monitoring (RUM) for performance metrics
3. **Analytics**: User behavior analytics (page views, feature usage)
4. **Logging**: Structured logging for debugging and troubleshooting
5. **Alerting**: Alerts for high error rates, performance degradation

### Accessibility Implementation

1. **Semantic HTML**: Use appropriate HTML elements (button, nav, main, etc.)
2. **ARIA Attributes**: Add ARIA labels, roles, and live regions where needed
3. **Keyboard Navigation**: Ensure all interactive elements are keyboard accessible
4. **Focus Management**: Manage focus for modals, dropdowns, and route changes
5. **Color Contrast**: Ensure WCAG AA contrast ratios (4.5:1 for text)
6. **Screen Reader Testing**: Test with NVDA, JAWS, VoiceOver
7. **Alternative Text**: Provide text alternatives for images and charts

### Browser Support

- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **No IE Support**: Internet Explorer is not supported
- **Mobile Browsers**: Safari iOS 14+, Chrome Android 90+
- **Progressive Enhancement**: Core functionality works without JavaScript (login redirect)

### Internationalization (Future Consideration)

While not in the initial scope, the architecture supports future internationalization:
- Use i18n library (react-i18next)
- Extract all user-facing strings to translation files
- Support RTL languages with CSS logical properties
- Format dates, numbers, and currencies based on locale
