#!/usr/bin/env python3
"""
Test Data Generator for FWMIS

This script generates test data including:
- Dummy BAS files for import testing
- Sample PDF evidence files
- Test cases in the database
- Performance test data sets

Usage:
    python test_data_generator.py --bas-files 5     # Generate 5 BAS files
    python test_data_generator.py --cases 100       # Generate 100 test cases
    python test_data_generator.py --evidence 10     # Generate 10 dummy PDF files
"""

import os
import random
import sqlite3
import argparse
from datetime import datetime, date
from pathlib import Path


class FWMISTestDataGenerator:
    """Generates test data for FWMIS automated testing"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.data_dir = self.project_root / "data"
        self.test_data_dir = self.data_dir / "test_data"

        # Sample data pools
        self.vendor_names = [
            "ABC Supplies Ltd", "XYZ Corporation", "Global Tech Solutions",
            "Metro Construction", "City Services Inc", "National Distributors",
            "Regional Traders", "Local Manufacturing Co", "International Imports",
            "Domestic Exports Ltd", "Premier Services", "Elite Contractors"
        ]

        self.categories = [
            "Professional Services", "Construction Materials", "IT Equipment",
            "Maintenance Services", "Consulting Fees", "Training Costs",
            "Travel Expenses", "Office Supplies", "Utilities", "Insurance"
        ]

    def setup_test_directory(self):
        """Create test data directory"""
        self.test_data_dir.mkdir(exist_ok=True)
        print(f"📁 Test data directory: {self.test_data_dir}")

    def generate_bas_file(self, filename=None, num_transactions=50):
        """Generate a dummy BAS file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_bas_{timestamp}.TXT"

        filepath = self.test_data_dir / filename

        print(f"📝 Generating BAS file: {filepath} ({num_transactions} transactions)")

        with open(filepath, 'w', encoding='utf-8') as f:
            # Write header
            f.write("Transaction_No|Amount|Vendor_Name|Date|Category|Description\n")

            # Generate transactions
            for i in range(num_transactions):
                transaction_no = "04d"
                amount = round(random.uniform(1000, 50000), 2)
                vendor = random.choice(self.vendor_names)
                transaction_date = self._random_date()
                category = random.choice(self.categories)
                description = f"Test transaction {i+1} for {category.lower()}"

                line = ",".join([
                    transaction_no,
                    ".2f",
                    vendor,
                    transaction_date,
                    category,
                    description
                ])
                f.write(line + "\n")

        print(f"✅ Generated BAS file with {num_transactions} transactions")
        return filepath

    def _random_date(self):
        """Generate a random date in the current financial year"""
        from datetime import timedelta

        year = datetime.now().year
        start_date = date(year, 4, 1)  # April 1st (start of financial year)
        end_date = date.today()

        # Generate random date between start and end
        days_diff = (end_date - start_date).days
        if days_diff <= 0:
            # If we're before April, use last year's financial year
            start_date = date(year - 1, 4, 1)
            end_date = date(year, 3, 31)
            days_diff = (end_date - start_date).days

        if days_diff > 0:
            random_days = random.randint(0, days_diff)
            random_date = start_date + timedelta(days=random_days)
        else:
            # Fallback to a fixed recent date
            random_date = date.today() - timedelta(days=random.randint(1, 30))

        return random_date.strftime("%Y-%m-%d")

    def generate_test_cases(self, num_cases=100, db_path=None):
        """Generate test cases directly in the database"""
        if db_path is None:
            db_path = self.data_dir / "fruitless.db"

        if not db_path.exists():
            print(f"❌ Database not found: {db_path}")
            return

        print(f"🗃️  Generating {num_cases} test cases in database")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if fy_id 1 exists, if not create it
        cursor.execute("SELECT id FROM financial_years WHERE year = '2025-2026'")
        fy_result = cursor.fetchone()
        if fy_result:
            fy_id = fy_result[0]
        else:
            cursor.execute("INSERT INTO financial_years (year, is_active) VALUES ('2025-2026', 1)")
            fy_id = cursor.lastrowid

        # Generate cases
        inserted_count = 0
        for i in range(num_cases):
            transaction_no = "04d"

            # Check if transaction already exists
            cursor.execute("SELECT id FROM cases WHERE transaction_no = ?", (transaction_no,))
            if cursor.fetchone():
                continue  # Skip duplicates

            amount = round(random.uniform(1000, 100000), 2)
            vendor = random.choice(self.vendor_names)
            list_name = random.choice(['Checklist', 'Lead Schedule'])
            status = random.choice(['Alleged', 'Confirmed', 'Finalized'])
            is_finalized = 1 if status == 'Finalized' else 0

            try:
                cursor.execute("""
                    INSERT INTO cases (transaction_no, list, status, fy_id, amount, vendor_name, is_finalized)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (transaction_no, list_name, status, fy_id, amount, vendor, is_finalized))
                inserted_count += 1
            except sqlite3.IntegrityError:
                continue  # Skip if still a duplicate

        conn.commit()
        conn.close()

        print(f"✅ Generated {inserted_count} test cases in database")

    def generate_dummy_pdf(self, filename=None):
        """Generate a dummy PDF file for evidence testing"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_evidence_{timestamp}.pdf"

        filepath = self.test_data_dir / filename

        print(f"📄 Generating dummy PDF: {filepath}")

        # Create a minimal PDF (this is a very basic text-based PDF)
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test Evidence Document) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000274 00000 n
0000000373 00000 n
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
459
%%EOF"""

        with open(filepath, 'wb') as f:
            f.write(pdf_content)

        print(f"✅ Generated dummy PDF: {filepath}")
        return filepath

    def generate_performance_dataset(self, size="small"):
        """Generate datasets for performance testing"""
        sizes = {
            "small": 100,
            "medium": 1000,
            "large": 10000
        }

        num_cases = sizes.get(size, 100)
        print(f"⚡ Generating performance dataset: {size} ({num_cases} cases)")

        # Generate BAS file
        bas_file = self.generate_bas_file(f"perf_test_{size}.TXT", num_cases)

        # Generate cases in database
        self.generate_test_cases(num_cases)

        print(f"✅ Performance dataset '{size}' generated")
        return bas_file

    def cleanup_test_data(self):
        """Clean up generated test data"""
        if self.test_data_dir.exists():
            import shutil
            shutil.rmtree(self.test_data_dir)
            print(f"🗑️  Cleaned up test data directory: {self.test_data_dir}")
        else:
            print("ℹ️  No test data directory to clean up")


def main():
    parser = argparse.ArgumentParser(description="FWMIS Test Data Generator")
    parser.add_argument("--bas-files", type=int, help="Number of BAS files to generate")
    parser.add_argument("--cases", type=int, help="Number of test cases to generate in database")
    parser.add_argument("--evidence", type=int, help="Number of dummy PDF files to generate")
    parser.add_argument("--performance", choices=["small", "medium", "large"],
                       help="Generate performance test dataset")
    parser.add_argument("--cleanup", action="store_true", help="Clean up test data")

    args = parser.parse_args()

    generator = FWMISTestDataGenerator()
    generator.setup_test_directory()

    if args.cleanup:
        generator.cleanup_test_data()
        return

    if args.bas_files:
        for i in range(args.bas_files):
            generator.generate_bas_file()

    if args.cases:
        generator.generate_test_cases(args.cases)

    if args.evidence:
        for i in range(args.evidence):
            generator.generate_dummy_pdf()

    if args.performance:
        generator.generate_performance_dataset(args.performance)

    if not any([args.bas_files, args.cases, args.evidence, args.performance, args.cleanup]):
        print("FWMIS Test Data Generator")
        print("Usage examples:")
        print("  python test_data_generator.py --bas-files 5")
        print("  python test_data_generator.py --cases 100")
        print("  python test_data_generator.py --evidence 10")
        print("  python test_data_generator.py --performance medium")
        print("  python test_data_generator.py --cleanup")


if __name__ == "__main__":
    main()
