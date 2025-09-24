import os
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox
from scripts.Utilities.financial_utils import get_financial_year
from scripts.Utilities.optimized_excel_utils import StreamingExcelExporter, create_optimized_excel_export
from scripts.Utilities.performance_profiler import memory_profiler
from scripts.Utilities.optimization_manager import get_optimization_manager


class ViewCasesUtils:
    @staticmethod
    def export_to_excel(dialog):
        """Export the current case list to Excel format using memory-efficient streaming."""
        try:
            # Check if there are cases to export
            if dialog.case_table.rowCount() == 0:
                QMessageBox.warning(dialog, "No Data", "No cases to export.")
                return

            # Get optimization manager and auto-enable for large exports
            optimization_manager = get_optimization_manager()
            data_size = dialog.case_table.rowCount()
            
            # Auto-enable optimizations for large exports
            optimizations_enabled = optimization_manager.auto_enable_for_large_dataset(data_size, "export")
            
            if optimizations_enabled:
                # Show optimization notification
                QMessageBox.information(
                    dialog,
                    "Performance Optimization",
                    f"Large dataset detected ({data_size} cases).\n\n"
                    "Performance optimizations have been automatically enabled:\n"
                    "• Streaming Excel exports\n"
                    "• Memory-efficient processing\n\n"
                    "This will provide better performance and memory usage."
                )

            # Take memory snapshot before export
            memory_profiler.take_snapshot("before_export")

            # Get current list filter for filename
            current_list = dialog.list_filter_combo.currentText().replace(" ", "_")

            # Create year folder
            from scripts.Utilities.financial_utils import create_year_folder
            year_folder = create_year_folder(get_financial_year())
            export_dir = os.path.join(year_folder, "Exports")
            os.makedirs(export_dir, exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"List_Export_{current_list}_{timestamp}.xlsx"
            filepath = os.path.join(export_dir, filename)

            # Extract data using memory-efficient generator
            def extract_table_data():
                """Generator to extract table data without loading everything into memory."""
                headers = []
                
                # Get headers from table horizontal header
                for col in range(dialog.case_table.columnCount()):
                    header_item = dialog.case_table.horizontalHeaderItem(col)
                    if header_item:
                        headers.append(header_item.text())

                # Yield headers first
                yield {"type": "headers", "data": headers}

                # Get data rows - iterate through all table rows and columns
                for row in range(dialog.case_table.rowCount()):
                    row_data = {}
                    for col in range(dialog.case_table.columnCount()):
                        item = dialog.case_table.item(row, col)
                        if item:
                            # Handle special case for Case No (extract transaction number from Qt.UserRole)
                            if col == 0:  # Case No column
                                transaction_no = item.data(Qt.UserRole)
                                row_data[headers[col]] = (
                                    transaction_no if transaction_no else item.text()
                                )
                            else:
                                row_data[headers[col]] = item.text()
                        else:
                            # Check for widget (like buttons) - extract text if available
                            widget = dialog.case_table.cellWidget(row, col)
                            if widget and hasattr(widget, "text"):
                                row_data[headers[col]] = widget.text()
                            else:
                                row_data[headers[col]] = ""

                    yield {"type": "row", "data": row_data}

            # Use optimized Excel exporter
            exporter = StreamingExcelExporter(chunk_size=1000)
            
            # Convert generator to iterator for streaming export
            def cases_iterator():
                headers = None
                for item in extract_table_data():
                    if item["type"] == "headers":
                        headers = item["data"]
                    elif item["type"] == "row":
                        yield item["data"]

            # Export using streaming
            exported_file = exporter.export_cases_to_excel_streaming(
                cases_iterator(), 
                filepath, 
                f"{current_list} Cases"
            )

            # Take memory snapshot after export
            memory_profiler.take_snapshot("after_export")

            # Show success message
            QMessageBox.information(
                dialog,
                "Export Successful",
                f"Case list exported successfully using optimized streaming!\n\n"
                f"File: {filename}\n"
                f"Location: {export_dir}\n"
                f"Cases exported: {dialog.case_table.rowCount()}",
            )

        except ImportError:
            # Handle missing dependencies with user-friendly error
            QMessageBox.critical(
                dialog,
                "Missing Dependencies",
                "Excel export requires openpyxl.\n\n"
                "Please install with: pip install openpyxl",
            )
        except Exception as e:
            # Catch any other export errors and show to user
            QMessageBox.critical(
                dialog, "Export Error", f"Failed to export to Excel: {str(e)}"
            )

    @staticmethod
    def validate_view_data(data):
        """Validate data for view cases functionality"""
        if not data:
            return False, "No data provided"
        if not isinstance(data, dict):
            return False, "Data must be a dictionary"
        required_keys = ["responsibilities", "fy_filter", "list_filter"]
        for key in required_keys:
            if key not in data:
                return False, f"Missing required key: {key}"
        return True, "Data is valid"

    @staticmethod
    def format_case_display(case_data):
        """Format case data for display in the table"""
        formatted = {}
        formatted["case_no"] = case_data.get(
            "base_transaction_no", case_data.get("transaction_no", "N/A")
        )
        formatted["date_reported"] = case_data.get("date_reported", "N/A")
        formatted["category"] = case_data.get("category", "N/A")
        formatted["amount"] = case_data.get("amount", 0.0)
        formatted["list"] = case_data.get("list", "N/A")
        formatted["status"] = case_data.get("assessment_status", "N/A")
        formatted["todo"] = (
            "Yes"
            if case_data.get("bas_payment_no") or case_data.get("bas_journal_no")
            else "No"
        )
        return formatted

    @staticmethod
    def get_case_filter_conditions(selected_list):
        """Get SQL conditions for different list filters"""
        from scripts.Utilities.shared_case_filter_utils import get_list_filter_conditions
        
        return get_list_filter_conditions(selected_list)

    @staticmethod
    def calculate_case_totals(cases):
        """Calculate totals for a list of cases"""
        total_amount = 0.0
        total_cases = len(cases)
        categories = {}
        statuses = {}

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
    def generate_case_report(cases, report_type):
        """Generate a report for cases"""
        totals = ViewCasesUtils.calculate_case_totals(cases)

        report = f"Case Report - {report_type}\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += f"Total Cases: {totals['total_cases']}\n"
        report += f"Total Amount: R {totals['total_amount']:,.2f}\n\n"

        if totals["categories"]:
            report += "Categories:\n"
            for cat, count in totals["categories"].items():
                report += f"  {cat}: {count}\n"

        if totals["statuses"]:
            report += "\nStatuses:\n"
            for stat, count in totals["statuses"].items():
                report += f"  {stat}: {count}\n"

        return report

    @staticmethod
    def filter_cases_by_responsibility(cases, resp_ids):
        """Filter cases by responsibility IDs"""
        if not resp_ids:
            return cases
        return [case for case in cases if case.get("responsibility_id") in resp_ids]

    @staticmethod
    def sort_cases(cases, sort_by="date_reported", ascending=True):
        """Sort cases by specified field"""

        def sort_key(case):
            value = case.get(sort_by)
            if value is None:
                return "" if ascending else "z"
            return value

        return sorted(cases, key=sort_key, reverse=not ascending)

    @staticmethod
    def search_cases(cases, search_term):
        """Search cases by transaction number or category"""
        if not search_term:
            return cases

        search_term = search_term.lower()
        filtered = []
        for case in cases:
            transaction_no = str(case.get("transaction_no", "")).lower()
            category = str(case.get("category", "")).lower()
            if search_term in transaction_no or search_term in category:
                filtered.append(case)
        return filtered

    @staticmethod
    def validate_export_data(data):
        """Validate data before export"""
        if not data:
            return False, "No data to export"

        if not isinstance(data, list):
            return False, "Data must be a list of cases"

        if len(data) == 0:
            return False, "No cases to export"

        # Check if all items are dictionaries
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                return False, f"Item {i} is not a valid case dictionary"

        return True, "Data is valid for export"

    @staticmethod
    def format_currency_for_export(amount):
        """Format currency amount for export"""
        if amount is None:
            return "R 0.00"
        try:
            return f"R {float(amount):,.2f}"
        except (ValueError, TypeError):
            return "R 0.00"

    @staticmethod
    def get_export_filename(list_name):
        """Generate export filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_list_name = list_name.replace(" ", "_").replace("/", "_")
        return f"List_Export_{safe_list_name}_{timestamp}.xlsx"

    @staticmethod
    def create_export_directory(year):
        """Create export directory for the year"""
        export_dir = os.path.join("data", str(year), "Exports")
        os.makedirs(export_dir, exist_ok=True)
        return export_dir

    @staticmethod
    def apply_excel_formatting(worksheet, df):
        """Apply formatting to Excel worksheet"""
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = (
                column[0].column_letter if hasattr(column[0], "column_letter") else None
            )
            if column_letter is None:
                continue

            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

        return worksheet

    @staticmethod
    def validate_case_selection(selected_items):
        """Validate selected case items"""
        if not selected_items:
            return False, "No cases selected"

        valid_items = []
        for item in selected_items:
            if hasattr(item, "data") and callable(item.data):
                valid_items.append(item)
            else:
                return False, "Invalid case item selected"

        return True, valid_items

    @staticmethod
    def get_case_details_from_selection(selected_item):
        """Extract case details from selected table item"""
        if not selected_item:
            return None

        transaction_no = selected_item.data(Qt.UserRole)
        row = selected_item.row()

        return {"transaction_no": transaction_no, "row": row}

    @staticmethod
    def build_case_query(base_conditions, params, fy_id=None, resp_ids=None):
        """Build SQL query for case retrieval"""
        conditions = base_conditions.copy()

        if fy_id:
            conditions.append("fy_id = ?")
            params.append(fy_id)

        if resp_ids:
            placeholders = ",".join("?" for _ in resp_ids)
            conditions.append(f"responsibility_id IN ({placeholders})")
            params.extend(resp_ids)

        where_clause = " AND ".join(conditions)
        query = f"SELECT * FROM cases WHERE {where_clause}"

        return query, params

    @staticmethod
    def parse_case_data(row_data):
        """Parse raw case data from database"""
        if not row_data:
            return None

        case_dict = {
            "id": row_data[0],
            "transaction_no": row_data[1],
            "base_transaction_no": row_data[2],
            "date_reported": row_data[3],
            "category": row_data[4],
            "amount": row_data[5],
            "assessment_status": row_data[6],
            "lc_status": row_data[7],
            "suffixes": row_data[8],
            "responsibility_id": row_data[9],
        }

        return case_dict

    @staticmethod
    def determine_display_values(case_dict, selected_list):
        """Determine display values based on list filter"""
        display_list = selected_list
        display_status = case_dict.get("assessment_status", "Unknown")

        if selected_list == "Lead Schedule":
            display_status = case_dict.get("lc_status", "Awaiting LC determination")
        elif selected_list in ["Recovered", "Write-Off Recommended", "Written Off"]:
            display_status = selected_list.replace("Write-Off", "Write Off")

        return display_list, display_status

    @staticmethod
    def check_case_permissions(case_dict, user_permissions):
        """Check if user has permissions to view/edit case"""
        if not user_permissions:
            return False

        # Implement permission checking logic here
        # For now, return True
        return True

    @staticmethod
    def log_case_action(action, case_id, user_id):
        """Log case-related actions"""
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp}: {action} on case {case_id} by user {user_id}"
        print(log_entry)  # In real app, this would write to a log file

    @staticmethod
    def validate_date_range(start_date, end_date):
        """Validate date range for filtering"""
        if start_date and end_date:
            if start_date > end_date:
                return False, "Start date cannot be after end date"
        return True, "Date range is valid"

    @staticmethod
    def format_date_for_display(date_str):
        """Format date string for display"""
        if not date_str:
            return "N/A"
        try:
            date_obj = datetime.fromisoformat(date_str)
            return date_obj.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return str(date_str)

    @staticmethod
    def calculate_percentage(part, total):
        """Calculate percentage safely"""
        if total == 0:
            return 0.0
        return (part / total) * 100

    @staticmethod
    def truncate_text(text, max_length=50):
        """Truncate text to maximum length"""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    @staticmethod
    def sanitize_filename(filename):
        """Sanitize filename for safe file system use"""
        import re

        return re.sub(r'[<>:"/\\|?*]', "_", filename)

    @staticmethod
    def get_file_size_mb(filepath):
        """Get file size in MB"""
        if not os.path.exists(filepath):
            return 0.0
        size_bytes = os.path.getsize(filepath)
        return size_bytes / (1024 * 1024)

    @staticmethod
    def validate_file_path(filepath):
        """Validate file path for security"""
        if not filepath:
            return False, "File path is empty"

        # Check for directory traversal attempts
        if ".." in filepath or filepath.startswith("/"):
            return False, "Invalid file path"

        return True, "File path is valid"
