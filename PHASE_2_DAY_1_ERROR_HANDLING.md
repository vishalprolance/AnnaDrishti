# Phase 2 - Day 1: Error Handling Implementation

## What We're Adding

### 1. Custom Exception Classes
- `WorkflowError` - Base exception for workflow issues
- `ValidationError` - Input validation failures

### 2. Input Validation
- Required field checks (farmer_name, crop_type)
- Numeric range validation (plot_area: 0-100 acres, quantity: 0-1M kg)
- Type validation (ensure numbers are actually numbers)
- Returns 400 Bad Request with clear error messages

### 3. Exponential Backoff Retry
- Retries DynamoDB operations up to 3 times
- Exponential backoff: 1s, 2s, 4s
- Handles `ProvisionedThroughputExceededException`
- Prevents cascading failures

### 4. CloudWatch Metrics
- `WorkflowCreated` - Successful workflow creation
- `WorkflowCreationFailed` - Failed attempts
- `ValidationError` - Input validation failures
- `WorkflowError` - Workflow-specific errors
- `UnexpectedError` - Unexpected exceptions
- `WorkflowCreationLatency` - Performance tracking

### 5. Structured Error Responses
```json
{
  "success": false,
  "error": "Validation failed",
  "details": "farmer_name is required; plot_area must be between 0 and 100 acres",
  "message": "Invalid input data"
}
```

### 6. Enhanced Logging
- Detailed error messages
- Stack traces for unexpected errors
- Metric publishing for monitoring

## Implementation Status

1. ✅ `start_workflow.py` - Complete
2. ✅ `scan_market.py` - Complete
3. ✅ `detect_surplus.py` - Complete
4. ✅ `negotiate.py` - Complete

All Lambda functions now have:
- Custom exception classes
- Input validation with clear error messages
- Exponential backoff retry (3 attempts: 1s, 2s, 4s)
- CloudWatch metrics publishing
- Structured error responses (400/500 status codes)
- Performance tracking

## CloudWatch Metrics Published

### Workflows (start_workflow.py)
- `AnnaDrishti/Workflows/WorkflowCreated`
- `AnnaDrishti/Workflows/WorkflowCreationFailed`
- `AnnaDrishti/Workflows/ValidationError`
- `AnnaDrishti/Workflows/WorkflowError`
- `AnnaDrishti/Workflows/UnexpectedError`
- `AnnaDrishti/Workflows/WorkflowCreationLatency`

### Market Scan (scan_market.py)
- `AnnaDrishti/MarketScan/MarketDataFetched`
- `AnnaDrishti/MarketScan/MarketDataFetchFailed`
- `AnnaDrishti/MarketScan/MarketScanCompleted`
- `AnnaDrishti/MarketScan/MarketScanFailed`
- `AnnaDrishti/MarketScan/ValidationError`
- `AnnaDrishti/MarketScan/MarketScanError`
- `AnnaDrishti/MarketScan/UnexpectedError`
- `AnnaDrishti/MarketScan/MarketScanLatency`

### Surplus Detection (detect_surplus.py)
- `AnnaDrishti/SurplusDetection/SurplusDetected`
- `AnnaDrishti/SurplusDetection/NoSurplusDetected`
- `AnnaDrishti/SurplusDetection/SurplusDetectionCompleted`
- `AnnaDrishti/SurplusDetection/SurplusDetectionFailed`
- `AnnaDrishti/SurplusDetection/ValidationError`
- `AnnaDrishti/SurplusDetection/SurplusDetectionError`
- `AnnaDrishti/SurplusDetection/UnexpectedError`
- `AnnaDrishti/SurplusDetection/SurplusDetectionLatency`

### Negotiation (negotiate.py)
- `AnnaDrishti/Negotiation/BedrockInvocationSuccess`
- `AnnaDrishti/Negotiation/BedrockInvocationFailed`
- `AnnaDrishti/Negotiation/NegotiationCompleted`
- `AnnaDrishti/Negotiation/NegotiationFailed`
- `AnnaDrishti/Negotiation/ValidationError`
- `AnnaDrishti/Negotiation/BedrockError`
- `AnnaDrishti/Negotiation/NegotiationError`
- `AnnaDrishti/Negotiation/UnexpectedError`
- `AnnaDrishti/Negotiation/NegotiationLatency`

## Next Steps

Add CloudWatch Alarms and Dashboard for monitoring (optional for Phase 2).

## Benefits

- **Reliability**: Automatic retries prevent transient failures
- **Debuggability**: Clear error messages and metrics
- **Monitoring**: CloudWatch metrics for alerting
- **User Experience**: Helpful error messages instead of generic failures

Ready to continue with the other Lambda functions?
