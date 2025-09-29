"""
Optimization Manager for FWMIS.
Provides easy enable/disable of performance optimizations.
"""

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class OptimizationManager:
    """Manages optimization settings and provides easy enable/disable functionality."""

    def __init__(self):
        # Default: optimizations disabled for day-to-day work
        self.optimization_config = {
            "memory_efficient_imports": False,
            "streaming_excel_exports": False,
            "batch_database_operations": False,
            "performance_monitoring": True,  # Keep monitoring enabled
            "database_indexes": False,
            "adaptive_chunk_sizing": False,
        }

        self.optimization_status = {
            "import_worker": "optimized",  # "original" or "optimized"
            "excel_export": "optimized",  # "original" or "optimized"
            "database_settings": "optimized",  # "original" or "optimized"
        }

    def enable_optimizations(self, optimizations: Optional[Dict[str, bool]] = None):
        """Enable specific optimizations or all optimizations."""
        if optimizations is None:
            optimizations = {key: True for key in self.optimization_config.keys()}

        for optimization, enabled in optimizations.items():
            if optimization in self.optimization_config:
                self.optimization_config[optimization] = enabled
                logger.info(
                    f"Optimization '{optimization}': {'enabled' if enabled else 'disabled'}"
                )
            else:
                logger.warning(f"Unknown optimization: {optimization}")

    def disable_optimizations(self, optimizations: Optional[Dict[str, bool]] = None):
        """Disable specific optimizations or all optimizations."""
        if optimizations is None:
            optimizations = {key: False for key in self.optimization_config.keys()}

        for optimization, enabled in optimizations.items():
            if optimization in self.optimization_config:
                self.optimization_config[optimization] = not enabled
                logger.info(
                    f"Optimization '{optimization}': {'disabled' if not enabled else 'enabled'}"
                )
            else:
                logger.warning(f"Unknown optimization: {optimization}")

    def is_optimization_enabled(self, optimization: str) -> bool:
        """Check if a specific optimization is enabled."""
        return self.optimization_config.get(optimization, False)

    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status."""
        return {
            "config": self.optimization_config.copy(),
            "status": self.optimization_status.copy(),
            "all_enabled": all(self.optimization_config.values()),
        }

    def apply_database_optimizations(self):
        """Apply database optimizations if enabled."""
        if not self.is_optimization_enabled("database_indexes"):
            logger.info("Database optimizations disabled")
            return

        try:
            from scripts.Utilities.optimized_import_utils import (
                create_performance_indexes,
                optimize_database_settings,
            )

            optimize_database_settings()
            create_performance_indexes()
            logger.info("Database optimizations applied successfully")

        except Exception as e:
            logger.error(f"Failed to apply database optimizations: {e}")

    def get_import_worker_class(self):
        """Get the appropriate import worker class based on optimization settings."""
        if self.is_optimization_enabled("memory_efficient_imports"):
            try:
                from scripts.core.optimized_import_worker import OptimizedImportWorker

                return OptimizedImportWorker
            except ImportError:
                logger.warning(
                    "Optimized import worker not available, falling back to original"
                )

        from scripts.core.import_worker import ImportWorker

        return ImportWorker

    def get_excel_exporter_class(self):
        """Get the appropriate Excel exporter class based on optimization settings."""
        if self.is_optimization_enabled("streaming_excel_exports"):
            try:
                from scripts.Utilities.optimized_excel_utils import (
                    StreamingExcelExporter,
                )

                return StreamingExcelExporter
            except ImportError:
                logger.warning(
                    "Optimized Excel exporter not available, falling back to original"
                )

        # Return None to use original pandas-based export
        return None

    def get_optimal_chunk_size(self) -> int:
        """Get optimal chunk size based on optimization settings."""
        if not self.is_optimization_enabled("adaptive_chunk_sizing"):
            return 1000  # Default chunk size

        try:
            from scripts.Utilities.optimized_import_utils import get_optimal_chunk_size

            return get_optimal_chunk_size()
        except ImportError:
            return 1000

    def should_use_streaming(self, data_size: int) -> bool:
        """Determine if streaming should be used based on data size and settings."""
        if not self.is_optimization_enabled("memory_efficient_imports"):
            return False

        # Use streaming for datasets larger than 1000 items
        return data_size > 1000

    def auto_enable_for_large_dataset(
        self, data_size: int, operation_type: str = "import"
    ):
        """Automatically enable optimizations for large datasets."""
        if data_size > 1000:
            logger.info(
                f"Large dataset detected ({data_size} items), enabling optimizations for {operation_type}"
            )

            # Enable relevant optimizations
            optimizations_to_enable = {
                "memory_efficient_imports": True,
                "batch_database_operations": True,
                "adaptive_chunk_sizing": True,
            }

            if operation_type == "export":
                optimizations_to_enable["streaming_excel_exports"] = True

            self.enable_optimizations(optimizations_to_enable)
            return True
        return False

    def get_system_resources_info(self) -> dict:
        """Get current system resource information."""
        try:
            import psutil

            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)

            return {
                "memory_total_gb": round(memory.total / (1024**3), 1),
                "memory_available_gb": round(memory.available / (1024**3), 1),
                "memory_used_percent": memory.percent,
                "cpu_percent": cpu_percent,
                "memory_status": self._get_memory_status(memory.percent),
                "psutil_available": True,
            }
        except ImportError:
            return {
                "memory_total_gb": "Unknown",
                "memory_available_gb": "Unknown",
                "memory_used_percent": "Unknown",
                "cpu_percent": "Unknown",
                "memory_status": "Unknown",
                "psutil_available": False,
            }

    def should_use_streaming(self, data_size: int) -> bool:
        """Determine if streaming should be used based on data size."""
        return data_size > 1000

    def get_optimal_chunk_size(self) -> int:
        """Get optimal chunk size based on current system resources."""
        try:
            import psutil

            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)

            # Adjust chunk size based on available memory
            if available_gb > 4:
                return 1000
            elif available_gb > 2:
                return 500
            else:
                return 250
        except ImportError:
            return 500  # Default chunk size

    def _get_memory_status(self, memory_percent: float) -> str:
        """Get memory status based on usage percentage."""
        if memory_percent < 50:
            return "Good"
        elif memory_percent < 75:
            return "Moderate"
        elif memory_percent < 90:
            return "High"
        else:
            return "Critical"

    def log_optimization_status(self):
        """Log current optimization status."""
        status = self.get_optimization_status()

        logger.info("FWMIS Optimization Status:")
        logger.info("=" * 30)

        for optimization, enabled in status["config"].items():
            status_icon = "[OK]" if enabled else "[OFF]"
            logger.info(
                f"{status_icon} {optimization}: {'enabled' if enabled else 'disabled'}"
            )

        logger.info(
            f"\nOverall Status: {'All optimizations enabled' if status['all_enabled'] else 'Some optimizations disabled'}"
        )

    def create_performance_summary(self) -> str:
        """Create a performance summary report."""
        status = self.get_optimization_status()

        summary = "FWMIS Performance Optimization Summary\n"
        summary += "=" * 40 + "\n\n"

        summary += "Enabled Optimizations:\n"
        for optimization, enabled in status["config"].items():
            if enabled:
                summary += f"  • {optimization} (Active)\n"

        summary += "\nDisabled Optimizations:\n"
        for optimization, enabled in status["config"].items():
            if not enabled:
                summary += f"  • {optimization} (Disabled)\n"

        summary += f"\nOverall Status: {'All optimizations active' if status['all_enabled'] else 'Mixed optimization status'}\n"

        return summary


# Global optimization manager instance
optimization_manager = OptimizationManager()


def get_optimization_manager() -> OptimizationManager:
    """Get the global optimization manager instance."""
    return optimization_manager


def enable_all_optimizations():
    """Enable all performance optimizations."""
    optimization_manager.enable_optimizations()
    optimization_manager.apply_database_optimizations()
    optimization_manager.log_optimization_status()


def disable_all_optimizations():
    """Disable all performance optimizations."""
    optimization_manager.disable_optimizations()
    optimization_manager.log_optimization_status()


def get_optimization_summary() -> str:
    """Get optimization summary report."""
    return optimization_manager.create_performance_summary()


# Auto-enable optimizations on import
if __name__ != "__main__":
    try:
        enable_all_optimizations()
    except Exception as e:
        logger.warning(f"Failed to auto-enable optimizations: {e}")
