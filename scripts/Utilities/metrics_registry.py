"""
Metrics Registry

Central registry for managing application metrics.
"""

import time
from typing import Any, Dict

from .metrics_core import Counter, Gauge, Histogram


class MetricsRegistry:
    """Registry for all application metrics."""

    def __init__(self):
        self.counters: Dict[str, Counter] = {}
        self.gauges: Dict[str, Gauge] = {}
        self.histograms: Dict[str, Histogram] = {}
        self._start_time = time.time()

    def counter(self, name: str, description: str, labels: Dict[str, str] = None) -> Counter:
        """Get or create a counter."""
        if name not in self.counters:
            self.counters[name] = Counter(name, description, labels=labels or {})
        return self.counters[name]

    def gauge(self, name: str, description: str, labels: Dict[str, str] = None) -> Gauge:
        """Get or create a gauge."""
        if name not in self.gauges:
            self.gauges[name] = Gauge(name, description, labels=labels or {})
        return self.gauges[name]

    def histogram(self, name: str, description: str, labels: Dict[str, str] = None) -> Histogram:
        """Get or create a histogram."""
        if name not in self.histograms:
            self.histograms[name] = Histogram(name, description, labels=labels or {})
        return self.histograms[name]

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics."""
        return {
            "uptime_seconds": time.time() - self._start_time,
            "counters": {name: counter.value for name, counter in self.counters.items()},
            "gauges": {name: gauge.value for name, gauge in self.gauges.items()},
            "histograms": {
                name: {
                    "count": hist.count(),
                    "sum": hist.sum(),
                    "p50": hist.get_percentile(50),
                    "p95": hist.get_percentile(95),
                    "p99": hist.get_percentile(99)
                }
                for name, hist in self.histograms.items()
            }
        }


# Global metrics registry
_metrics_registry = MetricsRegistry()

# Application metrics
REQUEST_COUNT = _metrics_registry.counter(
    "fwmis_requests_total",
    "Total number of requests"
)

RESPONSE_TIME = _metrics_registry.histogram(
    "fwmis_response_time_seconds",
    "Response time in seconds"
)

ERROR_COUNT = _metrics_registry.counter(
    "fwmis_errors_total",
    "Total number of errors"
)

ACTIVE_CONNECTIONS = _metrics_registry.gauge(
    "fwmis_active_connections",
    "Number of active database connections"
)

DATABASE_QUERY_TIME = _metrics_registry.histogram(
    "fwmis_database_query_time_seconds",
    "Database query execution time"
)

# Business metrics
CASES_CREATED = _metrics_registry.counter(
    "fwmis_cases_created_total",
    "Total number of cases created"
)

CASES_UPDATED = _metrics_registry.counter(
    "fwmis_cases_updated_total",
    "Total number of cases updated"
)

ANNEXURES_PROCESSED = _metrics_registry.counter(
    "fwmis_annexures_processed_total",
    "Total number of annexures processed"
)

USER_ACTIONS = _metrics_registry.counter(
    "fwmis_user_actions_total",
    "Total number of user actions"
)


def get_metrics_registry() -> MetricsRegistry:
    """Get the global metrics registry."""
    return _metrics_registry
