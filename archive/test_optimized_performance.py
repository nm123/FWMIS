#!/usr/bin/env python3
"""
Performance test script for FWMIS optimized components.
Tests memory usage, database performance, and large dataset handling.
"""

import os
import sys
import time
import logging
from datetime import datetime, date
from typing import List, Dict, Any

# Add the scripts directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from scripts.Utilities.optimized_import_utils import (
    OptimizedBASParser, BatchDatabaseInserter, 
    create_performance_indexes, optimize_database_settings,
    memory_usage_monitor, get_optimal_chunk_size
)
from scripts.Utilities.optimized_excel_utils import StreamingExcelExporter
from scripts.Utilities.performance_profiler import performance_profiler, memory_profiler
from scripts.Utilities.db_utils import get_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_test_data(num_cases: int = 10000) -> List[Dict[str, Any]]:
    """Create test case data for performance testing."""
    logger.info(f"Creating {num_cases} test cases...")
    
    test_cases = []
    for i in range(num_cases):
        case = {
            "transaction_no": f"2026000{i:05d}",
            "base_transaction_no": f"2026000{i:05d}",
            "date_incurred": "2025-01-15",
            "date_identified": "2025-01-15", 
            "date_reported": "2025-01-15",
            "description": f"Test case {i} - Performance testing",
            "bas_payment_no": f"PAY{i:06d}",
            "bas_payment_date": "2025-01-15",
            "persal_no": None,
            "category": "Test Category",
            "responsibility_id": 1,
            "amount": 1000.00 + (i * 10),
            "source_document": None,
            "minutes": None,
            "evidence_path": None,
            "status": "Alleged",
            "list": "Checklist",
            "assessment_assessed_by": None,
            "assessment_date": None,
            "assessment_result": None,
            "period_id": 1,
            "criminal_charges": "N/A",
            "disciplinary_process": "N/A",
            "loss_recovery": "N/A",
            "prevention_steps": "N/A",
            "original_list": "Checklist",
            "attachments": "[]",
            "shared_document_id": None,
            "bas_journal_no": None,
            "bas_journal_date": None,
        }
        test_cases.append(case)
    
    logger.info(f"Created {len(test_cases)} test cases")
    return test_cases


def test_memory_usage():
    """Test memory usage monitoring."""
    logger.info("Testing memory usage monitoring...")
    
    try:
        # Take initial memory snapshot
        memory_profiler.take_snapshot("test_start")
        
        # Create some test data
        test_data = create_test_data(1000)
        memory_profiler.take_snapshot("after_data_creation")
        
        # Check memory usage
        memory_ok = memory_usage_monitor()
        logger.info(f"Memory usage check: {'OK' if memory_ok else 'WARNING'}")
        
        # Clean up
        del test_data
        memory_profiler.take_snapshot("after_cleanup")
        
        logger.info("Memory usage test completed")
        return True
        
    except Exception as e:
        logger.error(f"Memory usage test failed: {e}")
        return False


def test_database_optimizations():
    """Test database optimizations."""
    logger.info("Testing database optimizations...")
    
    try:
        # Apply optimizations
        optimize_database_settings()
        create_performance_indexes()
        
        # Test database connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Test a simple query
            cursor.execute("SELECT COUNT(*) FROM cases")
            count = cursor.fetchone()[0]
            logger.info(f"Database connection test: {count} cases found")
            
            # Test index usage
            cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM cases WHERE fy_id = 1")
            plan = cursor.fetchall()
            logger.info(f"Query plan: {plan}")
        
        logger.info("Database optimizations test completed")
        return True
        
    except Exception as e:
        logger.error(f"Database optimizations test failed: {e}")
        return False


def test_batch_inserter():
    """Test batch database inserter."""
    logger.info("Testing batch database inserter...")
    
    try:
        # Create test data
        test_cases = create_test_data(1000)
        
        # Test batch inserter
        inserter = BatchDatabaseInserter(chunk_size=100)
        
        with performance_profiler.timer("batch_insert_test"):
            inserted_cases = inserter.insert_cases_batch(test_cases, fy_id=1)
        
        logger.info(f"Batch inserter test: {len(inserted_cases)} cases inserted")
        
        # Clean up test data
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cases WHERE description LIKE 'Test case%'")
            conn.commit()
        
        logger.info("Batch inserter test completed")
        return True
        
    except Exception as e:
        logger.error(f"Batch inserter test failed: {e}")
        return False


def test_excel_export():
    """Test optimized Excel export."""
    logger.info("Testing optimized Excel export...")
    
    try:
        # Create test data
        test_cases = create_test_data(5000)
        
        # Create test export file
        export_file = "test_export.xlsx"
        
        # Test streaming exporter
        exporter = StreamingExcelExporter(chunk_size=1000)
        
        with performance_profiler.timer("excel_export_test"):
            def cases_iterator():
                for case in test_cases:
                    yield case
            
            exported_file = exporter.export_cases_to_excel_streaming(
                cases_iterator(), 
                export_file, 
                "Test Cases"
            )
        
        # Check if file was created
        if os.path.exists(exported_file):
            file_size = os.path.getsize(exported_file) / (1024 * 1024)  # MB
            logger.info(f"Excel export test: {file_size:.2f} MB file created")
            
            # Clean up
            os.remove(exported_file)
        else:
            logger.error("Excel export test: File was not created")
            return False
        
        logger.info("Excel export test completed")
        return True
        
    except Exception as e:
        logger.error(f"Excel export test failed: {e}")
        return False


def test_chunk_size_optimization():
    """Test adaptive chunk size optimization."""
    logger.info("Testing chunk size optimization...")
    
    try:
        # Test different chunk sizes
        chunk_sizes = [100, 500, 1000, 5000]
        
        for chunk_size in chunk_sizes:
            logger.info(f"Testing chunk size: {chunk_size}")
            
            # Create test data
            test_cases = create_test_data(chunk_size * 2)
            
            # Test with this chunk size
            inserter = BatchDatabaseInserter(chunk_size=chunk_size)
            
            start_time = time.time()
            inserted_cases = inserter.insert_cases_batch(test_cases, fy_id=1)
            end_time = time.time()
            
            duration = end_time - start_time
            logger.info(f"Chunk size {chunk_size}: {len(inserted_cases)} cases in {duration:.2f}s")
            
            # Clean up
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM cases WHERE description LIKE 'Test case%'")
                conn.commit()
        
        # Test optimal chunk size detection
        optimal_size = get_optimal_chunk_size()
        logger.info(f"Optimal chunk size detected: {optimal_size}")
        
        logger.info("Chunk size optimization test completed")
        return True
        
    except Exception as e:
        logger.error(f"Chunk size optimization test failed: {e}")
        return False


def test_large_dataset_handling():
    """Test handling of large datasets."""
    logger.info("Testing large dataset handling...")
    
    try:
        # Test with progressively larger datasets
        dataset_sizes = [1000, 5000, 10000]
        
        for size in dataset_sizes:
            logger.info(f"Testing dataset size: {size}")
            
            # Create test data
            test_cases = create_test_data(size)
            
            # Test memory usage
            memory_profiler.take_snapshot(f"before_large_test_{size}")
            
            # Test batch processing
            inserter = BatchDatabaseInserter(chunk_size=1000)
            
            with performance_profiler.timer(f"large_dataset_{size}"):
                inserted_cases = inserter.insert_cases_batch(test_cases, fy_id=1)
            
            memory_profiler.take_snapshot(f"after_large_test_{size}")
            
            logger.info(f"Large dataset test {size}: {len(inserted_cases)} cases processed")
            
            # Clean up
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM cases WHERE description LIKE 'Test case%'")
                conn.commit()
        
        logger.info("Large dataset handling test completed")
        return True
        
    except Exception as e:
        logger.error(f"Large dataset handling test failed: {e}")
        return False


def run_performance_report():
    """Generate performance report."""
    logger.info("Generating performance report...")
    
    try:
        from scripts.Utilities.performance_profiler import log_performance_report
        log_performance_report()
        logger.info("Performance report generated")
        return True
        
    except Exception as e:
        logger.error(f"Performance report generation failed: {e}")
        return False


def main():
    """Run all performance tests."""
    logger.info("Starting FWMIS Performance Tests")
    logger.info("=" * 50)
    
    tests = [
        ("Memory Usage", test_memory_usage),
        ("Database Optimizations", test_database_optimizations),
        ("Batch Inserter", test_batch_inserter),
        ("Excel Export", test_excel_export),
        ("Chunk Size Optimization", test_chunk_size_optimization),
        ("Large Dataset Handling", test_large_dataset_handling),
        ("Performance Report", run_performance_report),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning {test_name} test...")
        try:
            result = test_func()
            results[test_name] = "PASSED" if result else "FAILED"
            logger.info(f"{test_name} test: {results[test_name]}")
        except Exception as e:
            logger.error(f"{test_name} test failed with exception: {e}")
            results[test_name] = "ERROR"
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("PERFORMANCE TEST SUMMARY")
    logger.info("=" * 50)
    
    passed = sum(1 for result in results.values() if result == "PASSED")
    total = len(results)
    
    for test_name, result in results.items():
        status_icon = "✅" if result == "PASSED" else "❌"
        logger.info(f"{status_icon} {test_name}: {result}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All performance tests passed! Optimizations are working correctly.")
    else:
        logger.warning(f"⚠️  {total - passed} tests failed. Check the logs for details.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
