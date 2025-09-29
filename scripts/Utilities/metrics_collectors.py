"""
Metrics Collectors

Decorators and functions for collecting application metrics.
"""

import time
from functools import wraps
from typing import Any, Callable, Dict, Optional

from .metrics_core import Histogram
from .metrics_registry import (
    REQUEST_COUNT,
    RESPONSE_TIME,
    ERROR_COUNT,
    DATABASE_QUERY_TIME
)


def track_request(endpoint: str) -> Callable:
    """Decorator to track request metrics."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            # Increment request count
            REQUEST_COUNT.labels["endpoint"] = endpoint
            REQUEST_COUNT.increment()

            try:
                result = func(*args, **kwargs)

                # Record response time
                response_time = time.time() - start_time
                RESPONSE_TIME.labels["endpoint"] = endpoint
                RESPONSE_TIME.observe(response_time)

                return result

            except Exception as e:
                # Record error
                ERROR_COUNT.labels["endpoint"] = endpoint
                ERROR_COUNT.labels["error_type"] = type(e).__name__
                ERROR_COUNT.increment()

                # Record response time for failed requests
                response_time = time.time() - start_time
                RESPONSE_TIME.labels["endpoint"] = endpoint
                RESPONSE_TIME.labels["status"] = "error"
                RESPONSE_TIME.observe(response_time)

                raise

        return wrapper
    return decorator


def track_database_query(query_type: str = "unknown") -> Callable:
    """Decorator to track database query metrics."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)

                # Record query time
                query_time = time.time() - start_time
                DATABASE_QUERY_TIME.labels["query_type"] = query_type
                DATABASE_QUERY_TIME.observe(query_time)

                return result

            except Exception as e:
                # Record failed query time
                query_time = time.time() - start_time
                DATABASE_QUERY_TIME.labels["query_type"] = query_type
                DATABASE_QUERY_TIME.labels["status"] = "error"
                DATABASE_QUERY_TIME.observe(query_time)

                raise

        return wrapper
    return decorator


class StructuredLogger:
    """Structured logging utility."""

    @staticmethod
    def log_case_action(action: str, case_id: int, user_id: Optional[str] = None,
                       extra_data: Optional[Dict[str, Any]] = None) -> None:
        """Log case-related actions with structured data."""
        import logging
        logger = logging.getLogger(__name__)

        log_data = {
            "action": action,
            "case_id": case_id,
            "user_id": user_id,
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "event_type": "case_action"
        }

        if extra_data:
            log_data.update(extra_data)

        logger.info(f"Case action: {action}", extra=log_data)

        # Update metrics
        from .metrics_registry import USER_ACTIONS
        USER_ACTIONS.labels["action"] = action
        USER_ACTIONS.increment()

    @staticmethod
    def log_database_operation(operation: str, table: str, duration: float,
                             success: bool = True, error: Optional[str] = None) -> None:
        """Log database operations with performance data."""
        import logging
        logger = logging.getLogger(__name__)

        log_data = {
            "operation": operation,
            "table": table,
            "duration_seconds": duration,
            "success": success,
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "event_type": "database_operation"
        }

        if error:
            log_data["error"] = error

        if success:
            logger.debug(f"DB operation: {operation} on {table}", extra=log_data)
        else:
            logger.error(f"DB operation failed: {operation} on {table}", extra=log_data)

    @staticmethod
    def log_application_event(event: str, level: str = "info",
                            extra_data: Optional[Dict[str, Any]] = None) -> None:
        """Log application-level events."""
        import logging
        logger = logging.getLogger(__name__)

        log_data = {
            "event": event,
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "event_type": "application_event"
        }

        if extra_data:
            log_data.update(extra_data)

        log_method = getattr(logger, level.lower(), logger.info)
        log_method(f"Application event: {event}", extra=log_data)

    @staticmethod
    def log_performance_metric(metric_name: str, value: float,
                              labels: Optional[Dict[str, str]] = None) -> None:
        """Log performance metrics."""
        import logging
        logger = logging.getLogger(__name__)

        log_data = {
            "metric": metric_name,
            "value": value,
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "event_type": "performance_metric"
        }

        if labels:
            log_data.update(labels)

        logger.info(f"Performance metric: {metric_name} = {value}", extra=log_data)
