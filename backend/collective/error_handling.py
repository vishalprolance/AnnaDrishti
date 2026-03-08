"""
Error handling and graceful degradation for integration points.

This module provides error handling utilities and degradation strategies
to ensure the system continues operating when integration errors occur.
"""

import logging
from typing import Optional, Callable, Any, Dict
from functools import wraps
from datetime import datetime
import traceback


# Configure logger
logger = logging.getLogger(__name__)


class IntegrationError(Exception):
    """Base exception for integration errors"""
    pass


class SellAgentIntegrationError(IntegrationError):
    """Error communicating with Sell Agent"""
    pass


class ProcessAgentIntegrationError(IntegrationError):
    """Error communicating with Process Agent"""
    pass


class DegradedModeError(Exception):
    """System is operating in degraded mode"""
    pass


class ErrorHandler:
    """
    Centralized error handler for integration points.
    
    Provides:
    - Error logging to CloudWatch
    - Graceful degradation strategies
    - Error recovery mechanisms
    """
    
    def __init__(self):
        """Initialize error handler"""
        self.error_count: Dict[str, int] = {}
        self.last_error_time: Dict[str, datetime] = {}
    
    def log_error(
        self,
        error: Exception,
        context: str,
        severity: str = "ERROR",
        additional_info: Dict = None,
    ) -> None:
        """
        Log error with context and additional information.
        
        In production, this would:
        - Log to CloudWatch Logs
        - Send SNS notifications for critical errors
        - Update error metrics in CloudWatch Metrics
        - Trigger alerts based on error thresholds
        
        Args:
            error: Exception that occurred
            context: Context where error occurred (e.g., "sell_agent_integration")
            severity: Error severity (ERROR, WARNING, CRITICAL)
            additional_info: Additional context information
        """
        # Track error count
        self.error_count[context] = self.error_count.get(context, 0) + 1
        self.last_error_time[context] = datetime.now()
        
        # Build error message
        error_msg = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "severity": severity,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_count": self.error_count[context],
            "traceback": traceback.format_exc(),
        }
        
        if additional_info:
            error_msg["additional_info"] = additional_info
        
        # Log to console (in production, log to CloudWatch)
        if severity == "CRITICAL":
            logger.critical(f"CRITICAL ERROR: {context}", extra=error_msg)
        elif severity == "ERROR":
            logger.error(f"ERROR: {context}", extra=error_msg)
        else:
            logger.warning(f"WARNING: {context}", extra=error_msg)
        
        # In production:
        # - Send to CloudWatch Logs
        # - Publish to SNS topic for critical errors
        # - Update CloudWatch Metrics
        # - Trigger PagerDuty/Opsgenie alerts if threshold exceeded
    
    def get_error_stats(self, context: str) -> Dict:
        """
        Get error statistics for a context.
        
        Args:
            context: Context to get stats for
        
        Returns:
            Dictionary with error count and last error time
        """
        return {
            "context": context,
            "error_count": self.error_count.get(context, 0),
            "last_error_time": (
                self.last_error_time[context].isoformat()
                if context in self.last_error_time
                else None
            ),
        }
    
    def should_degrade(self, context: str, threshold: int = 5) -> bool:
        """
        Check if system should enter degraded mode for a context.
        
        Args:
            context: Context to check
            threshold: Error count threshold for degradation
        
        Returns:
            True if should degrade, False otherwise
        """
        return self.error_count.get(context, 0) >= threshold


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """
    Get the global error handler instance.
    
    Returns:
        ErrorHandler singleton instance
    """
    global _error_handler
    
    if _error_handler is None:
        _error_handler = ErrorHandler()
    
    return _error_handler


def handle_integration_error(
    context: str,
    fallback_value: Any = None,
    raise_on_critical: bool = False,
):
    """
    Decorator for handling integration errors with graceful degradation.
    
    Usage:
        @handle_integration_error(context="sell_agent", fallback_value={})
        def call_sell_agent():
            # Integration code that might fail
            pass
    
    Args:
        context: Context identifier for error tracking
        fallback_value: Value to return on error (enables degraded mode)
        raise_on_critical: Whether to raise exception on critical errors
    
    Returns:
        Decorated function with error handling
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = get_error_handler()
            
            try:
                return func(*args, **kwargs)
            
            except Exception as e:
                # Determine severity
                severity = "CRITICAL" if isinstance(e, (
                    SellAgentIntegrationError,
                    ProcessAgentIntegrationError,
                )) else "ERROR"
                
                # Log error
                error_handler.log_error(
                    error=e,
                    context=context,
                    severity=severity,
                    additional_info={
                        "function": func.__name__,
                        "args": str(args),
                        "kwargs": str(kwargs),
                    }
                )
                
                # Check if should degrade
                if error_handler.should_degrade(context):
                    logger.warning(
                        f"Entering degraded mode for {context} "
                        f"(error count: {error_handler.error_count[context]})"
                    )
                
                # Raise or return fallback
                if raise_on_critical and severity == "CRITICAL":
                    raise
                
                if fallback_value is not None:
                    logger.info(f"Returning fallback value for {context}")
                    return fallback_value
                
                raise
        
        return wrapper
    return decorator


class DegradationStrategy:
    """
    Strategies for graceful degradation when integrations fail.
    """
    
    @staticmethod
    def fallback_to_cache(cache_key: str, cache_ttl: int = 300) -> Any:
        """
        Fallback to cached data when integration fails.
        
        Args:
            cache_key: Cache key to retrieve
            cache_ttl: Cache TTL in seconds
        
        Returns:
            Cached data or None
        """
        # In production, implement Redis/ElastiCache lookup
        logger.info(f"Attempting cache fallback for {cache_key}")
        return None
    
    @staticmethod
    def fallback_to_default(default_value: Any) -> Any:
        """
        Fallback to default value when integration fails.
        
        Args:
            default_value: Default value to return
        
        Returns:
            Default value
        """
        logger.info(f"Using default fallback value: {default_value}")
        return default_value
    
    @staticmethod
    def fallback_to_queue(operation: str, data: Dict) -> Dict:
        """
        Queue operation for retry when integration fails.
        
        Args:
            operation: Operation identifier
            data: Operation data
        
        Returns:
            Queue confirmation
        """
        # In production, push to SQS for retry
        logger.info(f"Queuing operation for retry: {operation}")
        return {
            "status": "queued",
            "operation": operation,
            "retry_scheduled": True,
        }
    
    @staticmethod
    def notify_degraded_mode(context: str, error: Exception) -> None:
        """
        Notify operators that system is in degraded mode.
        
        Args:
            context: Context in degraded mode
            error: Error that caused degradation
        """
        # In production:
        # - Send SNS notification
        # - Update CloudWatch dashboard
        # - Trigger PagerDuty alert
        # - Update status page
        
        logger.warning(
            f"DEGRADED MODE: {context} - {str(error)}\n"
            f"System is operating with reduced functionality.\n"
            f"Manual intervention may be required."
        )


def log_to_cloudwatch(
    log_group: str,
    log_stream: str,
    message: str,
    level: str = "INFO",
) -> None:
    """
    Log message to CloudWatch Logs.
    
    In production, this would use boto3 to send logs to CloudWatch.
    For now, logs to console.
    
    Args:
        log_group: CloudWatch log group name
        log_stream: CloudWatch log stream name
        message: Log message
        level: Log level (INFO, WARNING, ERROR, CRITICAL)
    """
    # In production:
    # import boto3
    # logs_client = boto3.client('logs')
    # logs_client.put_log_events(
    #     logGroupName=log_group,
    #     logStreamName=log_stream,
    #     logEvents=[{
    #         'timestamp': int(datetime.now().timestamp() * 1000),
    #         'message': message
    #     }]
    # )
    
    # For now, log to console
    timestamp = datetime.now().isoformat()
    print(f"[CloudWatch] {timestamp} [{level}] {log_group}/{log_stream}: {message}")
