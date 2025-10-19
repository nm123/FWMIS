"""
Performance profiling utilities for identifying bottlenecks and optimizing performance.
"""

import time
import logging
import functools
import gc
import os
from typing import Dict, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class PerformanceProfiler:
    """Performance profiler for monitoring execution time and memory usage."""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
    
    def start_timer(self, operation_name: str):
        """Start timing an operation."""
        self.start_times[operation_name] = time.time()
    
    def end_timer(self, operation_name: str) -> float:
        """End timing an operation and return duration."""
        if operation_name not in self.start_times:
            logger.warning(f"Timer '{operation_name}' was not started")
            return 0.0
        
        duration = time.time() - self.start_times[operation_name]
        
        if operation_name not in self.metrics:
            self.metrics[operation_name] = []
        
        self.metrics[operation_name].append(duration)
        del self.start_times[operation_name]
        
        logger.info(f"Operation '{operation_name}' took {duration:.3f} seconds")
        return duration
    
    def get_average_time(self, operation_name: str) -> float:
        """Get average execution time for an operation."""
        if operation_name not in self.metrics or not self.metrics[operation_name]:
            return 0.0
        
        return sum(self.metrics[operation_name]) / len(self.metrics[operation_name])
    
    def get_total_time(self, operation_name: str) -> float:
        """Get total execution time for an operation."""
        if operation_name not in self.metrics:
            return 0.0
        
        return sum(self.metrics[operation_name])
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        summary = {}
        
        for operation, times in self.metrics.items():
            if times:
                summary[operation] = {
                    'count': len(times),
                    'total_time': sum(times),
                    'average_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times)
                }
        
        return summary
    
    def log_summary(self):
        """Log performance summary."""
        summary = self.get_summary()
        
        logger.info("=== PERFORMANCE SUMMARY ===")
        for operation, stats in summary.items():
            logger.info(
                f"{operation}: {stats['count']} calls, "
                f"avg: {stats['average_time']:.3f}s, "
                f"total: {stats['total_time']:.3f}s"
            )

@contextmanager
def profile_operation(operation_name: str, profiler: Optional[PerformanceProfiler] = None):
    """Context manager for profiling operations."""
    if profiler is None:
        profiler = PerformanceProfiler()
    
    profiler.start_timer(operation_name)
    try:
        yield profiler
    finally:
        profiler.end_timer(operation_name)

def profile_function(operation_name: Optional[str] = None):
    """Decorator for profiling function execution time."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                logger.info(f"Function '{name}' executed in {duration:.3f} seconds")
        
        return wrapper
    return decorator

class MemoryProfiler:
    """Memory usage profiler."""
    
    def __init__(self):
        self.memory_snapshots = {}
    
    def take_snapshot(self, label: str):
        """Take a memory snapshot."""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            self.memory_snapshots[label] = {
                'rss': memory_info.rss,  # Resident Set Size
                'vms': memory_info.vms,  # Virtual Memory Size
                'timestamp': time.time()
            }
            
            logger.info(f"Memory snapshot '{label}': RSS={memory_info.rss / 1024 / 1024:.1f}MB")
            
        except ImportError:
            logger.warning("psutil not available for memory profiling")
    
    def compare_snapshots(self, label1: str, label2: str) -> Dict[str, int]:
        """Compare two memory snapshots."""
        if label1 not in self.memory_snapshots or label2 not in self.memory_snapshots:
            logger.warning(f"Snapshots '{label1}' or '{label2}' not found")
            return {}
        
        snap1 = self.memory_snapshots[label1]
        snap2 = self.memory_snapshots[label2]
        
        return {
            'rss_diff': snap2['rss'] - snap1['rss'],
            'vms_diff': snap2['vms'] - snap1['vms'],
            'time_diff': snap2['timestamp'] - snap1['timestamp']
        }
    
    def log_memory_usage(self):
        """Log current memory usage."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info()
            
            logger.info(
                "System Memory: %s%% used (%sGB / %sGB)",
                memory.percent,
                memory.used / 1024 / 1024 / 1024,
                memory.total / 1024 / 1024 / 1024,
            )
            logger.info(
                "Process Memory: RSS=%sMB, VMS=%sMB",
                process_memory.rss / 1024 / 1024,
                process_memory.vms / 1024 / 1024,
            )
            
        except ImportError:
            logger.warning("psutil not available for memory logging")

def optimize_memory():
    """Force garbage collection and memory optimization."""
    collected = gc.collect()
    logger.info(f"Garbage collection freed {collected} objects")
    
    # Set garbage collection thresholds for better performance
    gc.set_threshold(700, 10, 10)

class DatabaseProfiler:
    """Database operation profiler."""
    
    def __init__(self):
        self.query_times = {}
        self.slow_queries = []
    
    def profile_query(self, query: str, params: tuple = None):
        """Profile a database query."""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    
                    query_key = f"{query[:50]}..." if len(query) > 50 else query
                    
                    if query_key not in self.query_times:
                        self.query_times[query_key] = []
                    
                    self.query_times[query_key].append(duration)
                    
                    # Log slow queries
                    if duration > 1.0:  # Queries taking more than 1 second
                        self.slow_queries.append({
                            'query': query,
                            'params': params,
                            'duration': duration,
                            'timestamp': time.time()
                        })
                        logger.warning(f"Slow query detected: {duration:.3f}s - {query_key}")
            
            return wrapper
        return decorator
    
    def get_slow_queries(self) -> list:
        """Get list of slow queries."""
        return self.slow_queries
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Get query performance statistics."""
        stats = {}
        
        for query, times in self.query_times.items():
            if times:
                stats[query] = {
                    'count': len(times),
                    'total_time': sum(times),
                    'average_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times)
                }
        
        return stats

def create_performance_report() -> str:
    """Create a comprehensive performance report."""
    report = []
    report.append("=== FWMIS PERFORMANCE REPORT ===")
    report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # System information
    try:
        import psutil
        memory = psutil.virtual_memory()
        cpu_count = psutil.cpu_count()
        
        report.append("SYSTEM INFORMATION:")
        report.append(f"  CPU Cores: {cpu_count}")
        report.append(f"  Total Memory: {memory.total / 1024 / 1024 / 1024:.1f} GB")
        report.append(f"  Available Memory: {memory.available / 1024 / 1024 / 1024:.1f} GB")
        report.append(f"  Memory Usage: {memory.percent}%")
        report.append("")
        
    except ImportError:
        report.append("SYSTEM INFORMATION: psutil not available")
        report.append("")
    
    # Database file size
    try:
        db_path = "data/fruitless.db"
        if os.path.exists(db_path):
            db_size = os.path.getsize(db_path)
            report.append(f"DATABASE SIZE: {db_size / 1024 / 1024:.1f} MB")
            report.append("")
    except Exception as e:
        report.append(f"DATABASE SIZE: Error reading - {e}")
        report.append("")
    
    # Recommendations
    report.append("PERFORMANCE RECOMMENDATIONS:")
    report.append("  1. Use streaming for large file imports")
    report.append("  2. Implement batch database operations")
    report.append("  3. Create appropriate database indexes")
    report.append("  4. Monitor memory usage during operations")
    report.append("  5. Use SQL aggregations instead of Python loops")
    report.append("  6. Consider PyPy for 2-7x speed improvements")
    
    return "\n".join(report)

def log_performance_report():
    """Log the performance report."""
    report = create_performance_report()
    logger.info(report)
    
    # Also save to file
    try:
        with open("data/performance_report.txt", "w") as f:
            f.write(report)
        logger.info("Performance report saved to data/performance_report.txt")
    except Exception as e:
        logger.error(f"Error saving performance report: {e}")

# Global profiler instances
performance_profiler = PerformanceProfiler()
memory_profiler = MemoryProfiler()
database_profiler = DatabaseProfiler()
