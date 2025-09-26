#!/usr/bin/env python3
"""
Database Optimization Utilities for FWMIS

This module provides database optimization features including:
- Index creation and management
- Query performance analysis
- Database maintenance operations
- Performance monitoring
"""

import sqlite3
import os
import time
from typing import List, Dict, Tuple
from scripts.Utilities.config import DB_PATH


class DatabaseOptimizer:
    """Database optimization and performance monitoring utilities"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def get_database_stats(self) -> Dict:
        """Get comprehensive database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            stats = {}

            # Table statistics
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[f"{table}_count"] = count

            # Database file size
            stats['db_size_mb'] = os.path.getsize(self.db_path) / (1024 * 1024)

            # Index information
            cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index'")
            indexes = cursor.fetchall()
            stats['indexes'] = indexes

            return stats

        finally:
            conn.close()

    def create_performance_indexes(self) -> List[str]:
        """Create indexes optimized for FWMIS performance"""
        indexes_created = []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Essential indexes for FWMIS performance
            indexes = [
                ("idx_cases_status", "cases", "assessment_status"),
                ("idx_cases_lc_status", "cases", "lc_status"),
                ("idx_cases_finalized", "cases", "is_finalized"),
                ("idx_cases_transaction", "cases", "base_transaction_no"),
                ("idx_cases_fy", "cases", "fy_id"),
                ("idx_cases_amount", "cases", "amount"),
                ("idx_cases_suffixes", "cases", "suffixes"),
                ("idx_cases_write_off_group", "cases", "write_off_group_id"),
            ]

            for index_name, table, column in indexes:
                try:
                    cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column})")
                    indexes_created.append(index_name)
                    print(f"[OK] Created index: {index_name}")
                except sqlite3.Error as e:
                    print(f"[WARNING] Failed to create index {index_name}: {e}")

            conn.commit()

        finally:
            conn.close()

        return indexes_created

    def analyze_query_performance(self, queries: List[Tuple[str, str]]) -> Dict:
        """Analyze performance of common queries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        results = {}

        try:
            for query_name, query in queries:
                times = []

                # Run query multiple times for accurate measurement
                for _ in range(5):
                    start_time = time.time()
                    cursor.execute(query)
                    result = cursor.fetchall()
                    elapsed = time.time() - start_time
                    times.append(elapsed)

                avg_time = sum(times) / len(times)
                results[query_name] = {
                    'avg_time': avg_time,
                    'min_time': min(times),
                    'max_time': max(times),
                    'result_count': len(result) if result else 0
                }

        finally:
            conn.close()

        return results

    def optimize_database(self) -> Dict:
        """Perform database optimization operations"""
        print("[OPTIMIZE] Starting database optimization...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        results = {}

        try:
            # Enable WAL mode for better concurrent access
            cursor.execute("PRAGMA journal_mode=WAL")
            wal_result = cursor.fetchone()
            wal_mode = wal_result[0] if wal_result else "UNKNOWN"
            results['wal_mode'] = wal_mode

            # Optimize page size
            cursor.execute("PRAGMA page_size=4096")
            page_result = cursor.fetchone()
            page_size = page_result[0] if page_result else 4096
            results['page_size'] = page_size

            # Set synchronous mode for better performance (with some risk)
            cursor.execute("PRAGMA synchronous=NORMAL")
            sync_result = cursor.fetchone()
            sync_mode = sync_result[0] if sync_result else "NORMAL"
            results['synchronous'] = sync_mode

            # Cache size optimization
            cursor.execute("PRAGMA cache_size=-64000")  # ~64MB cache
            cache_result = cursor.fetchone()
            cache_size = cache_result[0] if cache_result else -64000
            results['cache_size'] = cache_size

            # Run ANALYZE for query optimization
            print("[ANALYZE] Running ANALYZE for query optimization...")
            cursor.execute("ANALYZE")
            results['analyze_completed'] = True

            # Vacuum to reclaim space and optimize
            print("[VACUUM] Running VACUUM to optimize database...")
            start_size = os.path.getsize(self.db_path)
            cursor.execute("VACUUM")
            end_size = os.path.getsize(self.db_path)
            space_saved = start_size - end_size
            results['space_saved_mb'] = space_saved / (1024 * 1024)

            conn.commit()

        finally:
            conn.close()

        print("[SUCCESS] Database optimization completed!")
        return results

    def get_performance_recommendations(self) -> List[str]:
        """Generate performance recommendations based on current setup"""
        recommendations = []

        stats = self.get_database_stats()

        # Case count recommendations
        case_count = stats.get('cases_count', 0)
        if case_count > 50000:
            recommendations.append("🔴 CRITICAL: Database has >50,000 cases. Consider archiving old finalized cases.")
        elif case_count > 10000:
            recommendations.append("🟡 WARNING: Database has >10,000 cases. Implement pagination for list views.")

        # Database size recommendations
        db_size = stats.get('db_size_mb', 0)
        if db_size > 500:
            recommendations.append("🔴 CRITICAL: Database >500MB. Immediate archiving required.")
        elif db_size > 100:
            recommendations.append("🟡 WARNING: Database >100MB. Monitor growth and consider optimization.")

        # Index recommendations
        indexes = stats.get('indexes', [])
        essential_indexes = ['idx_cases_status', 'idx_cases_finalized', 'idx_cases_transaction']
        missing_indexes = []

        for idx in essential_indexes:
            if not any(idx in index_info for index_info in indexes):
                missing_indexes.append(idx)

        if missing_indexes:
            recommendations.append(f"🟡 MISSING INDEXES: Create these indexes for better performance: {', '.join(missing_indexes)}")

        # General recommendations
        recommendations.extend([
            "✅ Implement database connection pooling for concurrent users",
            "✅ Use prepared statements for repeated queries",
            "✅ Monitor slow queries (>1 second) in production",
            "✅ Schedule regular database maintenance (weekly VACUUM)",
            "✅ Consider read replicas for heavy reporting workloads"
        ])

        return recommendations


def optimize_database_cli():
    """Command-line interface for database optimization"""
    import argparse

    parser = argparse.ArgumentParser(description="FWMIS Database Optimizer")
    parser.add_argument("--create-indexes", action="store_true", help="Create performance indexes")
    parser.add_argument("--optimize", action="store_true", help="Run full database optimization")
    parser.add_argument("--analyze", action="store_true", help="Analyze query performance")
    parser.add_argument("--recommendations", action="store_true", help="Show performance recommendations")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")

    args = parser.parse_args()

    optimizer = DatabaseOptimizer()

    if args.stats:
        print("📊 DATABASE STATISTICS:")
        stats = optimizer.get_database_stats()
        for key, value in stats.items():
            if key == 'indexes':
                print(f"  {key}: {len(value)} indexes")
                for idx in value[:5]:  # Show first 5
                    print(f"    - {idx[0]} on {idx[1]}")
                if len(value) > 5:
                    print(f"    ... and {len(value) - 5} more")
            else:
                print(f"  {key}: {value}")
        print()

    if args.create_indexes:
        print("🏗️  CREATING PERFORMANCE INDEXES:")
        indexes = optimizer.create_performance_indexes()
        print(f"Created {len(indexes)} indexes")
        print()

    if args.optimize:
        print("🔧 RUNNING DATABASE OPTIMIZATION:")
        results = optimizer.optimize_database()
        for key, value in results.items():
            print(f"  {key}: {value}")
        print()

    if args.analyze:
        print("📈 QUERY PERFORMANCE ANALYSIS:")
        # Common FWMIS queries to analyze
        queries = [
            ("Count all cases", "SELECT COUNT(*) FROM cases"),
            ("List alleged cases", "SELECT * FROM cases WHERE assessment_status = 'Alleged' LIMIT 100"),
            ("Search by transaction", "SELECT * FROM cases WHERE base_transaction_no LIKE 'TEST-%'"),
            ("Complex filter", "SELECT COUNT(*) FROM cases WHERE assessment_status = 'Confirmed' AND lc_status IS NOT NULL"),
            ("Status summary", "SELECT assessment_status, COUNT(*) FROM cases GROUP BY assessment_status"),
        ]

        results = optimizer.analyze_query_performance(queries)
        for query_name, data in results.items():
            print(f"  {query_name}: {data['avg_time']:.4f}s avg ({data['result_count']} results)")
        print()

    if args.recommendations:
        print("💡 PERFORMANCE RECOMMENDATIONS:")
        recommendations = optimizer.get_performance_recommendations()
        for rec in recommendations:
            print(f"  {rec}")
        print()

    if not any([args.stats, args.create_indexes, args.optimize, args.analyze, args.recommendations]):
        parser.print_help()


if __name__ == "__main__":
    optimize_database_cli()
