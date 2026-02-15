# Design Document: Backend Foundation & Data Layer

## Overview

The Backend Foundation & Data Layer provides the core infrastructure for Anna Drishti, implementing a FastAPI-based REST API server with PostgreSQL for persistent storage and Redis for session management. The system is designed to support multi-tenant FPO operations, handle financial transactions with ACID guarantees, and maintain comprehensive audit trails.

The architecture follows a layered approach with clear separation between API endpoints, business logic, data access, and external integrations. The design prioritizes data integrity, scalability, and operational transparency through comprehensive logging and audit trails.

Key design principles:
- **Multi-tenancy**: All data is scoped to FPOs with strict isolation
- **Immutability**: Transaction ledger entries are append-only
- **Auditability**: All state changes are logged with timestamps and actors
- **Scalability**: Stateless API design with connection pooling and caching
- **Reliability**: ACID transactions for financial operations with retry logic

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────┐   │
│  │ IVR System   │  │ WhatsApp Bot   │  │ Web Dashboard    │   │
│  │ (Exotel)     │  │ (Gupshup)      │  │ (React)          │   │
│  └──────────────┘  └────────────────┘  └──────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS/REST
┌────────────────────────┴────────────────────────────────────────┐
│                     API GATEWAY LAYER                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ AWS API Gateway OR FastAPI Direct                        │  │
│  │ • Request routing                                        │  │
│  │ • Rate limiting                                          │  │
│  │ • CORS handling                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────────┐
│                   APPLICATION LAYER                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ FastAPI Application (Python 3.11+)                       │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │ API Endpoints (Routers)                            │ │  │
│  │  │ • /farmers  • /plots  • /transactions              │ │  │
│  │  │ • /buyers   • /processors  • /fpos                 │ │  │
│  │  │ • /sessions • /auth  • /health                     │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │ Middleware                                         │ │  │
│  │  │ • Authentication (JWT validation)                  │ │  │
│  │  │ • Authorization (FPO scope enforcement)            │ │  │
│  │  │ • Request logging                                  │ │  │
│  │  │ • Error handling                                   │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │ Business Logic Layer                               │ │  │
│  │  │ • FarmerService  • PlotService                     │ │  │
│  │  │ • TransactionService  • SessionService             │ │  │
│  │  │ • AuthService  • AuditService                      │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │ Data Access Layer (Repositories)                   │ │  │
│  │  │ • SQLAlchemy ORM models                            │ │  │
│  │  │ • Repository pattern for data access               │ │  │
│  │  │ • Transaction management                           │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────────┐
│                      DATA LAYER                                  │
│  ┌─────────────────────────┐  ┌──────────────────────────────┐ │
│  │ PostgreSQL (RDS)        │  │ Redis (ElastiCache)          │ │
│  │ • Farmers               │  │ • IVR sessions (TTL 30min)   │ │
│  │ • Plots                 │  │ • Price cache (TTL 1hr)      │ │
│  │ • Transactions          │  │ • Rate limiting counters     │ │
│  │ • Transaction_Audit     │  │                              │ │
│  │ • Buyers                │  │                              │ │
│  │ • Processors            │  │                              │ │
│  │ • FPOs                  │  │                              │ │
│  │ • Coordinators          │  │                              │ │
│  │ • Audit_Logs            │  │                              │ │
│  └─────────────────────────┘  └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Deployment Options

The system supports two deployment architectures:

**Option 1: AWS Lambda + API Gateway**
- API endpoints deployed as Lambda functions
- API Gateway handles routing and rate limiting
- Best for: Variable load, cost optimization
- Cold start mitigation: Provisioned concurrency for critical endpoints

**Option 2: ECS Fargate**
- FastAPI application runs as containerized service
- Application Load Balancer for routing
- Best for: Consistent load, lower latency requirements
- Auto-scaling based on CPU/memory metrics

Both options share the same RDS PostgreSQL and ElastiCache Redis instances.

## Components and Interfaces

### 1. API Endpoints

#### Farmer Management

```python
# Create farmer
POST /api/v1/farmers
Request: {
  "name": str,
  "phone": str,  # 10-digit Indian mobile number
  "fpo_id": int,
  "village": str,
  "language_preference": str  # "hi", "mr", etc.
}
Response: {
  "id": int,
  "name": str,
  "phone": str,
  "fpo_id": int,
  "village": str,
  "language_preference": str,
  "created_at": datetime,
  "updated_at": datetime
}

# Get farmer by ID
GET /api/v1/farmers/{farmer_id}
Response: Farmer object

# List farmers (with pagination and filtering)
GET /api/v1/farmers?fpo_id={fpo_id}&page={page}&size={size}&village={village}
Response: {
  "items": [Farmer],
  "total": int,
  "page": int,
  "size": int,
  "pages": int
}

# Update farmer
PUT /api/v1/farmers/{farmer_id}
Request: Partial Farmer object
Response: Updated Farmer object

# Delete farmer (soft delete)
DELETE /api/v1/farmers/{farmer_id}
Response: 204 No Content
```

#### Plot Management

```python
# Create plot
POST /api/v1/plots
Request: {
  "farmer_id": int,
  "area_acres": float,
  "latitude": float,
  "longitude": float,
  "soil_type": str,  # "loamy", "clay", "sandy", etc.
  "water_source": str,  # "rainfed", "irrigated", "drip"
  "survey_number": str  # Optional government survey number
}
Response: Plot object with id

# Get plots for a farmer
GET /api/v1/plots?farmer_id={farmer_id}
Response: [Plot]

# Update plot
PUT /api/v1/plots/{plot_id}
Request: Partial Plot object
Response: Updated Plot object
```

#### Transaction Management

```python
# Create transaction
POST /api/v1/transactions
Request: {
  "farmer_id": int,
  "plot_id": int,
  "crop_type": str,
  "quantity_kg": float,
  "price_per_kg": float,
  "buyer_id": int,
  "transaction_type": str,  # "fresh_market", "processing"
  "payment_method": str,  # "upi", "cash", "bank_transfer"
  "confirmation_audio_url": str  # S3 URL of farmer confirmation
}
Response: Transaction object with id and status "pending"

# Get transaction by ID
GET /api/v1/transactions/{transaction_id}
Response: Transaction object with full audit trail

# Update transaction status
PUT /api/v1/transactions/{transaction_id}/status
Request: {
  "status": str,  # "confirmed", "completed", "payment_received", "disputed"
  "notes": str,
  "updated_by": str  # User/system identifier
}
Response: Updated Transaction with new audit entry

# List transactions with filtering
GET /api/v1/transactions?farmer_id={id}&status={status}&from_date={date}&to_date={date}
Response: Paginated list of transactions

# Get transaction audit trail
GET /api/v1/transactions/{transaction_id}/audit
Response: [AuditEntry] ordered by timestamp
```

#### Session Management

```python
# Create IVR session
POST /api/v1/sessions
Request: {
  "phone": str,
  "session_type": str,  # "sell", "query", "confirmation"
  "initial_data": dict  # Optional context data
}
Response: {
  "session_id": str,  # UUID
  "expires_at": datetime,
  "state": dict
}

# Get session
GET /api/v1/sessions/{session_id}
Response: Session object or 404 if expired

# Update session state
PUT /api/v1/sessions/{session_id}
Request: {
  "state": dict,  # Merge with existing state
  "extend_ttl": bool  # Reset TTL to 30 minutes
}
Response: Updated Session object

# Delete session (explicit cleanup)
DELETE /api/v1/sessions/{session_id}
Response: 204 No Content
```

#### Authentication

```python
# Login
POST /api/v1/auth/login
Request: {
  "username": str,
  "password": str
}
Response: {
  "access_token": str,  # JWT token
  "token_type": "bearer",
  "expires_in": int,  # seconds
  "user": {
    "id": int,
    "username": str,
    "role": str,
    "fpo_id": int
  }
}

# Refresh token
POST /api/v1/auth/refresh
Request: {
  "refresh_token": str
}
Response: New access token

# Password reset request
POST /api/v1/auth/password-reset
Request: {
  "phone": str
}
Response: 200 OK (sends OTP via SMS)

# Password reset confirm
POST /api/v1/auth/password-reset/confirm
Request: {
  "phone": str,
  "otp": str,
  "new_password": str
}
Response: 200 OK
```

#### Health and Monitoring

```python
# Health check
GET /api/v1/health
Response: {
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": datetime
}

# Metrics
GET /api/v1/metrics
Response: {
  "requests_total": int,
  "requests_per_second": float,
  "error_rate": float,
  "avg_response_time_ms": float,
  "active_sessions": int
}
```

### 2. Business Logic Services

#### TransactionService

```python
class TransactionService:
    """Handles transaction creation and lifecycle management"""
    
    def create_transaction(
        self,
        farmer_id: int,
        transaction_data: TransactionCreate,
        created_by: str
    ) -> Transaction:
        """
        Creates a new transaction with initial audit entry.
        Validates farmer exists, buyer exists, and prices are positive.
        Executes within database transaction for atomicity.
        """
        
    def update_status(
        self,
        transaction_id: int,
        new_status: str,
        notes: str,
        updated_by: str
    ) -> Transaction:
        """
        Updates transaction status and creates audit entry.
        Validates status transition is allowed.
        Executes within database transaction.
        """
        
    def get_transaction_with_audit(
        self,
        transaction_id: int,
        requesting_fpo_id: int
    ) -> TransactionWithAudit:
        """
        Retrieves transaction with full audit trail.
        Enforces FPO scope - only returns if transaction belongs to FPO.
        """
        
    def calculate_farmer_revenue(
        self,
        farmer_id: int,
        from_date: date,
        to_date: date
    ) -> dict:
        """
        Calculates total revenue for farmer in date range.
        Only includes transactions with status "payment_received".
        """
```

#### SessionService

```python
class SessionService:
    """Manages IVR session state in Redis"""
    
    def create_session(
        self,
        phone: str,
        session_type: str,
        initial_data: dict = None
    ) -> Session:
        """
        Creates new session in Redis with 30-minute TTL.
        Generates UUID session_id.
        """
        
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Retrieves session from Redis.
        Returns None if expired or not found.
        """
        
    def update_session(
        self,
        session_id: str,
        state_updates: dict,
        extend_ttl: bool = True
    ) -> Session:
        """
        Merges state_updates into existing session state.
        Optionally resets TTL to 30 minutes.
        """
        
    def delete_session(self, session_id: str) -> bool:
        """Explicitly removes session from Redis"""
```

#### AuthService

```python
class AuthService:
    """Handles authentication and authorization"""
    
    def authenticate(
        self,
        username: str,
        password: str
    ) -> Optional[User]:
        """
        Validates credentials against hashed password.
        Returns User object if valid, None otherwise.
        Logs authentication attempt.
        """
        
    def create_access_token(
        self,
        user: User,
        expires_delta: timedelta = None
    ) -> str:
        """
        Creates JWT token with user claims.
        Default expiration: 24 hours.
        """
        
    def verify_token(self, token: str) -> Optional[dict]:
        """
        Validates JWT token signature and expiration.
        Returns decoded claims if valid, None otherwise.
        """
        
    def enforce_fpo_scope(
        self,
        user: User,
        resource_fpo_id: int
    ) -> bool:
        """
        Verifies user has access to resource based on FPO membership.
        Raises PermissionError if access denied.
        """
```

#### AuditService

```python
class AuditService:
    """Handles audit logging for all system actions"""
    
    def log_action(
        self,
        entity_type: str,
        entity_id: int,
        action: str,  # "create", "update", "delete"
        user_id: str,
        changes: dict = None
    ) -> AuditLog:
        """
        Creates audit log entry with timestamp.
        Stores old and new values for updates.
        """
        
    def log_transaction_status_change(
        self,
        transaction_id: int,
        old_status: str,
        new_status: str,
        user_id: str,
        notes: str
    ) -> TransactionAudit:
        """
        Creates transaction-specific audit entry.
        Stored in separate transaction_audit table for immutability.
        """
        
    def query_audit_logs(
        self,
        entity_type: str = None,
        entity_id: int = None,
        user_id: str = None,
        from_date: datetime = None,
        to_date: datetime = None
    ) -> List[AuditLog]:
        """Queries audit logs with filtering"""
```

## Data Models

### Database Schema

```sql
-- FPO table
CREATE TABLE fpos (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    state VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    registration_number VARCHAR(100) UNIQUE,
    member_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Coordinators table
CREATE TABLE coordinators (
    id SERIAL PRIMARY KEY,
    fpo_id INTEGER NOT NULL REFERENCES fpos(id),
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(10) NOT NULL,
    role VARCHAR(50) DEFAULT 'coordinator',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Farmers table
CREATE TABLE farmers (
    id SERIAL PRIMARY KEY,
    fpo_id INTEGER NOT NULL REFERENCES fpos(id),
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(10) NOT NULL,
    village VARCHAR(255),
    language_preference VARCHAR(10) DEFAULT 'hi',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(fpo_id, phone)
);

-- Plots table
CREATE TABLE plots (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER NOT NULL REFERENCES farmers(id),
    area_acres DECIMAL(10, 2) NOT NULL CHECK (area_acres > 0),
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    soil_type VARCHAR(50),
    water_source VARCHAR(50),
    survey_number VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Buyers table
CREATE TABLE buyers (
    id SERIAL PRIMARY KEY,
    fpo_id INTEGER NOT NULL REFERENCES fpos(id),
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(10) NOT NULL,
    whatsapp_number VARCHAR(15),
    business_name VARCHAR(255),
    location VARCHAR(255),
    verification_status VARCHAR(50) DEFAULT 'pending',
    reliability_score DECIMAL(3, 2) DEFAULT 5.0 CHECK (reliability_score >= 0 AND reliability_score <= 5),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Processors table
CREATE TABLE processors (
    id SERIAL PRIMARY KEY,
    fpo_id INTEGER NOT NULL REFERENCES fpos(id),
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(10) NOT NULL,
    whatsapp_number VARCHAR(15),
    business_name VARCHAR(255),
    location VARCHAR(255),
    processing_types TEXT[],  -- Array of processing types: "paste", "dried", "powder"
    weekly_capacity_kg DECIMAL(10, 2),
    contract_rate_min DECIMAL(10, 2),
    contract_rate_max DECIMAL(10, 2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transactions table (immutable core data)
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER NOT NULL REFERENCES farmers(id),
    plot_id INTEGER REFERENCES plots(id),
    crop_type VARCHAR(100) NOT NULL,
    quantity_kg DECIMAL(10, 2) NOT NULL CHECK (quantity_kg > 0),
    price_per_kg DECIMAL(10, 2) NOT NULL CHECK (price_per_kg > 0),
    total_amount DECIMAL(12, 2) GENERATED ALWAYS AS (quantity_kg * price_per_kg) STORED,
    buyer_id INTEGER REFERENCES buyers(id),
    processor_id INTEGER REFERENCES processors(id),
    transaction_type VARCHAR(50) NOT NULL,  -- "fresh_market", "processing"
    payment_method VARCHAR(50),
    confirmation_audio_url TEXT,
    current_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255) NOT NULL,
    CHECK (buyer_id IS NOT NULL OR processor_id IS NOT NULL)
);

-- Transaction audit trail (append-only)
CREATE TABLE transaction_audit (
    id SERIAL PRIMARY KEY,
    transaction_id INTEGER NOT NULL REFERENCES transactions(id),
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    notes TEXT,
    changed_by VARCHAR(255) NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- General audit logs
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(100) NOT NULL,
    entity_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_farmers_fpo ON farmers(fpo_id);
CREATE INDEX idx_farmers_phone ON farmers(phone);
CREATE INDEX idx_plots_farmer ON plots(farmer_id);
CREATE INDEX idx_transactions_farmer ON transactions(farmer_id);
CREATE INDEX idx_transactions_status ON transactions(current_status);
CREATE INDEX idx_transactions_created ON transactions(created_at);
CREATE INDEX idx_transaction_audit_txn ON transaction_audit(transaction_id);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
```

### SQLAlchemy Models

```python
from sqlalchemy import Column, Integer, String, Decimal, Boolean, TIMESTAMP, ForeignKey, CheckConstraint, ARRAY, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class FPO(Base):
    __tablename__ = "fpos"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    state = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    registration_number = Column(String(100), unique=True)
    member_count = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    farmers = relationship("Farmer", back_populates="fpo")
    coordinators = relationship("Coordinator", back_populates="fpo")
    buyers = relationship("Buyer", back_populates="fpo")
    processors = relationship("Processor", back_populates="fpo")

class Farmer(Base):
    __tablename__ = "farmers"
    
    id = Column(Integer, primary_key=True)
    fpo_id = Column(Integer, ForeignKey("fpos.id"), nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(10), nullable=False)
    village = Column(String(255))
    language_preference = Column(String(10), default="hi")
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    fpo = relationship("FPO", back_populates="farmers")
    plots = relationship("Plot", back_populates="farmer")
    transactions = relationship("Transaction", back_populates="farmer")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False)
    plot_id = Column(Integer, ForeignKey("plots.id"))
    crop_type = Column(String(100), nullable=False)
    quantity_kg = Column(Decimal(10, 2), nullable=False)
    price_per_kg = Column(Decimal(10, 2), nullable=False)
    buyer_id = Column(Integer, ForeignKey("buyers.id"))
    processor_id = Column(Integer, ForeignKey("processors.id"))
    transaction_type = Column(String(50), nullable=False)
    payment_method = Column(String(50))
    confirmation_audio_url = Column(Text)
    current_status = Column(String(50), nullable=False, default="pending")
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    created_by = Column(String(255), nullable=False)
    
    # Relationships
    farmer = relationship("Farmer", back_populates="transactions")
    plot = relationship("Plot")
    buyer = relationship("Buyer")
    processor = relationship("Processor")
    audit_trail = relationship("TransactionAudit", back_populates="transaction", order_by="TransactionAudit.changed_at")
    
    __table_args__ = (
        CheckConstraint("quantity_kg > 0", name="check_quantity_positive"),
        CheckConstraint("price_per_kg > 0", name="check_price_positive"),
        CheckConstraint("buyer_id IS NOT NULL OR processor_id IS NOT NULL", name="check_buyer_or_processor"),
    )

class TransactionAudit(Base):
    __tablename__ = "transaction_audit"
    
    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    old_status = Column(String(50))
    new_status = Column(String(50), nullable=False)
    notes = Column(Text)
    changed_by = Column(String(255), nullable=False)
    changed_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="audit_trail")
```

### Redis Session Schema

```python
# Session stored as JSON in Redis with key pattern: session:{session_id}
{
    "session_id": "uuid-string",
    "phone": "9876543210",
    "session_type": "sell",  # "sell", "query", "confirmation"
    "state": {
        "current_step": "crop_selection",
        "collected_data": {
            "farmer_id": 123,
            "crop_type": "tomato",
            "estimated_quantity": 2500
        },
        "context": {
            "language": "hi",
            "retry_count": 0
        }
    },
    "created_at": "2024-01-15T10:30:00Z",
    "expires_at": "2024-01-15T11:00:00Z"
}

# TTL: 1800 seconds (30 minutes)
```


## Error Handling

### Error Response Format

All API errors follow a consistent JSON structure:

```python
{
    "error": {
        "code": str,  # Machine-readable error code
        "message": str,  # Human-readable error message
        "details": dict,  # Optional additional context
        "timestamp": datetime,
        "request_id": str  # For tracing
    }
}
```

### Error Categories

#### Validation Errors (400 Bad Request)

```python
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Request validation failed",
        "details": {
            "field": "phone",
            "reason": "Phone number must be exactly 10 digits"
        }
    }
}
```

#### Authentication Errors (401 Unauthorized)

```python
{
    "error": {
        "code": "AUTHENTICATION_FAILED",
        "message": "Invalid or expired token"
    }
}
```

#### Authorization Errors (403 Forbidden)

```python
{
    "error": {
        "code": "PERMISSION_DENIED",
        "message": "User does not have access to this FPO's data"
    }
}
```

#### Not Found Errors (404 Not Found)

```python
{
    "error": {
        "code": "RESOURCE_NOT_FOUND",
        "message": "Farmer with id 123 not found"
    }
}
```

#### Conflict Errors (409 Conflict)

```python
{
    "error": {
        "code": "DUPLICATE_RESOURCE",
        "message": "Farmer with phone 9876543210 already exists in this FPO"
    }
}
```

#### Server Errors (500 Internal Server Error)

```python
{
    "error": {
        "code": "INTERNAL_ERROR",
        "message": "An unexpected error occurred",
        "request_id": "req_abc123"  # For support lookup
    }
}
```

### Retry Logic

#### Database Connection Failures

```python
class DatabaseRetryPolicy:
    """Exponential backoff for database connection failures"""
    
    max_retries = 3
    base_delay = 0.1  # seconds
    max_delay = 2.0  # seconds
    
    def execute_with_retry(self, operation):
        for attempt in range(self.max_retries):
            try:
                return operation()
            except OperationalError as e:
                if attempt == self.max_retries - 1:
                    raise
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                time.sleep(delay)
```

#### Redis Connection Failures

```python
class RedisRetryPolicy:
    """Graceful degradation for Redis failures"""
    
    def get_session(self, session_id: str) -> Optional[Session]:
        try:
            return redis_client.get(session_id)
        except RedisConnectionError:
            logger.error("Redis unavailable, session lookup failed")
            # Return None to indicate session not found
            # Caller should handle by creating new session or returning error
            return None
```

### Circuit Breaker Pattern

For external service calls (future integrations):

```python
class CircuitBreaker:
    """Prevents cascading failures from external service outages"""
    
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    def call(self, operation):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half_open"
            else:
                raise CircuitBreakerOpenError("Service unavailable")
        
        try:
            result = operation()
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            raise
```

### Health Checks

```python
@app.get("/api/v1/health")
async def health_check():
    """
    Comprehensive health check for all dependencies.
    Returns 200 if all healthy, 503 if any component unhealthy.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Check database
    try:
        db.execute("SELECT 1")
        health_status["components"]["database"] = "healthy"
    except Exception as e:
        health_status["components"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check Redis
    try:
        redis_client.ping()
        health_status["components"]["redis"] = "healthy"
    except Exception as e:
        health_status["components"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)
```


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property Reflection

After analyzing all acceptance criteria, several properties were identified as redundant or combinable:

- CRUD operations (4.1-4.4) can be combined into comprehensive properties that test create-read-update-delete round trips for all entity types
- Validation properties (9.1-9.8) can be consolidated into general validation properties that apply to all entity types
- Audit logging properties (10.1-10.6) can be combined into properties that verify logging happens for all operations
- Session management properties (6.1-6.7) can be consolidated into properties about session lifecycle

The following properties represent the minimal set needed to verify system correctness without redundancy.

### Core API Properties

Property 1: Request validation consistency
*For any* API endpoint and any invalid request data, the API should return a 400 status code with a structured error response containing an error code and message.
**Validates: Requirements 1.2, 1.4**

Property 2: UTF-8 encoding round trip
*For any* text field and any valid UTF-8 string (including Hindi characters), storing the string and retrieving it should return an equivalent string.
**Validates: Requirements 1.3**

Property 3: Request logging completeness
*For any* API request, an audit log entry should be created with timestamp, request identifier, and endpoint information.
**Validates: Requirements 1.5**

### Data Integrity Properties

Property 4: Foreign key constraint enforcement
*For any* entity with a foreign key reference, attempting to create the entity with a non-existent foreign key value should be rejected by the database.
**Validates: Requirements 2.7**

Property 5: Multi-tenancy data isolation
*For any* FPO and any entity type, querying entities for that FPO should only return entities associated with that FPO, never entities from other FPOs.
**Validates: Requirements 2.8**

Property 6: Required field validation
*For any* entity type and any required field, attempting to create an entity with that field missing should return a validation error indicating the missing field.
**Validates: Requirements 9.1, 9.7**

Property 7: Data type validation
*For any* entity field with a specific type, attempting to create an entity with a value of the wrong type should return a validation error.
**Validates: Requirements 9.2**

Property 8: Phone number format validation
*For any* phone number field, attempting to store a value that is not exactly 10 digits should return a validation error.
**Validates: Requirements 9.3**

Property 9: Positive number validation
*For any* quantity or price field, attempting to store a negative or zero value should return a validation error.
**Validates: Requirements 9.4**

Property 10: Coordinate range validation
*For any* latitude/longitude field, attempting to store values outside valid ranges (latitude: -90 to 90, longitude: -180 to 180) should return a validation error.
**Validates: Requirements 9.5**

Property 11: Validation error message completeness
*For any* validation failure, the error response should include the field name and a description of why validation failed.
**Validates: Requirements 9.6**

Property 12: Unique constraint enforcement
*For any* field with a unique constraint within an FPO (such as phone numbers), attempting to create a second entity with the same value should be rejected.
**Validates: Requirements 9.8**

### Authentication and Authorization Properties

Property 13: Credential validation
*For any* coordinator credentials, authentication should succeed if and only if the username exists and the password matches the stored hash.
**Validates: Requirements 3.1**

Property 14: JWT token structure
*For any* successful authentication, the issued JWT token should contain user claims (user_id, fpo_id, role) and an expiration time.
**Validates: Requirements 3.2**

Property 15: Token validation
*For any* API request with a JWT token, the request should be accepted if and only if the token has a valid signature and has not expired.
**Validates: Requirements 3.3, 3.5**

Property 16: FPO scope enforcement
*For any* coordinator and any resource, the coordinator should be able to access the resource if and only if the resource belongs to the coordinator's FPO.
**Validates: Requirements 3.4**

### CRUD Operation Properties

Property 17: Create-read round trip
*For any* entity type and any valid entity data, creating the entity and then reading it back should return data equivalent to what was created.
**Validates: Requirements 4.1, 4.2**

Property 18: Update persistence
*For any* existing entity and any valid update data, updating the entity and then reading it back should return data reflecting the updates.
**Validates: Requirements 4.3**

Property 19: Delete effectiveness
*For any* existing entity, deleting the entity should result in subsequent read attempts returning a not-found error or the entity marked as inactive.
**Validates: Requirements 4.4**

Property 20: Pagination correctness
*For any* list endpoint with N total entities, requesting page size S and offset O should return exactly min(S, N-O) entities, and the union of all pages should equal the complete set.
**Validates: Requirements 4.5**

Property 21: Filtering correctness
*For any* list endpoint and any filter criteria, all returned entities should match the filter criteria, and no matching entities should be excluded.
**Validates: Requirements 4.6**

Property 22: Sorting correctness
*For any* list endpoint and any sort field, returned entities should be ordered according to the sort field in the specified direction (ascending or descending).
**Validates: Requirements 4.6**

Property 23: Constraint violation error messages
*For any* CRUD operation that violates a database constraint, the error response should include a description of which constraint was violated.
**Validates: Requirements 4.7**

### Transaction Ledger Properties

Property 24: Transaction uniqueness and timestamping
*For any* transaction creation, the transaction should be assigned a unique identifier and a timestamp, and no two transactions should have the same identifier.
**Validates: Requirements 5.1**

Property 25: Transaction immutability
*For any* existing transaction record, attempting to modify or delete the record should fail, preserving the original data.
**Validates: Requirements 5.4**

Property 26: Audit trail append-only
*For any* transaction status update, a new audit entry should be created without modifying any existing audit entries, and the audit trail should be ordered by timestamp.
**Validates: Requirements 5.5, 5.6**

Property 27: Transaction history filtering
*For any* transaction query with filters (farmer, date range, status), all returned transactions should match the filter criteria, and no matching transactions should be excluded.
**Validates: Requirements 5.7**

### Session Management Properties

Property 28: Session uniqueness
*For any* session creation, the session should be assigned a unique session identifier, and no two active sessions should have the same identifier.
**Validates: Requirements 6.1**

Property 29: Session TTL enforcement
*For any* session, accessing the session after 30 minutes without updates should return a not-found result, indicating the session has expired.
**Validates: Requirements 6.3, 6.5**

Property 30: Session state persistence
*For any* session and any state updates, updating the session state and then retrieving the session should return the updated state.
**Validates: Requirements 6.4, 6.7**

Property 31: Session TTL reset on update
*For any* session that is updated before expiration, the session should remain accessible for 30 minutes after the update.
**Validates: Requirements 6.7**

### ACID Transaction Properties

Property 32: Multi-operation atomicity
*For any* sequence of database operations within a transaction, if any operation fails, then all operations should be rolled back and no partial changes should be visible.
**Validates: Requirements 7.1, 7.2**

Property 33: Transaction isolation
*For any* two concurrent transactions T1 and T2, neither transaction should see uncommitted changes from the other transaction.
**Validates: Requirements 7.3**

Property 34: Payment update atomicity
*For any* payment status update with related balance changes, either all changes should be committed together or none should be committed.
**Validates: Requirements 7.6**

### Caching Properties

Property 35: Cache consistency
*For any* cached data, if the underlying data is updated, then subsequent reads should return the updated data (either from cache after invalidation or from database).
**Validates: Requirements 8.5**

### Audit Logging Properties

Property 36: CRUD operation logging
*For any* entity creation, update, or deletion, an audit log entry should be created with the user identifier, timestamp, entity type, entity ID, and action type.
**Validates: Requirements 10.1**

Property 37: Authentication attempt logging
*For any* authentication attempt (success or failure), an audit log entry should be created with the username, timestamp, and result.
**Validates: Requirements 10.2**

Property 38: Transaction status change logging
*For any* transaction status change, an audit log entry should be created with the transaction ID, old status, new status, timestamp, and user identifier.
**Validates: Requirements 10.3**

Property 39: Farmer confirmation logging
*For any* farmer confirmation, an audit log entry should be created with the farmer ID, transaction ID, audio reference URL, and timestamp.
**Validates: Requirements 10.4**

Property 40: Audit log schema consistency
*For any* audit log entry, the entry should contain a consistent set of fields (entity_type, entity_id, action, user_id, timestamp) regardless of the type of action being logged.
**Validates: Requirements 10.5**

Property 41: Audit log query filtering
*For any* audit log query with filters (entity type, user, date range, action type), all returned logs should match the filter criteria, and no matching logs should be excluded.
**Validates: Requirements 10.6**

### Error Handling Properties

Property 42: Database connection retry with backoff
*For any* database connection failure, the system should retry the connection with exponentially increasing delays (up to a maximum) before giving up.
**Validates: Requirements 11.1**

Property 43: Unexpected error logging and response
*For any* unexpected error, the system should log the full error stack trace and return a generic error message to the client (not exposing internal details).
**Validates: Requirements 11.3**

Property 44: Circuit breaker state transitions
*For any* external service with a circuit breaker, after N consecutive failures, the circuit should open and reject requests without calling the service, and after a timeout period, the circuit should transition to half-open to test recovery.
**Validates: Requirements 11.6**

## Testing Strategy

The Backend Foundation & Data Layer will be tested using a dual approach combining unit tests and property-based tests to ensure comprehensive coverage.

### Testing Approach

**Unit Tests**: Verify specific examples, edge cases, and integration points
- Specific API endpoint examples (e.g., creating a farmer with valid data)
- Edge cases (e.g., expired tokens, missing required fields)
- Error conditions (e.g., database connection failures, constraint violations)
- Integration between components (e.g., authentication middleware with endpoints)

**Property-Based Tests**: Verify universal properties across all inputs
- Generate random valid and invalid data for all entity types
- Test properties across many iterations (minimum 100 per property)
- Verify invariants hold regardless of input values
- Catch edge cases that might not be considered in unit tests

Together, these approaches provide comprehensive coverage: unit tests catch concrete bugs in specific scenarios, while property tests verify general correctness across the input space.

### Property-Based Testing Configuration

**Framework**: Use `hypothesis` for Python property-based testing

**Configuration**:
- Minimum 100 iterations per property test (due to randomization)
- Each property test must reference its design document property
- Tag format: `# Feature: backend-foundation-data-layer, Property {number}: {property_text}`

**Example Property Test Structure**:

```python
from hypothesis import given, strategies as st
import pytest

# Feature: backend-foundation-data-layer, Property 17: Create-read round trip
@given(
    name=st.text(min_size=1, max_size=255),
    phone=st.from_regex(r'[0-9]{10}', fullmatch=True),
    village=st.text(min_size=1, max_size=255)
)
@pytest.mark.property_test
def test_farmer_create_read_round_trip(name, phone, village, test_fpo, api_client):
    """
    For any valid farmer data, creating the farmer and then reading it back
    should return data equivalent to what was created.
    """
    # Create farmer
    create_response = api_client.post(
        "/api/v1/farmers",
        json={
            "name": name,
            "phone": phone,
            "fpo_id": test_fpo.id,
            "village": village,
            "language_preference": "hi"
        }
    )
    assert create_response.status_code == 201
    farmer_id = create_response.json()["id"]
    
    # Read farmer back
    read_response = api_client.get(f"/api/v1/farmers/{farmer_id}")
    assert read_response.status_code == 200
    farmer_data = read_response.json()
    
    # Verify data matches
    assert farmer_data["name"] == name
    assert farmer_data["phone"] == phone
    assert farmer_data["village"] == village
    assert farmer_data["fpo_id"] == test_fpo.id
```

### Test Organization

```
tests/
├── unit/
│   ├── test_api_endpoints.py
│   ├── test_auth_service.py
│   ├── test_transaction_service.py
│   ├── test_session_service.py
│   └── test_audit_service.py
├── property/
│   ├── test_crud_properties.py
│   ├── test_validation_properties.py
│   ├── test_auth_properties.py
│   ├── test_transaction_properties.py
│   ├── test_session_properties.py
│   └── test_audit_properties.py
├── integration/
│   ├── test_api_integration.py
│   ├── test_database_integration.py
│   └── test_redis_integration.py
└── conftest.py  # Shared fixtures
```

### Test Data Generators

For property-based tests, we'll use Hypothesis strategies to generate valid test data:

```python
from hypothesis import strategies as st

# Farmer data generator
farmer_strategy = st.fixed_dictionaries({
    "name": st.text(min_size=1, max_size=255, alphabet=st.characters(blacklist_categories=('Cs',))),
    "phone": st.from_regex(r'[0-9]{10}', fullmatch=True),
    "village": st.text(min_size=1, max_size=255),
    "language_preference": st.sampled_from(["hi", "mr", "te", "en"])
})

# Transaction data generator
transaction_strategy = st.fixed_dictionaries({
    "crop_type": st.sampled_from(["tomato", "onion", "potato", "chili", "wheat"]),
    "quantity_kg": st.floats(min_value=0.1, max_value=10000.0),
    "price_per_kg": st.floats(min_value=0.1, max_value=1000.0),
    "transaction_type": st.sampled_from(["fresh_market", "processing"]),
    "payment_method": st.sampled_from(["upi", "cash", "bank_transfer"])
})

# Invalid data generators for validation testing
invalid_phone_strategy = st.one_of(
    st.text(min_size=0, max_size=9),  # Too short
    st.text(min_size=11, max_size=20),  # Too long
    st.from_regex(r'[a-zA-Z]{10}', fullmatch=True),  # Non-numeric
)

invalid_quantity_strategy = st.one_of(
    st.just(0),
    st.floats(max_value=-0.1),  # Negative
)
```

### Coverage Goals

- **Line Coverage**: Minimum 85% for all application code
- **Branch Coverage**: Minimum 80% for all conditional logic
- **Property Coverage**: All 44 correctness properties must have corresponding property tests
- **Integration Coverage**: All API endpoints must have integration tests

### Continuous Integration

All tests will run on every commit:
1. Unit tests (fast feedback, < 1 minute)
2. Property tests (comprehensive, < 5 minutes with 100 iterations)
3. Integration tests (full stack, < 3 minutes)

Property tests will run with increased iterations (1000+) on nightly builds to catch rare edge cases.
