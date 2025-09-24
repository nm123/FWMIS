"""
Optimized import utilities for memory-efficient processing of large datasets.
Designed for low-end hardware (4-8GB RAM, old CPUs).
"""

import csv
import logging
import sqlite3
from typing import Iterator, List, Dict, Any, Optional
from contextlib import contextmanager
import os
import gc

logger = logging.getLogger(__name__)

# Memory-efficient chunk sizes for different hardware configurations
CHUNK_SIZES = {
    'low_memory': 1000,    # 4GB RAM
    'medium_memory': 5000, # 8GB RAM  
    'high_memory': 10000   # 16GB+ RAM
}

def get_optimal_chunk_size() -> int:
    """Determine optimal chunk size based on available memory."""
    try:
        import psutil
        available_memory_gb = psutil.virtual_memory().available / (1024**3)
        
        if available_memory_gb < 4:
            return CHUNK_SIZES['low_memory']
        elif available_memory_gb < 8:
            return CHUNK_SIZES['medium_memory']
        else:
            return CHUNK_SIZES['high_memory']
    except ImportError:
        # Fallback to conservative chunk size
        return CHUNK_SIZES['low_memory']

@contextmanager
def memory_efficient_db_connection():
    """Context manager for memory-efficient database operations."""
    from scripts.Utilities.db_utils import get_db_connection
    
    conn_ctx = get_db_connection()
    conn = conn_ctx.__enter__()
    try:
        # Optimize SQLite for bulk operations
        conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA mmap_size = 268435456")  # 256MB memory mapping
        conn.execute("PRAGMA synchronous = NORMAL")  # Faster than FULL
        yield conn
    finally:
        try:
            conn_ctx.__exit__(None, None, None)
        except Exception:
            pass

class StreamingCSVProcessor:
    """Memory-efficient CSV processor using streaming."""
    
    def __init__(self, file_path: str, chunk_size: Optional[int] = None):
        self.file_path = file_path
        self.chunk_size = chunk_size or get_optimal_chunk_size()
        
    def process_chunks(self) -> Iterator[List[Dict[str, Any]]]:
        """Process CSV file in memory-efficient chunks."""
        try:
            with open(self.file_path, 'r', encoding='utf-8', newline='') as file:
                reader = csv.DictReader(file)
                chunk = []
                
                for row in reader:
                    chunk.append(row)
                    
                    if len(chunk) >= self.chunk_size:
                        yield chunk
                        chunk = []
                        # Force garbage collection to free memory
                        gc.collect()
                
                # Yield remaining rows
                if chunk:
                    yield chunk
                    
        except Exception as e:
            logger.error(f"Error processing CSV chunks: {e}")
            raise

class OptimizedBASParser:
    """Memory-efficient BAS file parser with streaming."""
    
    def __init__(self, chunk_size: Optional[int] = None):
        self.chunk_size = chunk_size or get_optimal_chunk_size()
        self.transactions = []
        
    def parse_file_streaming(self, file_path: str, date_from=None, date_to=None) -> Iterator[List[Dict]]:
        """Parse BAS file in streaming fashion to avoid loading entire file into memory."""
        import re
        
        current_responsibility = None
        current_item = None
        chunk = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.rstrip()
                    
                    # Process line and extract transaction if valid
                    transaction = self._process_line(line, current_responsibility, current_item, date_from, date_to)
                    
                    if transaction:
                        chunk.append(transaction)
                    
                    # Update context variables
                    current_responsibility, current_item = self._update_context(line, current_responsibility, current_item)
                    
                    # Yield chunk when it reaches optimal size
                    if len(chunk) >= self.chunk_size:
                        yield chunk
                        chunk = []
                        gc.collect()  # Free memory
                
                # Yield remaining transactions
                if chunk:
                    yield chunk
                    
        except Exception as e:
            logger.error(f"Error parsing BAS file: {e}")
            raise
    
    def _process_line(self, line: str, current_responsibility: str, current_item: str, date_from, date_to) -> Optional[Dict]:
        """Process a single line and return transaction if valid."""
        import re
        from datetime import datetime
        
        # Check for transaction lines (AP, GJ, CL)
        trans_match = re.match(
            r"\s*(AP|GJ|CL)\s+(\d+)\s+(.+?)\s+(.+?)\s+(\d{2}/\d{2}/\d{4})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})",
            line,
        )
        
        if trans_match and current_responsibility and current_item:
            trans_type = trans_match.group(1)
            trans_number = trans_match.group(2)
            description = trans_match.group(3).strip()
            user_field = trans_match.group(4).strip()
            user_name = user_field.split()[-1] if user_field else ""
            user_date = trans_match.group(5)
            debit = trans_match.group(6).replace(",", "")
            credit = trans_match.group(7).replace(",", "")

            try:
                date_obj = datetime.strptime(user_date, "%d/%m/%Y").date()
                
                # Validate date range
                if date_from and date_to:
                    if not (date_from <= date_obj <= date_to):
                        return None
                
                amount = float(debit) if float(debit) > 0 else -float(credit)
                
                return {
                    "responsibility": current_responsibility,
                    "item": current_item,
                    "type": trans_type,
                    "number": trans_number,
                    "description": description,
                    "date": date_obj,
                    "user_id": user_name,
                    "amount": amount,
                    "is_credit": amount < 0,
                }
            except ValueError:
                return None
        
        return None
    
    def _update_context(self, line: str, current_responsibility: str, current_item: str) -> tuple:
        """Update parsing context variables."""
        import re
        
        # Check for responsibility line (R 007)
        resp_match = re.match(r"\s*R\s+(\d+)\s+(.+)", line)
        if resp_match:
            current_responsibility = resp_match.group(2).strip()
            return current_responsibility, current_item

        # Check for item line (I 005)
        item_match = re.match(
            r"\s*I\s+(\d+)\s+(.+?)\s+\d+\.\d{2}\s+\d+\.\d{2}\s*$", line
        )
        if item_match:
            current_item = item_match.group(2).strip()
            return current_responsibility, current_item
        
        return current_responsibility, current_item

class BatchDatabaseInserter:
    """Memory-efficient batch database inserter."""
    
    def __init__(self, chunk_size: Optional[int] = None):
        self.batch_size = chunk_size or get_optimal_chunk_size()
        
    def insert_cases_batch(self, cases: List[Dict], fy_id: int) -> List[str]:
        """Insert cases in optimized batches with proper transaction handling."""
        inserted_case_numbers = []
        
        try:
            with memory_efficient_db_connection() as conn:
                cursor = conn.cursor()
                
                # Use prepared statement for better performance
                insert_sql = """
                    INSERT INTO cases (
                        transaction_no, base_transaction_no, date_incurred, date_identified, date_reported,
                        description, bas_payment_no, bas_payment_date, persal_no, category,
                        responsibility_id, amount, source_document, minutes, evidence_path,
                        status, list, assessment_assessed_by, assessment_date, assessment_result,
                        fy_id, period_id, criminal_charges, disciplinary_process, loss_recovery,
                        prevention_steps, original_list, attachments, shared_document_id, 
                        bas_journal_no, bas_journal_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                # Process in batches
                for i in range(0, len(cases), self.batch_size):
                    batch = cases[i:i + self.batch_size]
                    
                    # Begin transaction for this batch
                    cursor.execute("BEGIN TRANSACTION")
                    
                    try:
                        for case in batch:
                            cursor.execute(insert_sql, (
                                case.get("transaction_no"),
                                case.get("base_transaction_no"),
                                case.get("date_incurred"),
                                case.get("date_identified"),
                                case.get("date_reported"),
                                case.get("description"),
                                case.get("bas_payment_no"),
                                case.get("bas_payment_date"),
                                case.get("persal_no"),
                                case.get("category"),
                                case.get("responsibility_id"),
                                case.get("amount"),
                                case.get("source_document"),
                                case.get("minutes"),
                                case.get("evidence_path"),
                                case.get("status"),
                                case.get("list"),
                                case.get("assessment_assessed_by"),
                                case.get("assessment_date"),
                                case.get("assessment_result"),
                                fy_id,
                                case.get("period_id"),
                                case.get("criminal_charges", "N/A"),
                                case.get("disciplinary_process", "N/A"),
                                case.get("loss_recovery", "N/A"),
                                case.get("prevention_steps", "N/A"),
                                case.get("original_list"),
                                case.get("attachments", "[]"),
                                case.get("shared_document_id"),
                                case.get("bas_journal_no"),
                                case.get("bas_journal_date"),
                            ))
                            
                            inserted_case_numbers.append(case.get("transaction_no"))
                        
                        # Commit batch
                        cursor.execute("COMMIT")
                        logger.info(f"Successfully inserted batch of {len(batch)} cases")
                        
                    except Exception as e:
                        cursor.execute("ROLLBACK")
                        logger.error(f"Error inserting batch: {e}")
                        raise
                    
                    # Force garbage collection between batches
                    gc.collect()
                
        except Exception as e:
            logger.error(f"Error in batch insert: {e}")
            raise
        
        return inserted_case_numbers

def create_performance_indexes():
    """Create optimized indexes for better query performance."""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_cases_fy_id ON cases(fy_id)",
        "CREATE INDEX IF NOT EXISTS idx_cases_responsibility_id ON cases(responsibility_id)",
        "CREATE INDEX IF NOT EXISTS idx_cases_date_incurred ON cases(date_incurred)",
        "CREATE INDEX IF NOT EXISTS idx_cases_amount ON cases(amount)",
        "CREATE INDEX IF NOT EXISTS idx_cases_category ON cases(category)",
        "CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status)",
        "CREATE INDEX IF NOT EXISTS idx_cases_list ON cases(list)",
        "CREATE INDEX IF NOT EXISTS idx_cases_period_id ON cases(period_id)",
        "CREATE INDEX IF NOT EXISTS idx_responsibilities_parent_id ON responsibilities(parent_id)",
        "CREATE INDEX IF NOT EXISTS idx_financial_years_status ON financial_years(status)",
        "CREATE INDEX IF NOT EXISTS idx_periods_fy_id ON periods(fy_id)",
    ]
    
    try:
        with memory_efficient_db_connection() as conn:
            cursor = conn.cursor()
            for index_sql in indexes:
                cursor.execute(index_sql)
            conn.commit()
            logger.info("Performance indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        raise

def optimize_database_settings():
    """Apply database optimizations for better performance."""
    optimizations = [
        "PRAGMA cache_size = -128000",  # 128MB cache
        "PRAGMA temp_store = MEMORY",
        "PRAGMA mmap_size = 536870912",  # 512MB memory mapping
        "PRAGMA synchronous = NORMAL",
        "PRAGMA journal_mode = WAL",
        "PRAGMA foreign_keys = ON",
    ]
    
    try:
        with memory_efficient_db_connection() as conn:
            cursor = conn.cursor()
            for pragma in optimizations:
                cursor.execute(pragma)
            conn.commit()
            logger.info("Database optimizations applied successfully")
    except Exception as e:
        logger.error(f"Error applying database optimizations: {e}")
        raise

def memory_usage_monitor():
    """Monitor memory usage and provide warnings."""
    try:
        import psutil
        memory = psutil.virtual_memory()
        
        if memory.percent > 85:
            logger.warning(f"High memory usage: {memory.percent}%")
            return False
        elif memory.percent > 95:
            logger.error(f"Critical memory usage: {memory.percent}%")
            return False
        
        return True
    except ImportError:
        return True  # psutil not available, assume OK

def adaptive_chunk_size(current_chunk_size: int, success_rate: float) -> int:
    """Adaptively adjust chunk size based on success rate."""
    if success_rate > 0.95:
        # Increase chunk size for better performance
        return min(current_chunk_size * 2, CHUNK_SIZES['high_memory'])
    elif success_rate < 0.8:
        # Decrease chunk size to avoid memory issues
        return max(current_chunk_size // 2, CHUNK_SIZES['low_memory'])
    else:
        return current_chunk_size
