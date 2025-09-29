"""
Application Metrics and Monitoring

Provides comprehensive monitoring capabilities for FWMIS including:
- Performance metrics
- Business metrics
- Error tracking
- System health monitoring

This module imports from specialized metric modules for better organization.
"""

# Re-export for backward compatibility
from .metrics_core import Counter, Gauge, Histogram
from .metrics_registry import (
    MetricsRegistry,
    get_metrics_registry,
    REQUEST_COUNT,
    RESPONSE_TIME,
    ERROR_COUNT,
    ACTIVE_CONNECTIONS,
    DATABASE_QUERY_TIME,
    CASES_CREATED,
    CASES_UPDATED,
    ANNEXURES_PROCESSED,
    USER_ACTIONS
)
from .metrics_collectors import (
    track_request,
    track_database_query,
    StructuredLogger
)
from .health_monitoring import HealthChecker, get_health_checker


# Legacy function for backward compatibility
def get_metrics_registry() -> MetricsRegistry:
    """Get the global metrics registry (legacy function)."""
    from .metrics_registry import get_metrics_registry as _get_registry
    return _get_registry()
