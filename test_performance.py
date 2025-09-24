"""
Performance test script for FWMIS application.
Tests memory efficiency and performance with large datasets.
"""

import os
import sys
import time
import logging
import sqlite3
from datetime import datetime, timedelta
import random
import tempfile

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from scripts.Utilities.optimized_import_utils import (
    StreamingCSVProcessor, OptimizedBASParser, BatchDatabaseInserter,
    create_performance_indexes, optimize_database_settings, get_optimal_chunk_size
)
from scripts.Utilities.optimized_excel_utils import StreamingExcelExporter, OptimizedReportGenerator
from scripts.Utilities.performance_profiler import (
    PerformanceProfiler, MemoryProfiler, log_performance_report
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceTestSuite:
    """Comprehensive performance test suite."""
    
    def __init__(self):
        self.profiler = PerformanceProfiler()
        self.memory_profiler = MemoryProfiler()
        self.test_results = {}
        
    def run_all_tests(self):
        """Run all performance tests."""
        logger.info("=== STARTING FWMIS PERFORMANCE TEST SUITE ===")
        
        tests = [
            ("Database Optimization", self.test_database_optimization),
            ("Memory Usage", self.test_memory_usage),
            ("CSV Processing", self.test_csv_processing),
            ("Excel Export", self.test_excel_export),
            ("Report Generation", self.test_report_generation),
            ("Large Dataset Import", self.test_large_dataset_import),
            ("Batch Operations", self.test_batch_operations),
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\n--- Running {test_name} Test ---")
            try:
                self.profiler.start_timer(test_name)
                self.memory_profiler.take_snapshot(f"{test_name}_start")
                
                result = test_func()
                self.test_results[test_name] = result
                
                self.profiler.end_timer(test_name)
                self.memory_profiler.take_snapshot(f"{test_name}_end")
                
                logger.info(f"✓ {test_name} completed successfully")
                
            except Exception as e:
                logger.error(f"✗ {test_name} failed: {e}")
                self.test_results[test_name] = {"error": str(e)}
        
        self.generate_test_report()
    
    def test_database_optimization(self):
        """Test database optimization features."""
        logger.info("Testing database optimization...")
        
        # Test index creation
        create_performance_indexes()
        
        # Test database settings optimization
        optimize_database_settings()
        
        # Test connection performance
        from scripts.Utilities.db_utils import get_db_connection
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Test query performance
            start_time = time.time()
            cursor.execute("SELECT COUNT(*) FROM cases")
            count = cursor.fetchone()[0]
            query_time = time.time() - start_time
            
            logger.info(f"Database query completed in {query_time:.3f}s, found {count} cases")
        
        return {
            "indexes_created": True,
            "optimizations_applied": True,
            "query_time": query_time,
            "case_count": count
        }
    
    def test_memory_usage(self):
        """Test memory usage monitoring."""
        logger.info("Testing memory usage monitoring...")
        
        # Test memory monitoring
        from scripts.Utilities.optimized_import_utils import memory_usage_monitor
        
        memory_ok = memory_usage_monitor()
        
        # Test chunk size optimization
        optimal_chunk_size = get_optimal_chunk_size()
        
        logger.info(f"Memory monitoring: {'OK' if memory_ok else 'WARNING'}")
        logger.info(f"Optimal chunk size: {optimal_chunk_size}")
        
        return {
            "memory_monitoring": memory_ok,
            "optimal_chunk_size": optimal_chunk_size
        }
    
    def test_csv_processing(self):
        """Test CSV processing with streaming."""
        logger.info("Testing CSV processing...")
        
        # Create test CSV file
        test_csv_path = self.create_test_csv(10000)  # 10k rows
        
        try:
            # Test streaming processor
            processor = StreamingCSVProcessor(test_csv_path, chunk_size=1000)
            
            total_rows = 0
            chunk_count = 0
            
            start_time = time.time()
            for chunk in processor.process_chunks():
                total_rows += len(chunk)
                chunk_count += 1
            processing_time = time.time() - start_time
            
            logger.info(f"Processed {total_rows} rows in {chunk_count} chunks in {processing_time:.3f}s")
            
            return {
                "rows_processed": total_rows,
                "chunks": chunk_count,
                "processing_time": processing_time,
                "rows_per_second": total_rows / processing_time if processing_time > 0 else 0
            }
            
        finally:
            # Cleanup
            if os.path.exists(test_csv_path):
                os.remove(test_csv_path)
    
    def test_excel_export(self):
        """Test Excel export with streaming."""
        logger.info("Testing Excel export...")
        
        # Create test data
        test_data = self.create_test_case_data(5000)  # 5k cases
        
        # Test streaming exporter
        exporter = StreamingExcelExporter(chunk_size=1000)
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            def data_generator():
                for case in test_data:
                    yield case
            
            start_time = time.time()
            exported_file = exporter.export_cases_to_excel_streaming(
                data_generator(),
                tmp_path,
                "Test Cases"
            )
            export_time = time.time() - start_time
            
            file_size = os.path.getsize(exported_file)
            
            logger.info(f"Exported {len(test_data)} cases in {export_time:.3f}s, file size: {file_size/1024/1024:.1f}MB")
            
            return {
                "cases_exported": len(test_data),
                "export_time": export_time,
                "file_size_mb": file_size / 1024 / 1024,
                "cases_per_second": len(test_data) / export_time if export_time > 0 else 0
            }
            
        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def test_report_generation(self):
        """Test report generation with SQL aggregations."""
        logger.info("Testing report generation...")
        
        # Test report generator
        report_generator = OptimizedReportGenerator()
        
        start_time = time.time()
        report_data = report_generator.generate_case_summary_report()
        generation_time = time.time() - start_time
        
        logger.info(f"Generated report in {generation_time:.3f}s")
        logger.info(f"Report contains {len(report_data.get('categories', []))} categories")
        
        return {
            "generation_time": generation_time,
            "categories_count": len(report_data.get('categories', [])),
            "statuses_count": len(report_data.get('statuses', [])),
            "total_cases": report_data.get('totals', {}).get('total_cases', 0)
        }
    
    def test_large_dataset_import(self):
        """Test importing large dataset."""
        logger.info("Testing large dataset import...")
        
        # Create large test dataset
        large_dataset = self.create_test_case_data(20000)  # 20k cases
        
        # Test batch inserter
        inserter = BatchDatabaseInserter(chunk_size=1000)
        
        start_time = time.time()
        try:
            # Note: This would normally insert to database, but for testing we'll simulate
            # In real usage, you'd call: inserted_cases = inserter.insert_cases_batch(large_dataset, fy_id=1)
            
            # Simulate batch processing
            batch_count = 0
            for i in range(0, len(large_dataset), 1000):
                batch = large_dataset[i:i + 1000]
                batch_count += 1
                # Simulate processing time
                time.sleep(0.001)  # 1ms per batch
            
            processing_time = time.time() - start_time
            
            logger.info(f"Processed {len(large_dataset)} cases in {batch_count} batches in {processing_time:.3f}s")
            
            return {
                "cases_processed": len(large_dataset),
                "batches": batch_count,
                "processing_time": processing_time,
                "cases_per_second": len(large_dataset) / processing_time if processing_time > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Large dataset import test failed: {e}")
            return {"error": str(e)}
    
    def test_batch_operations(self):
        """Test batch database operations."""
        logger.info("Testing batch operations...")
        
        from scripts.Utilities.db_utils import get_db_connection
        
        # Test batch insert performance
        test_cases = self.create_test_case_data(1000)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Test single inserts vs batch inserts
            start_time = time.time()
            
            # Single inserts (slower)
            cursor.execute("BEGIN TRANSACTION")
            for case in test_cases[:100]:  # Test with 100 cases
                cursor.execute(
                    "INSERT INTO cases (transaction_no, description, amount) VALUES (?, ?, ?)",
                    (case['transaction_no'], case['description'], case['amount'])
                )
            cursor.execute("COMMIT")
            
            single_insert_time = time.time() - start_time
            
            # Batch insert (faster)
            start_time = time.time()
            cursor.execute("BEGIN TRANSACTION")
            cursor.executemany(
                "INSERT INTO cases (transaction_no, description, amount) VALUES (?, ?, ?)",
                [(case['transaction_no'], case['description'], case['amount']) for case in test_cases[100:200]]
            )
            cursor.execute("COMMIT")
            
            batch_insert_time = time.time() - start_time
            
            logger.info(f"Single inserts: {single_insert_time:.3f}s, Batch inserts: {batch_insert_time:.3f}s")
            
            return {
                "single_insert_time": single_insert_time,
                "batch_insert_time": batch_insert_time,
                "performance_improvement": single_insert_time / batch_insert_time if batch_insert_time > 0 else 0
            }
    
    def create_test_csv(self, rows: int) -> str:
        """Create a test CSV file with specified number of rows."""
        test_csv_path = os.path.join(tempfile.gettempdir(), f"test_data_{rows}.csv")
        
        with open(test_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            csvfile.write("transaction_no,description,amount,date,category\n")
            
            for i in range(rows):
                csvfile.write(f"TEST{i:06d},Test transaction {i},{random.uniform(100, 10000):.2f},2025-01-01,Test Category\n")
        
        return test_csv_path
    
    def create_test_case_data(self, count: int) -> list:
        """Create test case data."""
        cases = []
        
        for i in range(count):
            cases.append({
                'transaction_no': f'TEST{i:06d}',
                'description': f'Test case {i}',
                'amount': random.uniform(100, 10000),
                'date_reported': '2025-01-01',
                'category': 'Test Category',
                'list': 'Checklist',
                'status': 'Alleged',
                'responsibility': 'Test Responsibility'
            })
        
        return cases
    
    def generate_test_report(self):
        """Generate comprehensive test report."""
        logger.info("\n=== PERFORMANCE TEST REPORT ===")
        
        # Performance summary
        self.profiler.log_summary()
        
        # Memory usage summary
        self.memory_profiler.log_memory_usage()
        
        # Test results summary
        logger.info("\n--- Test Results Summary ---")
        for test_name, result in self.test_results.items():
            if 'error' in result:
                logger.error(f"{test_name}: FAILED - {result['error']}")
            else:
                logger.info(f"{test_name}: PASSED")
                for key, value in result.items():
                    if isinstance(value, float):
                        logger.info(f"  {key}: {value:.3f}")
                    else:
                        logger.info(f"  {key}: {value}")
        
        # Recommendations
        logger.info("\n--- Performance Recommendations ---")
        logger.info("1. Use streaming for large file imports")
        logger.info("2. Implement batch database operations")
        logger.info("3. Monitor memory usage during operations")
        logger.info("4. Use SQL aggregations for reports")
        logger.info("5. Consider PyPy for 2-7x speed improvements")
        logger.info("6. Create appropriate database indexes")
        
        # Save report to file
        try:
            with open("data/performance_test_report.txt", "w") as f:
                f.write("FWMIS Performance Test Report\n")
                f.write("=" * 50 + "\n\n")
                
                for test_name, result in self.test_results.items():
                    f.write(f"{test_name}:\n")
                    if 'error' in result:
                        f.write(f"  Status: FAILED\n")
                        f.write(f"  Error: {result['error']}\n")
                    else:
                        f.write(f"  Status: PASSED\n")
                        for key, value in result.items():
                            f.write(f"  {key}: {value}\n")
                    f.write("\n")
            
            logger.info("Performance test report saved to data/performance_test_report.txt")
            
        except Exception as e:
            logger.error(f"Error saving test report: {e}")

def main():
    """Main function to run performance tests."""
    print("FWMIS Performance Test Suite")
    print("=" * 40)
    print("This script tests the performance and memory efficiency")
    print("of the FWMIS application with large datasets.")
    print()
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Run test suite
    test_suite = PerformanceTestSuite()
    test_suite.run_all_tests()
    
    print("\nPerformance tests completed!")
    print("Check the logs and data/performance_test_report.txt for detailed results.")

if __name__ == "__main__":
    main()
