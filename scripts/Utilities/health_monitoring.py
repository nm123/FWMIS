"""
Health Monitoring System

Provides health checking capabilities for system monitoring.
"""

import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


class HealthChecker:
    """Application health monitoring."""

    def __init__(self):
        self.last_health_check = datetime.now()
        self.health_status = "healthy"
        self.services_status = {}

    def check_database_connection(self) -> bool:
        """Check database connectivity."""
        try:
            from scripts.Utilities.database_connection import get_database_manager
            db_manager = get_database_manager()

            with db_manager.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def check_file_system(self) -> bool:
        """Check file system accessibility."""
        try:
            from scripts.config import get_config
            config = get_config()

            # Check critical directories
            critical_paths = [
                config.data_dir,
                config.logs_dir,
                config.temp_dir
            ]

            for path in critical_paths:
                if not path.exists():
                    logger.error(f"Critical path missing: {path}")
                    return False

                # Try to write a test file
                test_file = path / ".health_check"
                try:
                    test_file.write_text("health_check")
                    test_file.unlink()
                except Exception as e:
                    logger.error(f"Cannot write to {path}: {e}")
                    return False

            return True

        except Exception as e:
            logger.error(f"File system health check failed: {e}")
            return False

    def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        self.last_health_check = datetime.now()

        checks = {
            "database": self.check_database_connection(),
            "filesystem": self.check_file_system(),
            "overall": True
        }

        # Update overall status
        checks["overall"] = all(checks.values())
        self.health_status = "healthy" if checks["overall"] else "unhealthy"

        # Update services status
        self.services_status.update(checks)

        # Log health check result
        from scripts.Utilities.metrics import StructuredLogger
        StructuredLogger.log_application_event(
            "health_check_completed",
            level="info" if checks["overall"] else "error",
            extra_data={
                "checks": checks,
                "duration_seconds": (datetime.now() - self.last_health_check).total_seconds()
            }
        )

        return checks

    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return {
            "status": self.health_status,
            "last_check": self.last_health_check.isoformat(),
            "services": self.services_status,
            "uptime_seconds": (datetime.now() - datetime.fromtimestamp(__import__('time').time() - (__import__('time').time() - (__import__('psutil').Process().create_time() if 'psutil' in globals() else __import__('time').time())))).total_seconds()
        }


# Global health checker
health_checker = HealthChecker()


def get_health_checker() -> HealthChecker:
    """Get the global health checker."""
    return health_checker
