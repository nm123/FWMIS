"""
Optimized view cases utilities with memory-efficient operations.
Replaces Pandas-based Excel exports with streaming alternatives.
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox

from scripts.Utilities.optimized_excel_utils import StreamingExcelExporter, OptimizedReportGenerator
from scripts.Utilities.performance_profiler import profile_operation, memory_profiler

logger = logging.getLogger(__name__)

class OptimizedViewCasesUtils:
    """Memory-efficient view cases utilities."""
    
    @staticmethod
    @profile_operation("export_to_excel")
    def export_to_excel(dialog):
        """Export the current case list to Excel format using memory-efficient streaming."""
        try:
            # Check if there are cases to export
            if dialog.case_table.rowCount() == 0:
                QMessageBox.warning(dialog, "No Data", "No cases to export.")
                return

            # Take memory snapshot before export
            memory_profiler.take_snapshot("before_export")

            # Get current list filter for filename
            current_list = dialog.list_filter_combo.currentText().replace(" ", "_")

            # Create year folder
            from scripts.Utilities.financial_utils import create_year_folder, get_financial_year
            year_folder = create_year_folder(get_financial_year())
            export_dir = os.path.join(year_folder, "Exports")
            os.makedirs(export_dir, exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"List_Export_{current_list}_{timestamp}.xlsx"
            filepath = os.path.join(export_dir, filename)

            # Extract data using memory-efficient generator
            def cases_generator():
                """Generator for case data to avoid loading all into memory."""
                for row in range(dialog.case_table.rowCount()):
                    row_data = {}
                    for col in range(dialog.case_table.columnCount()):
                        item = dialog.case_table.item(row, col)
                        if item:
                            if col == 0:  # Case No column
                                transaction_no = item.data(Qt.UserRole)
                                if transaction_no:
                                    row_data[f"col_{col}"] = transaction_no
                                else:
                                    row_data[f"col_{col}"] = item.text()
                            else:
                                row_data[f"col_{col}"] = item.text()
                        else:
                            widget = dialog.case_table.cellWidget(row, col)
                            if widget and hasattr(widget, "text"):
                                row_data[f"col_{col}"] = widget.text()
                            else:
                                row_data[f"col_{col}"] = ""
                    yield row_data

            # Get headers
            headers = []
            for col in range(dialog.case_table.columnCount()):
                header_item = dialog.case_table.horizontalHeaderItem(col)
                if header_item:
                    headers.append(header_item.text())

            # Use streaming Excel exporter
            exporter = StreamingExcelExporter(chunk_size=1000)
            
            # Convert generator to proper format
            def formatted_cases_generator():
                for case_data in cases_generator():
                    formatted_case = {}
                    for i, header in enumerate(headers):
                        formatted_case[header] = case_data.get(f"col_{i}", "")
                    yield formatted_case

            # Export using streaming
            exporter.export_cases_to_excel_streaming(
                formatted_cases_generator(),
                filepath,
                f"{current_list} Cases",
            )

            # Take memory snapshot after export
            memory_profiler.take_snapshot("after_export")
            
            # Compare memory usage
            memory_diff = memory_profiler.compare_snapshots(
                "before_export",
                "after_export",
            )
            if memory_diff:
                logger.info(
                    "Memory usage during export: %.1fMB",
                    memory_diff["rss_diff"] / 1024 / 1024,
                )

            # Show success message
            QMessageBox.information(
                dialog,
                "Export Successful",
                f"Case list exported successfully!\n\n"
                f"File: {filename}\n"
                f"Location: {export_dir}\n"
                f"Cases exported: {dialog.case_table.rowCount()}",
            )

        except Exception as e:
            logger.error(f"Error in optimized Excel export: {e}")
            QMessageBox.critical(
                dialog, "Export Error", f"Failed to export to Excel: {str(e)}"
            )

    @staticmethod
    def generate_optimized_report(cases_data: List[Dict], report_type: str = "Summary") -> str:
        """Generate report using SQL aggregations instead of Python loops."""
        try:
            report_generator = OptimizedReportGenerator()
            
            # Extract fy_id from first case if available
            fy_id = cases_data[0].get('fy_id') if cases_data else None
            
            if report_type == "Summary":
                report_data = report_generator.generate_case_summary_report(fy_id)
            elif report_type == "Responsibility":
                report_data = report_generator.generate_responsibility_report(fy_id)
            else:
                report_data = report_generator.generate_case_summary_report(fy_id)
            
            # Format report
            report = f"Case Report - {report_type}\n"
            report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            if 'totals' in report_data:
                totals = report_data['totals']
                report += f"Total Cases: {totals['total_cases']}\n"
                report += f"Total Amount: R {totals['total_amount']:,.2f}\n"
                report += f"Average Amount: R {totals['avg_amount']:,.2f}\n\n"
            
            if 'categories' in report_data:
                report += "Categories:\n"
                for cat in report_data['categories'][:10]:  # Top 10
                    report += (
                        f"  {cat['category']}: {cat['count']} cases, "
                        f"R {cat['amount']:,.2f}\n"
                    )
                report += "\n"
            
            if 'statuses' in report_data:
                report += "Statuses:\n"
                for stat in report_data['statuses'][:10]:  # Top 10
                    report += (
                        f"  {stat['status']}: {stat['count']} cases, "
                        f"R {stat['amount']:,.2f}\n"
                    )
                report += "\n"
            
            if 'responsibilities' in report_data:
                report += "Top Responsibilities:\n"
                for resp in report_data['responsibilities'][:10]:  # Top 10
                    report += (
                        f"  {resp['name']}: {resp['case_count']} cases, "
                        f"R {resp['total_amount']:,.2f}\n"
                    )
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating optimized report: {e}")
            return f"Error generating report: {str(e)}"

    @staticmethod
    def validate_export_data_efficiently(data: List[Dict]) -> tuple[bool, str]:
        """Validate data before export with memory efficiency."""
        if not data:
            return False, "No data to export"

        if not isinstance(data, list):
            return False, "Data must be a list of cases"

        if len(data) == 0:
            return False, "No cases to export"

        # Check first few items for structure validation
        sample_size = min(10, len(data))
        for i in range(sample_size):
            if not isinstance(data[i], dict):
                return False, f"Item {i} is not a valid case dictionary"

        return True, "Data is valid for export"

    @staticmethod
    def filter_cases_efficiently(cases: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
        """Filter cases efficiently using list comprehension."""
        filtered_cases = cases
        
        # Apply filters one by one
        if 'search_term' in filters and filters['search_term']:
            search_term = filters['search_term'].lower()
            filtered_cases = [
                case for case in filtered_cases
                if search_term in str(case.get('transaction_no', '')).lower() or
                   search_term in str(case.get('category', '')).lower() or
                   search_term in str(case.get('description', '')).lower()
            ]
        
        if 'min_amount' in filters and filters['min_amount'] is not None:
            filtered_cases = [
                case for case in filtered_cases
                if case.get('amount', 0) >= filters['min_amount']
            ]
        
        if 'max_amount' in filters and filters['max_amount'] is not None:
            filtered_cases = [
                case for case in filtered_cases
                if case.get('amount', 0) <= filters['max_amount']
            ]
        
        if 'status' in filters and filters['status']:
            filtered_cases = [
                case for case in filtered_cases
                if case.get('status', '') == filters['status']
            ]
        
        if 'category' in filters and filters['category']:
            filtered_cases = [
                case for case in filtered_cases
                if case.get('category', '') == filters['category']
            ]
        
        return filtered_cases

    @staticmethod
    def sort_cases_efficiently(
        cases: List[Dict],
        sort_by: str = "date_reported",
        ascending: bool = True,
    ) -> List[Dict]:
        """Sort cases efficiently using built-in sort with key function."""
        def sort_key(case):
            value = case.get(sort_by)
            if value is None:
                return "" if ascending else "z"
            
            # Handle different data types
            if isinstance(value, str):
                return value.lower() if ascending else value.lower()
            elif isinstance(value, (int, float)):
                return value if ascending else -value
            else:
                return str(value) if ascending else str(value)
        
        return sorted(cases, key=sort_key, reverse=not ascending)

    @staticmethod
    def calculate_totals_efficiently(cases: List[Dict]) -> Dict[str, Any]:
        """Calculate totals efficiently using single pass."""
        total_amount = 0.0
        total_cases = len(cases)
        categories = {}
        statuses = {}
        
        # Single pass through cases
        for case in cases:
            amount = case.get("amount", 0.0)
            total_amount += amount
            
            category = case.get("category", "Unknown")
            categories[category] = categories.get(category, 0) + 1
            
            status = case.get("assessment_status", "Unknown")
            statuses[status] = statuses.get(status, 0) + 1
        
        return {
            "total_amount": total_amount,
            "total_cases": total_cases,
            "categories": categories,
            "statuses": statuses,
        }

    @staticmethod
    def get_export_filename_optimized(list_name: str) -> str:
        """Generate export filename with optimization info."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_list_name = list_name.replace(" ", "_").replace("/", "_")
        return f"Optimized_Export_{safe_list_name}_{timestamp}.xlsx"

    @staticmethod
    def create_export_directory_optimized(year: str) -> str:
        """Create export directory with optimization subfolder."""
        export_dir = os.path.join("data", str(year), "Exports", "Optimized")
        os.makedirs(export_dir, exist_ok=True)
        return export_dir

    @staticmethod
    def validate_memory_for_large_export(cases_count: int) -> bool:
        """Validate if there's enough memory for large export operations."""
        try:
            import psutil
            
            available_memory_gb = psutil.virtual_memory().available / (1024**3)
            
            # Estimate memory needed (conservative estimate)
            estimated_memory_mb = cases_count * 0.002  # ~2KB per case for Excel processing
            
            threshold_mb = available_memory_gb * 1024 * 0.3
            if estimated_memory_mb > threshold_mb:
                logger.warning(
                    "Large export may cause memory issues: %s cases, %.1fMB estimated",
                    cases_count,
                    estimated_memory_mb,
                )
                return False
            
            return True
            
        except ImportError:
            # psutil not available, assume OK for reasonable sizes
            return cases_count < 50000

    @staticmethod
    def log_export_performance(cases_count: int, export_time: float, file_size: int):
        """Log export performance metrics."""
        logger.info(
            "Export Performance: %s cases in %.2fs, %.1fMB file",
            cases_count,
            export_time,
            file_size / 1024 / 1024,
        )
        
        # Calculate performance metrics
        cases_per_second = cases_count / export_time if export_time > 0 else 0
        mb_per_second = (file_size / 1024 / 1024) / export_time if export_time > 0 else 0
        
        logger.info(
            "Performance Metrics: %.0f cases/sec, %.1f MB/sec",
            cases_per_second,
            mb_per_second,
        )
