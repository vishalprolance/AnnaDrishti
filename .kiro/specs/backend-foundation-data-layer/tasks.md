# Implementation Plan: Backend Foundation & Data Layer

## Overview

This implementation plan breaks down the Backend Foundation & Data Layer into discrete coding tasks. The approach follows a layered architecture: database schema → data models → business logic → API endpoints → testing. Each task builds incrementally, ensuring the system remains functional and testable at every step.

The implementation uses Python 3.11+ with FastAPI for the API server, SQLAlchemy for ORM, PostgreSQL for the database, and Redis for session management. All tasks include references to specific requirements they address.

## Tasks

- [ ] 1. Set up project structure and dependencies
  - Create Python project with Poetry or pip-requirements
  - Install FastAPI, SQLAlchemy, psycopg2, redis, pydantic, python-jose (JWT), passlib (password hashing), pytest, hypothesis
  - Set up directory structure: app/, app/models/, app/services/, app/api/, app/core/, tests/
  - Create configuration management using pydantic BaseSettings for environment variables
  - _Requirements: 12.1, 12.5_

- [ ] 2. Implement database schema and migrations
  - [ ] 2.1 Create SQLAlchemy models for all entities
    - Implement FPO, Coordinator, Farmer, Plot, Buyer, Processor, Transaction, TransactionAudit, AuditLog models
    - Define relationships, foreign keys, and constraints
    - Add indexes for performance (fpo_id, phone, created_at, etc.)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_
  
  - [ ]* 2.2 Write property test for foreign key constraints
    - **Property 4: Foreign key constraint enforcement**
    - **Validates: Requirements 2.7**
  
  - [ ] 2.3 Create Alembic migration scripts
    - Initialize Alembic for database migrations
    - Generate initial migration from SQLAlchemy models
    - Add migration script for creating indexes
    - _Requirements: 12.4_
  
  - [ ]* 2.4 Write unit tests for model relationships
    - Test that relationships are correctly defined
    - Test cascade delete behavior
    - _Requirements: 2.7_

- [ ] 3. Implement database connection and session management
  - [ ] 3.1 Create database connection pool
    - Implement SQLAlchemy engine with connection pooling
    - Configure pool size and timeout from environment variables
    - Add connection retry logic with exponential backoff
    - _Requirements: 8.4, 11.1_
  
  - [ ]* 3.2 Write property test for connection retry
    - **Property 42: Database connection retry with backoff**
    - **Validates: Requirements 11.1**
  
  - [ ] 3.3 Create database session dependency for FastAPI
    - Implement get_db() dependency that yields database sessions
    - Ensure sessions are properly closed after requests
    - _Requirements: 7.1_

- [ ] 4. Implement Redis session store
  - [ ] 4.1 Create Redis client and session service
    - Implement RedisClient wrapper with connection handling
    - Implement SessionService with create, get, update, delete methods
    - Set TTL to 30 minutes for all sessions
    - Handle Redis connection failures gracefully
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 11.5_
  
  - [ ]* 4.2 Write property test for session TTL
    - **Property 29: Session TTL enforcement**
    - **Validates: Requirements 6.3, 6.5**
  
  - [ ]* 4.3 Write property test for session TTL reset
    - **Property 31: Session TTL reset on update**
    - **Validates: Requirements 6.7**
  
  - [ ]* 4.4 Write property test for session uniqueness
    - **Property 28: Session uniqueness**
    - **Validates: Requirements 6.1**

- [ ] 5. Implement authentication and authorization
  - [ ] 5.1 Create AuthService with password hashing and JWT
    - Implement password hashing using passlib with bcrypt
    - Implement JWT token creation and validation using python-jose
    - Add token expiration handling (24 hour default)
    - _Requirements: 3.1, 3.2, 3.3, 3.5_
  
  - [ ]* 5.2 Write property test for credential validation
    - **Property 13: Credential validation**
    - **Validates: Requirements 3.1**
  
  - [ ]* 5.3 Write property test for JWT token structure
    - **Property 14: JWT token structure**
    - **Validates: Requirements 3.2**
  
  - [ ]* 5.4 Write property test for token validation
    - **Property 15: Token validation**
    - **Validates: Requirements 3.3, 3.5**
  
  - [ ] 5.5 Create authentication middleware
    - Implement FastAPI dependency for JWT token validation
    - Extract user claims from token and add to request state
    - Return 401 for invalid/expired tokens
    - _Requirements: 3.3, 3.5_
  
  - [ ] 5.6 Create FPO scope enforcement middleware
    - Implement dependency that checks user's FPO matches resource FPO
    - Return 403 for unauthorized access attempts
    - _Requirements: 3.4_
  
  - [ ]* 5.7 Write property test for FPO scope enforcement
    - **Property 16: FPO scope enforcement**
    - **Validates: Requirements 3.4**

- [ ] 6. Checkpoint - Ensure database and auth infrastructure works
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement audit logging service
  - [ ] 7.1 Create AuditService for logging all actions
    - Implement log_action() for general CRUD operations
    - Implement log_transaction_status_change() for transaction audits
    - Implement log_authentication_attempt() for auth events
    - Implement log_farmer_confirmation() for confirmations
    - Store logs in audit_logs and transaction_audit tables
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  
  - [ ]* 7.2 Write property test for CRUD operation logging
    - **Property 36: CRUD operation logging**
    - **Validates: Requirements 10.1**
  
  - [ ]* 7.3 Write property test for authentication logging
    - **Property 37: Authentication attempt logging**
    - **Validates: Requirements 10.2**
  
  - [ ]* 7.4 Write property test for audit log schema consistency
    - **Property 40: Audit log schema consistency**
    - **Validates: Requirements 10.5**
  
  - [ ] 7.5 Implement audit log query endpoints
    - Create endpoint to query audit logs with filtering
    - Support filters: entity_type, entity_id, user_id, date_range, action_type
    - _Requirements: 10.6_
  
  - [ ]* 7.6 Write property test for audit log filtering
    - **Property 41: Audit log query filtering**
    - **Validates: Requirements 10.6**

- [ ] 8. Implement business logic services
  - [ ] 8.1 Create FarmerService
    - Implement create_farmer() with validation
    - Implement get_farmer() with FPO scope check
    - Implement list_farmers() with pagination and filtering
    - Implement update_farmer() with audit logging
    - Implement delete_farmer() (soft delete)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_
  
  - [ ] 8.2 Create PlotService
    - Implement create_plot() with farmer validation
    - Implement get_plots_for_farmer()
    - Implement update_plot() with audit logging
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [ ] 8.3 Create TransactionService
    - Implement create_transaction() with database transaction wrapper
    - Implement update_status() with audit trail creation
    - Implement get_transaction_with_audit()
    - Implement calculate_farmer_revenue()
    - Ensure all operations use database transactions for atomicity
    - _Requirements: 4.1, 4.2, 4.3, 5.1, 5.2, 5.3, 5.6, 5.7, 7.1, 7.5, 7.6_
  
  - [ ]* 8.4 Write property test for transaction immutability
    - **Property 25: Transaction immutability**
    - **Validates: Requirements 5.4**
  
  - [ ]* 8.5 Write property test for audit trail append-only
    - **Property 26: Audit trail append-only**
    - **Validates: Requirements 5.5, 5.6**
  
  - [ ] 8.6 Create BuyerService and ProcessorService
    - Implement CRUD operations for buyers and processors
    - Include FPO scope enforcement
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 9. Implement data validation
  - [ ] 9.1 Create Pydantic schemas for all entities
    - Define request/response schemas with validation rules
    - Add validators for phone numbers (10 digits)
    - Add validators for positive numbers (quantity, price)
    - Add validators for coordinate ranges
    - Add custom error messages for validation failures
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_
  
  - [ ]* 9.2 Write property test for required field validation
    - **Property 6: Required field validation**
    - **Validates: Requirements 9.1, 9.7**
  
  - [ ]* 9.3 Write property test for data type validation
    - **Property 7: Data type validation**
    - **Validates: Requirements 9.2**
  
  - [ ]* 9.4 Write property test for phone number validation
    - **Property 8: Phone number format validation**
    - **Validates: Requirements 9.3**
  
  - [ ]* 9.5 Write property test for positive number validation
    - **Property 9: Positive number validation**
    - **Validates: Requirements 9.4**
  
  - [ ]* 9.6 Write property test for coordinate validation
    - **Property 10: Coordinate range validation**
    - **Validates: Requirements 9.5**
  
  - [ ]* 9.7 Write property test for validation error messages
    - **Property 11: Validation error message completeness**
    - **Validates: Requirements 9.6**
  
  - [ ]* 9.8 Write property test for unique constraint enforcement
    - **Property 12: Unique constraint enforcement**
    - **Validates: Requirements 9.8**

- [ ] 10. Checkpoint - Ensure services and validation work
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Implement API endpoints - Authentication
  - [ ] 11.1 Create /auth/login endpoint
    - Accept username and password
    - Validate credentials using AuthService
    - Return JWT token on success
    - Log authentication attempt
    - _Requirements: 3.1, 3.2, 10.2_
  
  - [ ] 11.2 Create /auth/refresh endpoint
    - Accept refresh token
    - Issue new access token
    - _Requirements: 3.2_
  
  - [ ] 11.3 Create /auth/password-reset endpoints
    - Implement request and confirm endpoints
    - Generate secure OTP tokens
    - _Requirements: 3.6_
  
  - [ ]* 11.4 Write unit tests for auth endpoints
    - Test successful login
    - Test failed login
    - Test token refresh
    - _Requirements: 3.1, 3.2, 3.6_

- [ ] 12. Implement API endpoints - Farmer Management
  - [ ] 12.1 Create POST /farmers endpoint
    - Validate request using Pydantic schema
    - Call FarmerService.create_farmer()
    - Return 201 with created farmer
    - Log action in audit log
    - _Requirements: 1.1, 1.2, 4.1, 10.1_
  
  - [ ] 12.2 Create GET /farmers/{id} endpoint
    - Enforce FPO scope
    - Call FarmerService.get_farmer()
    - Return 200 with farmer data or 404
    - _Requirements: 1.1, 4.2_
  
  - [ ] 12.3 Create GET /farmers endpoint with pagination
    - Support query parameters: fpo_id, page, size, village
    - Call FarmerService.list_farmers()
    - Return paginated response
    - _Requirements: 1.1, 4.2, 4.5, 4.6_
  
  - [ ] 12.4 Create PUT /farmers/{id} endpoint
    - Validate updates
    - Call FarmerService.update_farmer()
    - Log action in audit log
    - Return 200 with updated farmer
    - _Requirements: 1.1, 4.3, 10.1_
  
  - [ ] 12.5 Create DELETE /farmers/{id} endpoint
    - Call FarmerService.delete_farmer()
    - Log action in audit log
    - Return 204
    - _Requirements: 1.1, 4.4, 10.1_
  
  - [ ]* 12.6 Write property test for create-read round trip
    - **Property 17: Create-read round trip**
    - **Validates: Requirements 4.1, 4.2**
  
  - [ ]* 12.7 Write property test for update persistence
    - **Property 18: Update persistence**
    - **Validates: Requirements 4.3**
  
  - [ ]* 12.8 Write property test for delete effectiveness
    - **Property 19: Delete effectiveness**
    - **Validates: Requirements 4.4**

- [ ] 13. Implement API endpoints - Plot Management
  - [ ] 13.1 Create POST /plots endpoint
    - Validate request
    - Call PlotService.create_plot()
    - Return 201 with created plot
    - _Requirements: 1.1, 4.1_
  
  - [ ] 13.2 Create GET /plots endpoint
    - Support filtering by farmer_id
    - Call PlotService.get_plots_for_farmer()
    - Return list of plots
    - _Requirements: 1.1, 4.2_
  
  - [ ] 13.3 Create PUT /plots/{id} endpoint
    - Validate updates
    - Call PlotService.update_plot()
    - Return 200 with updated plot
    - _Requirements: 1.1, 4.3_
  
  - [ ]* 13.4 Write unit tests for plot endpoints
    - Test plot creation with valid data
    - Test plot retrieval by farmer
    - Test plot updates
    - _Requirements: 4.1, 4.2, 4.3_

- [ ] 14. Implement API endpoints - Transaction Management
  - [ ] 14.1 Create POST /transactions endpoint
    - Validate request
    - Call TransactionService.create_transaction()
    - Ensure operation uses database transaction
    - Return 201 with created transaction
    - _Requirements: 1.1, 4.1, 5.1, 7.1_
  
  - [ ] 14.2 Create GET /transactions/{id} endpoint
    - Call TransactionService.get_transaction_with_audit()
    - Return transaction with full audit trail
    - _Requirements: 1.1, 4.2, 5.7_
  
  - [ ] 14.3 Create PUT /transactions/{id}/status endpoint
    - Validate status transition
    - Call TransactionService.update_status()
    - Create audit entry
    - Return updated transaction
    - _Requirements: 1.1, 4.3, 5.5, 5.6, 10.3_
  
  - [ ] 14.4 Create GET /transactions endpoint with filtering
    - Support filters: farmer_id, status, from_date, to_date
    - Support pagination
    - Call TransactionService with filters
    - Return paginated list
    - _Requirements: 1.1, 4.2, 4.5, 4.6, 5.7_
  
  - [ ] 14.5 Create GET /transactions/{id}/audit endpoint
    - Return full audit trail for transaction
    - _Requirements: 1.1, 5.7_
  
  - [ ]* 14.6 Write property test for transaction uniqueness
    - **Property 24: Transaction uniqueness and timestamping**
    - **Validates: Requirements 5.1**
  
  - [ ]* 14.7 Write property test for transaction history filtering
    - **Property 27: Transaction history filtering**
    - **Validates: Requirements 5.7**
  
  - [ ]* 14.8 Write property test for multi-operation atomicity
    - **Property 32: Multi-operation atomicity**
    - **Validates: Requirements 7.1, 7.2**
  
  - [ ]* 14.9 Write property test for payment update atomicity
    - **Property 34: Payment update atomicity**
    - **Validates: Requirements 7.6**

- [ ] 15. Implement API endpoints - Session Management
  - [ ] 15.1 Create POST /sessions endpoint
    - Validate request
    - Call SessionService.create_session()
    - Return session with ID and expiration
    - _Requirements: 1.1, 6.1, 6.2_
  
  - [ ] 15.2 Create GET /sessions/{id} endpoint
    - Call SessionService.get_session()
    - Return session or 404 if expired
    - _Requirements: 1.1, 6.4_
  
  - [ ] 15.3 Create PUT /sessions/{id} endpoint
    - Validate state updates
    - Call SessionService.update_session()
    - Reset TTL if requested
    - Return updated session
    - _Requirements: 1.1, 6.7_
  
  - [ ] 15.4 Create DELETE /sessions/{id} endpoint
    - Call SessionService.delete_session()
    - Return 204
    - _Requirements: 1.1, 6.6_
  
  - [ ]* 15.5 Write property test for session state persistence
    - **Property 30: Session state persistence**
    - **Validates: Requirements 6.4, 6.7**

- [ ] 16. Implement API endpoints - Buyer and Processor Management
  - [ ] 16.1 Create CRUD endpoints for buyers
    - POST /buyers, GET /buyers/{id}, GET /buyers, PUT /buyers/{id}, DELETE /buyers/{id}
    - Use BuyerService for business logic
    - Enforce FPO scope
    - _Requirements: 1.1, 4.1, 4.2, 4.3, 4.4_
  
  - [ ] 16.2 Create CRUD endpoints for processors
    - POST /processors, GET /processors/{id}, GET /processors, PUT /processors/{id}, DELETE /processors/{id}
    - Use ProcessorService for business logic
    - Enforce FPO scope
    - _Requirements: 1.1, 4.1, 4.2, 4.3, 4.4_
  
  - [ ]* 16.3 Write unit tests for buyer and processor endpoints
    - Test CRUD operations
    - Test FPO scope enforcement
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 17. Checkpoint - Ensure all API endpoints work
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 18. Implement error handling and middleware
  - [ ] 18.1 Create global exception handler
    - Catch all exceptions and return structured error responses
    - Log unexpected errors with stack traces
    - Return generic error messages to clients
    - _Requirements: 1.4, 11.3_
  
  - [ ]* 18.2 Write property test for request validation consistency
    - **Property 1: Request validation consistency**
    - **Validates: Requirements 1.2, 1.4**
  
  - [ ]* 18.3 Write property test for unexpected error handling
    - **Property 43: Unexpected error logging and response**
    - **Validates: Requirements 11.3**
  
  - [ ] 18.2 Create request logging middleware
    - Log all incoming requests with timestamp and request ID
    - Add request ID to response headers
    - _Requirements: 1.5_
  
  - [ ]* 18.5 Write property test for request logging
    - **Property 3: Request logging completeness**
    - **Validates: Requirements 1.5**
  
  - [ ] 18.6 Create CORS middleware
    - Configure CORS for web dashboard access
    - Allow credentials and specific origins
    - _Requirements: 1.6_
  
  - [ ] 18.7 Implement circuit breaker for future external services
    - Create CircuitBreaker class with state management
    - Add open/closed/half-open state transitions
    - _Requirements: 11.6_
  
  - [ ]* 18.8 Write property test for circuit breaker
    - **Property 44: Circuit breaker state transitions**
    - **Validates: Requirements 11.6**

- [ ] 19. Implement health check and metrics endpoints
  - [ ] 19.1 Create GET /health endpoint
    - Check database connectivity
    - Check Redis connectivity
    - Return 200 if healthy, 503 if unhealthy
    - _Requirements: 11.4_
  
  - [ ] 19.2 Create GET /metrics endpoint
    - Track request counts, error rates, response times
    - Return metrics in JSON format
    - _Requirements: 12.6_
  
  - [ ]* 19.3 Write unit tests for health and metrics
    - Test health check with healthy/unhealthy dependencies
    - Test metrics endpoint returns expected data
    - _Requirements: 11.4, 12.6_

- [ ] 20. Implement UTF-8 and Hindi language support
  - [ ] 20.1 Configure database for UTF-8
    - Ensure PostgreSQL uses UTF-8 encoding
    - Test with Hindi text in all text fields
    - _Requirements: 1.3_
  
  - [ ]* 20.2 Write property test for UTF-8 round trip
    - **Property 2: UTF-8 encoding round trip**
    - **Validates: Requirements 1.3**

- [ ] 21. Implement caching layer
  - [ ] 21.1 Create caching decorator for frequently accessed data
    - Implement cache decorator using Redis
    - Add cache invalidation on updates
    - Configure TTL for cached data
    - _Requirements: 8.5_
  
  - [ ]* 21.2 Write property test for cache consistency
    - **Property 35: Cache consistency**
    - **Validates: Requirements 8.5**

- [ ] 22. Implement pagination and filtering helpers
  - [ ] 22.1 Create pagination utility
    - Implement paginate() function for SQLAlchemy queries
    - Return page metadata (total, pages, current page)
    - _Requirements: 4.5_
  
  - [ ]* 22.2 Write property test for pagination correctness
    - **Property 20: Pagination correctness**
    - **Validates: Requirements 4.5**
  
  - [ ] 22.3 Create filtering and sorting utilities
    - Implement dynamic filter builder for SQLAlchemy
    - Support multiple filter criteria
    - Support sorting by any field
    - _Requirements: 4.6_
  
  - [ ]* 22.4 Write property test for filtering correctness
    - **Property 21: Filtering correctness**
    - **Validates: Requirements 4.6**
  
  - [ ]* 22.5 Write property test for sorting correctness
    - **Property 22: Sorting correctness**
    - **Validates: Requirements 4.6**

- [ ] 23. Implement multi-tenancy enforcement
  - [ ] 23.1 Add FPO scope checks to all services
    - Ensure all queries filter by FPO ID
    - Prevent cross-FPO data access
    - _Requirements: 2.8, 3.4_
  
  - [ ]* 23.2 Write property test for multi-tenancy isolation
    - **Property 5: Multi-tenancy data isolation**
    - **Validates: Requirements 2.8**

- [ ] 24. Create deployment configuration
  - [ ] 24.1 Create Dockerfile
    - Multi-stage build for production
    - Install dependencies and copy application code
    - Configure for Python 3.11+
    - _Requirements: 12.2_
  
  - [ ] 24.2 Create docker-compose.yml for local development
    - Include PostgreSQL, Redis, and API server
    - Configure environment variables
    - _Requirements: 12.5_
  
  - [ ] 24.3 Create AWS Lambda deployment configuration (optional)
    - Create Lambda handler for FastAPI
    - Configure API Gateway integration
    - _Requirements: 12.3_
  
  - [ ] 24.4 Create environment variable templates
    - Create .env.example with all required variables
    - Document each variable
    - _Requirements: 12.1, 12.5_
  
  - [ ]* 24.5 Write unit tests for configuration loading
    - Test environment variable parsing
    - Test default values
    - _Requirements: 12.1_

- [ ] 25. Write integration tests
  - [ ]* 25.1 Write integration test for full transaction flow
    - Create farmer → create plot → create transaction → update status
    - Verify audit trail is complete
    - _Requirements: 4.1, 4.2, 4.3, 5.1, 5.5, 5.6_
  
  - [ ]* 25.2 Write integration test for authentication flow
    - Register coordinator → login → access protected endpoint
    - Test token expiration
    - _Requirements: 3.1, 3.2, 3.3, 3.5_
  
  - [ ]* 25.3 Write integration test for multi-tenancy
    - Create data for multiple FPOs
    - Verify coordinators can only access their FPO's data
    - _Requirements: 2.8, 3.4_
  
  - [ ]* 25.4 Write integration test for session lifecycle
    - Create session → update state → verify TTL → verify expiration
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.7_

- [ ] 26. Final checkpoint - Ensure all tests pass and system is ready
  - Run full test suite (unit + property + integration)
  - Verify all 44 correctness properties have tests
  - Check test coverage meets goals (85% line, 80% branch)
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional property-based and integration tests that can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties across many inputs
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end flows across components
- The implementation follows a bottom-up approach: database → services → API → tests
- All financial operations use database transactions for ACID guarantees
- Multi-tenancy is enforced at both the service and API layers
- Audit logging is comprehensive and immutable for compliance
