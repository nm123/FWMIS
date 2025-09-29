#!/usr/bin/env python3
"""
FWMIS Monitoring Dashboard

Provides real-time monitoring and diagnostics for the FWMIS application.
Can be run as a standalone script or integrated into the main application.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

# Add scripts to path for imports
current_dir = Path(__file__).parent
scripts_dir = current_dir
project_root = current_dir.parent

# Try different path combinations
for path in [scripts_dir, project_root]:
    if path not in sys.path:
        sys.path.insert(0, str(path))

try:
    from config import get_config
    from Utilities.database_connection import get_database_manager
    from Utilities.metrics import get_health_checker, get_metrics_registry
except ImportError as e:
    print(f"Import error: {e}")
    print("Available paths:", sys.path[:3])
    raise


class MonitoringDashboard:
    """Monitoring dashboard for FWMIS."""

    def __init__(self):
        self.config = get_config()
        self.metrics = get_metrics_registry()
        self.health_checker = get_health_checker()
        self.db_manager = get_database_manager()

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        # Perform health check
        health_status = self.health_checker.perform_health_check()

        # Get metrics summary
        metrics_summary = self.metrics.get_summary()

        # Get database stats
        db_stats = self.db_manager.get_stats()

        # Get configuration summary
        config_summary = {
            "environment": self.config.environment,
            "debug": self.config.debug,
            "database_path": str(self.config.database.path),
            "log_level": self.config.logging.level,
        }

        return {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy" if health_status.get("overall", False) else "unhealthy",
            "health": health_status,
            "metrics": metrics_summary,
            "database": db_stats,
            "configuration": config_summary,
            "version": self.config.version,
        }

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report."""
        metrics = self.metrics.get_summary()

        # Calculate performance indicators
        total_requests = sum(metrics.get("counters", {}).values())
        avg_response_time = (
            metrics.get("histograms", {})
            .get("fwmis_response_time_seconds", {})
            .get("p95", 0)
        )
        error_rate = 0

        if total_requests > 0:
            total_errors = sum(
                count
                for name, count in metrics.get("counters", {}).items()
                if "errors" in name
            )
            error_rate = (total_errors / total_requests) * 100

        return {
            "timestamp": datetime.now().isoformat(),
            "total_requests": total_requests,
            "average_response_time_p95": avg_response_time,
            "error_rate_percent": error_rate,
            "active_connections": metrics.get("gauges", {}).get(
                "fwmis_active_connections", 0
            ),
            "uptime_seconds": metrics.get("uptime_seconds", 0),
            "performance_score": self._calculate_performance_score(metrics),
        }

    def _calculate_performance_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate a performance score (0-100)."""
        score = 100.0

        # Response time penalties
        avg_response_time = (
            metrics.get("histograms", {})
            .get("fwmis_response_time_seconds", {})
            .get("p95", 0)
        )
        if avg_response_time > 5.0:  # More than 5 seconds
            score -= 30
        elif avg_response_time > 2.0:  # More than 2 seconds
            score -= 15
        elif avg_response_time > 1.0:  # More than 1 second
            score -= 5

        # Error rate penalties
        total_requests = sum(metrics.get("counters", {}).values())
        if total_requests > 0:
            total_errors = sum(
                count
                for name, count in metrics.get("counters", {}).items()
                if "errors" in name
            )
            error_rate = (total_errors / total_requests) * 100
            if error_rate > 10:  # More than 10% errors
                score -= 40
            elif error_rate > 5:  # More than 5% errors
                score -= 20
            elif error_rate > 1:  # More than 1% errors
                score -= 10

        return max(0.0, min(100.0, score))

    def get_business_metrics(self) -> Dict[str, Any]:
        """Get business-specific metrics."""
        metrics = self.metrics.get_summary()
        counters = metrics.get("counters", {})

        return {
            "timestamp": datetime.now().isoformat(),
            "cases_created": counters.get("fwmis_cases_created_total", 0),
            "cases_updated": counters.get("fwmis_cases_updated_total", 0),
            "annexures_processed": counters.get("fwmis_annexures_processed_total", 0),
            "user_actions": counters.get("fwmis_user_actions_total", 0),
            "database_connections": metrics.get("gauges", {}).get(
                "fwmis_active_connections", 0
            ),
        }

    def export_report(self, format: str = "json") -> str:
        """Export monitoring report."""
        report = {
            "system_status": self.get_system_status(),
            "performance": self.get_performance_report(),
            "business_metrics": self.get_business_metrics(),
        }

        if format == "json":
            return json.dumps(report, indent=2, default=str)
        else:
            # Simple text format
            lines = ["FWMIS Monitoring Report", "=" * 50]
            lines.append(f"Generated: {datetime.now().isoformat()}")
            lines.append(f"Status: {report['system_status']['status']}")
            lines.append(
                f"Performance Score: {report['performance']['performance_score']:.1f}/100"
            )
            lines.append(f"Total Requests: {report['performance']['total_requests']}")
            lines.append(
                f"Error Rate: {report['performance']['error_rate_percent']:.2f}%"
            )
            return "\n".join(lines)

    def display_dashboard(self) -> None:
        """Display monitoring dashboard in console."""
        print("\n" + "=" * 60)
        print("🎯 FWMIS MONITORING DASHBOARD")
        print("=" * 60)

        # System Status
        status = self.get_system_status()
        health_status = (
            "🟢 HEALTHY" if status["status"] == "healthy" else "🔴 UNHEALTHY"
        )
        print(f"System Status: {health_status}")
        print(f"Version: {status['version']}")
        print(f"Environment: {status['configuration']['environment']}")

        # Health Checks
        health = status["health"]
        print(f"\nHealth Checks:")
        for service, healthy in health.items():
            if service != "overall":
                status_icon = "✅" if healthy else "❌"
                print(f"  {status_icon} {service}: {'PASS' if healthy else 'FAIL'}")

        # Performance Metrics
        perf = self.get_performance_report()
        print("\nPerformance:")
        print(f"  Total Requests: {perf['total_requests']}")
        print(f"  Avg Response Time (P95): {perf['average_response_time_p95']:.2f}s")
        print(f"  Error Rate: {perf['error_rate_percent']:.2f}%")
        print(f"  Performance Score: {perf['performance_score']:.1f}/100")

        # Business Metrics
        business = self.get_business_metrics()
        print("\nBusiness Metrics:")
        print(f"  Cases Created: {business['cases_created']}")
        print(f"  Cases Updated: {business['cases_updated']}")
        print(f"  Annexures Processed: {business['annexures_processed']}")
        print(f"  User Actions: {business['user_actions']}")

        print("\n" + "=" * 60)


def main():
    """Main entry point for monitoring dashboard."""
    dashboard = MonitoringDashboard()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "status":
            print(dashboard.export_report("json"))
        elif command == "performance":
            print(json.dumps(dashboard.get_performance_report(), indent=2, default=str))
        elif command == "business":
            print(json.dumps(dashboard.get_business_metrics(), indent=2, default=str))
        elif command == "export":
            format_type = sys.argv[2] if len(sys.argv) > 2 else "json"
            print(dashboard.export_report(format_type))
        else:
            print(
                "Usage: python monitoring_dashboard.py [status|performance|business|export [json|text]]"
            )
    else:
        # Interactive dashboard
        dashboard.display_dashboard()


if __name__ == "__main__":
    main()
