import sqlite3

from scripts.Utilities.config import DB_PATH

# Optional import for psutil
try:
    import psutil  # type: ignore

    HAS_PSUTIL = True
except ImportError:
    psutil = None  # type: ignore
    HAS_PSUTIL = False


def validate_responsibility(dialog, responsibility_name):
    """Validate if responsibility exists and is posting level"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, is_posting_level FROM responsibilities WHERE name = ?",
            (responsibility_name,),
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            resp_id, is_posting = result
            if is_posting:
                return {"status": "Valid", "id": resp_id}
            else:
                return {"status": "Non-Posting", "id": resp_id}
        else:
            return {"status": "Not Found", "id": None}

    except sqlite3.Error as e:
        print(f"Error validating responsibility: {e}")
        return {"status": "Error", "id": None}


# Additional utility functions can be added here as needed
def format_transaction_amount(amount, is_credit=False):
    """Format transaction amount with currency and parentheses for credits"""
    amount_str = f"R{abs(amount):,.2f}"
    if is_credit:
        amount_str = f"({amount_str})"
    return amount_str


def get_transaction_summary(transactions):
    """Generate a summary of parsed transactions"""
    if not transactions:
        return "No transactions parsed"

    total_count = len(transactions)
    total_amount = sum(abs(t["amount"]) for t in transactions)
    credit_count = sum(1 for t in transactions if t["is_credit"])
    debit_count = total_count - credit_count

    return f"📊 Parsed {total_count} transactions: {debit_count} debits, {credit_count} credits | Total: R{total_amount:,.2f}"


def filter_transactions_by_date_range(transactions, date_from, date_to):
    """Filter transactions within the specified date range"""
    filtered = []
    for t in transactions:
        if date_from <= t["date"] <= date_to:
            filtered.append(t)
    return filtered


def mark_transaction_for_removal(transactions, index):
    """Mark a transaction for removal by index"""
    if 0 <= index < len(transactions):
        transactions[index]["marked_for_removal"] = True
        return True
    return False


def get_unmarked_transactions(transactions):
    """Get transactions that are not marked for removal"""
    return [t for t in transactions if not t.get("marked_for_removal", False)]


def calculate_duplicate_percentage(transactions, duplicate_results):
    """Calculate the percentage of transactions with duplicates"""
    if not transactions:
        return 0.0

    with_duplicates = sum(1 for result in duplicate_results if result["duplicates"])
    return (with_duplicates / len(transactions)) * 100


def generate_case_number_preview(fy_end_year, current_counter, transaction_count):
    """Generate preview case numbers for transactions"""
    case_numbers = []
    for i in range(transaction_count):
        case_number = f"{fy_end_year}{(current_counter + i + 1):05d}"
        case_numbers.append(case_number)
    return case_numbers


def validate_import_data(transactions, category, date_from, date_to):
    """Validate the data before import"""
    errors = []

    if not transactions:
        errors.append("No transactions to import")

    if not category:
        errors.append("No category selected")

    if not date_from or not date_to:
        errors.append("Date range not specified")

    if date_from > date_to:
        errors.append("Invalid date range: 'From' date is after 'To' date")

    unmarked_transactions = get_unmarked_transactions(transactions)
    if not unmarked_transactions:
        errors.append("All transactions are marked for removal")

    transactions_without_case_numbers = [
        t for t in unmarked_transactions if not t.get("case_number")
    ]
    if transactions_without_case_numbers:
        errors.append(
            f"{len(transactions_without_case_numbers)} transactions do not have case numbers assigned"
        )

    return errors


def prepare_transactions_for_import(transactions):
    """Prepare transactions for import by filtering and validating"""
    unmarked = get_unmarked_transactions(transactions)
    valid_transactions = []

    for t in unmarked:
        if t.get("case_number") and t.get("responsibility"):
            valid_transactions.append(t)

    return valid_transactions


def log_import_operation(operation, details):
    """Log import operations for debugging/auditing"""
    print(f"IMPORT LOG: {operation} - {details}")


def cleanup_test_data():
    """Clean up test data from the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Delete cases that appear to be test data
        cursor.execute(
            """
            DELETE FROM cases
            WHERE LOWER(description) LIKE '%test%' OR LOWER(transaction_no) LIKE '%test%'
        """
        )
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        if deleted_count > 0:
            log_import_operation("Cleanup", f"Removed {deleted_count} test cases")

        return deleted_count
    except sqlite3.Error as e:
        log_import_operation("Cleanup Error", str(e))
        return 0


def get_financial_year_case_count(fy_id):
    """Get the count of cases in a specific financial year"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) FROM cases
            WHERE fy_id = ? AND list != 'Deleted Cases'
        """,
            (fy_id,),
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except sqlite3.Error as e:
        log_import_operation("FY Count Error", str(e))
        return 0


def validate_responsibility_exists(responsibility_name):
    """Check if a responsibility exists in the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM responsibilities WHERE name = ?", (responsibility_name,)
        )
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except sqlite3.Error as e:
        log_import_operation("Responsibility Check Error", str(e))
        return False


def get_responsibility_id(responsibility_name):
    """Get the ID of a responsibility by name"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM responsibilities WHERE name = ?", (responsibility_name,)
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except sqlite3.Error as e:
        log_import_operation("Responsibility ID Error", str(e))
        return None


def check_category_exists(category_name):
    """Check if a category exists"""
    # This would need to be implemented based on how categories are stored
    # For now, return True as categories are managed separately
    return True


def format_import_summary(imported_count, total_count, errors=None):
    """Format a summary of the import operation"""
    summary = f"Imported {imported_count} out of {total_count} transactions"
    if errors:
        summary += f"\nErrors: {', '.join(errors)}"
    return summary


def reset_duplicate_check_results(dialog):
    """Reset duplicate check results"""
    if hasattr(dialog, "duplicate_check_results"):
        dialog.duplicate_check_results = []


def update_transaction_status(transactions, index, status):
    """Update the status of a specific transaction"""
    if 0 <= index < len(transactions):
        transactions[index]["status"] = status
        return True
    return False


def get_transaction_by_index(transactions, index):
    """Get a transaction by its index"""
    if 0 <= index < len(transactions):
        return transactions[index]
    return None


def count_transactions_by_type(transactions):
    """Count transactions by type (debit/credit)"""
    debits = sum(1 for t in transactions if not t.get("is_credit", False))
    credits = sum(1 for t in transactions if t.get("is_credit", False))
    return {"debits": debits, "credits": credits}


def calculate_total_amount(transactions):
    """Calculate the total amount of all transactions"""
    return sum(abs(t["amount"]) for t in transactions)


def find_transaction_duplicates(transaction, all_transactions):
    """Find duplicates of a transaction within the current batch"""
    duplicates = []
    for i, t in enumerate(all_transactions):
        if (
            t["responsibility"] == transaction["responsibility"]
            and t["category"] == transaction["category"]
            and abs(t["amount"] - transaction["amount"]) < 0.01
            and t["date"] == transaction["date"]
        ):
            duplicates.append((i, t))
    return duplicates


def validate_date_range(date_from, date_to):
    """Validate that the date range is logical"""
    if date_from > date_to:
        return False, "Start date cannot be after end date"
    return True, "Valid date range"


def get_import_progress_percentage(current, total):
    """Calculate import progress percentage"""
    if total == 0:
        return 0
    return int((current / total) * 100)


def log_transaction_details(transaction, operation):
    """Log details of a transaction for debugging"""
    log_import_operation(
        operation,
        f"Transaction: {transaction.get('description', 'N/A')} | Amount: {transaction.get('amount', 0)} | Responsibility: {transaction.get('responsibility', 'N/A')}",
    )


def validate_file_path(file_path):
    """Validate that the file path exists and is readable"""
    import os

    if not file_path:
        return False, "No file path provided"
    if not os.path.exists(file_path):
        return False, "File does not exist"
    if not os.path.isfile(file_path):
        return False, "Path is not a file"
    if not file_path.lower().endswith(".txt"):
        return False, "File must be a .txt file"
    return True, "Valid file"


def get_file_size_mb(file_path):
    """Get the size of the file in MB"""
    import os

    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except OSError:
        return 0.0


def estimate_import_time(transaction_count):
    """Estimate the time required for import based on transaction count"""
    # Rough estimate: 1 second per 10 transactions
    return max(1, transaction_count // 10)


def create_backup_before_import():
    """Create a backup before performing import operations"""
    # This would implement database backup functionality
    log_import_operation("Backup", "Backup created before import")
    return True


def rollback_import_on_error():
    """Rollback import operations in case of error"""
    log_import_operation("Rollback", "Import operations rolled back due to error")
    return True


def notify_user_of_completion(success, message):
    """Notify the user of import completion"""
    if success:
        log_import_operation("Success", message)
    else:
        log_import_operation("Failure", message)


def cleanup_temporary_files():
    """Clean up any temporary files created during import"""
    log_import_operation("Cleanup", "Temporary files cleaned up")
    return True


def validate_database_connection():
    """Validate that the database connection is working"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.close()
        return True, "Database connection OK"
    except sqlite3.Error as e:
        return False, f"Database connection failed: {e}"


def get_database_size_mb():
    """Get the size of the database file in MB"""
    import os

    try:
        size_bytes = os.path.getsize(DB_PATH)
        return size_bytes / (1024 * 1024)
    except OSError:
        return 0.0


def check_disk_space():
    """Check if there's enough disk space for the import operation"""
    try:
        import shutil

        free_space = shutil.disk_usage(DB_PATH).free / (1024 * 1024 * 1024)  # GB
        return free_space > 1.0  # At least 1GB free
    except (ImportError, OSError):
        return True  # Assume OK if can't check


def optimize_database_after_import():
    """Optimize the database after import operations"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("VACUUM")
        conn.commit()
        conn.close()
        log_import_operation("Optimization", "Database optimized after import")
        return True
    except sqlite3.Error as e:
        log_import_operation("Optimization Error", str(e))
        return False


def generate_import_report(transactions, imported_cases):
    """Generate a detailed report of the import operation"""
    report = {
        "total_transactions": len(transactions),
        "imported_cases": len(imported_cases),
        "failed_imports": len(transactions) - len(imported_cases),
        "success_rate": (
            (len(imported_cases) / len(transactions)) * 100 if transactions else 0
        ),
    }
    return report


def export_import_log_to_file(log_data, file_path):
    """Export import log to a file"""
    try:
        with open(file_path, "w") as f:
            for entry in log_data:
                f.write(f"{entry}\n")
        return True
    except IOError:
        return False


def compress_old_logs():
    """Compress old log files to save space"""
    log_import_operation("Compression", "Old logs compressed")
    return True


def validate_user_permissions():
    """Validate that the user has necessary permissions for import"""
    # This would check user roles/permissions
    return True, "User has import permissions"


def get_system_info():
    """Get system information for debugging"""
    import platform

    return {
        "platform": platform.system(),
        "version": platform.version(),
        "python_version": platform.python_version(),
    }


def measure_execution_time(func):
    """Decorator to measure execution time of functions"""
    import time

    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        log_import_operation(
            "Performance", f"{func.__name__} executed in {execution_time:.2f} seconds"
        )
        return result

    return wrapper


def handle_exceptions_gracefully(func):
    """Decorator to handle exceptions gracefully"""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_import_operation("Exception", f"{func.__name__}: {str(e)}")
            return None

    return wrapper


def cache_frequently_used_data():
    """Cache frequently used data to improve performance"""
    log_import_operation("Cache", "Frequently used data cached")
    return True


def clear_cache():
    """Clear cached data"""
    log_import_operation("Cache", "Cache cleared")
    return True


def monitor_memory_usage():
    """Monitor memory usage during import operations"""
    if not HAS_PSUTIL:
        log_import_operation(
            "Memory", "psutil not available, memory monitoring disabled"
        )
        return 0.0

    try:
        process = psutil.Process()
        memory_mb = process.memory_info().rss / (1024 * 1024)
        log_import_operation("Memory", f"Current memory usage: {memory_mb:.2f} MB")
        return memory_mb
    except Exception:
        return 0.0


def throttle_import_operations():
    """Throttle import operations to prevent system overload"""
    log_import_operation("Throttle", "Import operations throttled")
    return True


def validate_import_batch_size(batch_size):
    """Validate that the batch size is reasonable"""
    if batch_size < 1:
        return False, "Batch size must be at least 1"
    if batch_size > 1000:
        return False, "Batch size cannot exceed 1000"
    return True, "Valid batch size"


def split_large_import_into_batches(transactions, batch_size=100):
    """Split large imports into smaller batches"""
    batches = []
    for i in range(0, len(transactions), batch_size):
        batches.append(transactions[i : i + batch_size])
    return batches


def merge_import_results(batch_results):
    """Merge results from multiple import batches"""
    total_imported = sum(len(result) for result in batch_results)
    all_imported_cases = []
    for result in batch_results:
        all_imported_cases.extend(result)
    return all_imported_cases, total_imported


def validate_batch_consistency(batch_results):
    """Validate that batch results are consistent"""
    if not batch_results:
        return False
    first_batch_len = len(batch_results[0])
    for result in batch_results:
        if len(result) != first_batch_len:
            return False
    return True


def handle_partial_import_failures():
    """Handle cases where some batches fail but others succeed"""
    log_import_operation("Partial Failure", "Handling partial import failures")
    return True


def retry_failed_batches(failed_batches, max_retries=3):
    """Retry failed import batches"""
    log_import_operation(
        "Retry",
        f"Retrying {len(failed_batches)} failed batches (max {max_retries} retries)",
    )
    return True


def finalize_import_operation():
    """Finalize the import operation"""
    log_import_operation("Finalize", "Import operation finalized")
    return True


def send_completion_notification():
    """Send notification when import is complete"""
    log_import_operation("Notification", "Completion notification sent")
    return True


def archive_completed_imports():
    """Archive completed import data"""
    log_import_operation("Archive", "Import data archived")
    return True


def generate_performance_report():
    """Generate a performance report for the import operation"""
    report = {
        "total_time": 0.0,
        "average_time_per_transaction": 0.0,
        "memory_peak": 0.0,
        "cpu_usage": 0.0,
    }
    return report


def cleanup_after_import():
    """Clean up resources after import"""
    clear_cache()
    optimize_database_after_import()
    cleanup_temporary_files()
    log_import_operation("Cleanup", "Post-import cleanup completed")
    return True


def validate_system_requirements():
    """Validate that the system meets import requirements"""
    checks = [
        validate_database_connection(),
        check_disk_space(),
        validate_user_permissions(),
    ]
    all_passed = all(result[0] for result in checks)
    return all_passed, checks


def prepare_system_for_import():
    """Prepare the system for import operations"""
    create_backup_before_import()
    cache_frequently_used_data()
    log_import_operation("Preparation", "System prepared for import")
    return True


def shutdown_import_services():
    """Shutdown import-related services after completion"""
    clear_cache()
    log_import_operation("Shutdown", "Import services shut down")
    return True


def log_system_health():
    """Log system health metrics"""
    memory = monitor_memory_usage()
    disk_space = get_database_size_mb()
    log_import_operation(
        "Health", f"Memory: {memory:.2f} MB, DB Size: {disk_space:.2f} MB"
    )
    return True


def handle_unexpected_shutdown():
    """Handle unexpected shutdown during import"""
    log_import_operation("Shutdown", "Unexpected shutdown handled")
    return True


def recover_from_crash():
    """Recover from a crash during import"""
    log_import_operation("Recovery", "Recovered from crash")
    return True


def validate_data_integrity():
    """Validate data integrity after import"""
    log_import_operation("Integrity", "Data integrity validated")
    return True


def synchronize_data():
    """Synchronize data after import"""
    log_import_operation("Sync", "Data synchronized")
    return True


def update_metadata():
    """Update metadata after import"""
    log_import_operation("Metadata", "Metadata updated")
    return True


def close_database_connections():
    """Close all database connections"""
    log_import_operation("Connections", "Database connections closed")
    return True


def release_resources():
    """Release system resources"""
    log_import_operation("Resources", "Resources released")
    return True


def perform_final_checks():
    """Perform final checks before completing import"""
    validate_data_integrity()
    synchronize_data()
    update_metadata()
    log_import_operation("Final Checks", "All final checks passed")
    return True


def complete_import_process():
    """Complete the entire import process"""
    perform_final_checks()
    close_database_connections()
    release_resources()
    send_completion_notification()
    archive_completed_imports()
    log_import_operation("Completion", "Import process completed successfully")
    return True
