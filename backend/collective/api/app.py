"""
FastAPI application for collective selling system
"""

import logging
import time
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Callable

from .inventory import router as inventory_router
from .society import router as society_router
from .demand import router as demand_router
from .processing import router as processing_router
from .allocation import router as allocation_router
from .legacy import router as legacy_router


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Create FastAPI app
app = FastAPI(
    title="Anna Drishti Collective Selling API",
    description="API for collective selling and allocation system",
    version="1.0.0",
    root_path="/demo",  # API Gateway stage path
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable):
    """Log all incoming requests and their processing time"""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"Status: {response.status_code} "
            f"Duration: {process_time:.3f}s"
        )
        
        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Error: {request.method} {request.url.path} "
            f"Duration: {process_time:.3f}s "
            f"Error: {str(e)}"
        )
        raise


# Authentication middleware (placeholder for future implementation)
@app.middleware("http")
async def authenticate_request(request: Request, call_next: Callable):
    """
    Authentication middleware - validates API keys or JWT tokens.
    Currently a placeholder that allows all requests.
    
    In production, implement:
    - API key validation from headers
    - JWT token verification
    - Role-based access control
    """
    # Skip authentication for health check and root endpoints
    if request.url.path in ["/", "/health", "/docs", "/openapi.json"]:
        return await call_next(request)
    
    # TODO: Implement actual authentication
    # Example:
    # api_key = request.headers.get("X-API-Key")
    # if not api_key or not validate_api_key(api_key):
    #     return JSONResponse(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         content={"detail": "Invalid or missing API key"}
    #     )
    
    return await call_next(request)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "path": request.url.path,
            "method": request.method
        }
    )


# HTTP exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper logging"""
    logger.warning(
        f"HTTP exception: {exc.status_code} - {exc.detail} "
        f"Path: {request.url.path}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Include routers
app.include_router(inventory_router)
app.include_router(society_router)
app.include_router(demand_router)
app.include_router(processing_router)
app.include_router(allocation_router)
app.include_router(legacy_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Anna Drishti Collective Selling API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
