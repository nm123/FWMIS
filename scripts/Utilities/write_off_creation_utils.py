"""
Utilities for creating write-off submissions.
"""

import csv
import os
import sqlite3
from datetime import datetime

from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import create_year_folder
from scripts.Utilities.utils import format_currency_amount


def get_evidence_status(evidence_paths):
    """Get a summary of evidence status"""
    if not evidence_paths:
        return "No evidence"

    try:
        import json

        evidence = json.loads(evidence_paths)
        evidence_types = []
        if evidence.get("assessment"):
            evidence_types.append("Assessment")
        if evidence.get("lc_minutes"):
            evidence_types.append("LC Minutes")
        if evidence.get("recovery"):
            evidence_types.append("Recovery")

        return ", ".join(evidence_types) if evidence_types else "No evidence"
    except:
        return "Invalid evidence data"


def generate_annexure(group_id, fy):
    """Generate CSV, PDF, and Excel annexures for the write-off submission"""
    try:
        # Create year folder if it doesn't exist
        year_folder = create_year_folder(fy)
        annexure_dir = os.path.join(year_folder, "Annexures")
        os.makedirs(annexure_dir, exist_ok=True)

        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Get case details
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT base_transaction_no, date_reported, category, amount,
                   assessment_status, lc_status, evidence_paths
            FROM cases
            WHERE write_off_group_id = ?
            ORDER BY base_transaction_no
        """,
            (group_id,),
        )

        cases = cursor.fetchall()
        conn.close()

        # Generate CSV
        csv_filename = f"Write_Off_Annexure_{group_id}_{timestamp}.csv"
        csv_filepath = os.path.join(annexure_dir, csv_filename)

        with open(csv_filepath, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                [
                    "Case Number",
                    "Date Reported",
                    "Category",
                    "Amount",
                    "Assessment Status",
                    "LC Status",
                    "Evidence Available",
                ]
            )

            for case in cases:
                (
                    base_transaction_no,
                    date_reported,
                    category,
                    amount,
                    assessment_status,
                    lc_status,
                    evidence_paths,
                ) = case
                evidence_status = get_evidence_status(evidence_paths)
                writer.writerow(
                    [
                        base_transaction_no,
                        date_reported,
                        category,
                        amount,
                        assessment_status,
                        lc_status,
                        evidence_status,
                    ]
                )

        print(f"CSV Annexure generated: {csv_filepath}")

        # Generate PDF
        pdf_filename = f"Write_Off_Annexure_{group_id}_{timestamp}.pdf"
        pdf_filepath = os.path.join(annexure_dir, pdf_filename)

        generate_pdf_annexure(pdf_filepath, group_id, cases, timestamp)

        print(f"PDF Annexure generated: {pdf_filepath}")

        # Generate Excel
        excel_filename = f"Write_Off_Annexure_{group_id}_{timestamp}.xlsx"
        excel_filepath = os.path.join(annexure_dir, excel_filename)

        generate_excel_annexure(excel_filepath, group_id, cases, timestamp)

        print(f"Excel Annexure generated: {excel_filepath}")

    except Exception as e:
        print(f"Error generating annexure: {e}")
        raise  # Re-raise to let caller handle


def generate_pdf_annexure(filepath, group_id, cases, timestamp):
    """Generate a PDF annexure for the write-off submission"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer,
                                        Table, TableStyle)

        doc = SimpleDocTemplate(filepath, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        title = Paragraph(f"<b>Write-Off Submission Annexure</b>", styles["Title"])
        elements.append(title)
        elements.append(Spacer(1, 12))

        # Submission details
        details = Paragraph(
            f"""
        <b>Submission ID:</b> {group_id}<br/>
        <b>Generated:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br/>
        <b>Total Cases:</b> {len(cases)}<br/>
        <b>Total Amount:</b> R {sum(case[3] for case in cases):,.2f}
        """,
            styles["Normal"],
        )
        elements.append(details)
        elements.append(Spacer(1, 20))

        # Table data
        data = [
            [
                "Case Number",
                "Date Reported",
                "Category",
                "Amount",
                "Assessment Status",
                "LC Status",
                "Evidence",
            ]
        ]

        for case in cases:
            (
                base_transaction_no,
                date_reported,
                category,
                amount,
                assessment_status,
                lc_status,
                evidence_paths,
            ) = case
            evidence_status = get_evidence_status(evidence_paths)
            formatted_amount = format_currency_amount(amount)
            data.append(
                [
                    base_transaction_no,
                    str(date_reported) if date_reported else "",
                    str(category) if category else "",
                    formatted_amount,
                    assessment_status or "",
                    lc_status or "",
                    evidence_status,
                ]
            )

        # Create table
        table = Table(data)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        elements.append(table)

        # Build PDF
        doc.build(elements)

    except ImportError:
        print("Warning: reportlab not installed. PDF annexure generation skipped.")
    except Exception as e:
        print(f"Error generating PDF annexure: {e}")


def generate_excel_annexure(filepath, group_id, cases, timestamp):
    """Generate an Excel annexure for the write-off submission"""
    try:
        import pandas as pd

        # Prepare data for DataFrame - structure case data into dictionary format for pandas
        data = []
        for case in cases:
            (
                base_transaction_no,
                date_reported,
                category,
                amount,
                assessment_status,
                lc_status,
                evidence_paths,
            ) = case
            evidence_status = get_evidence_status(evidence_paths)
            data.append(
                {
                    "Case Number": base_transaction_no,
                    "Date Reported": str(date_reported) if date_reported else "",
                    "Category": str(category) if category else "",
                    "Amount": amount,
                    "Assessment Status": assessment_status or "",
                    "LC Status": lc_status or "",
                    "Evidence Available": evidence_status,
                }
            )

        # Create DataFrame from prepared data
        df = pd.DataFrame(data)

        # Create Excel writer with openpyxl engine for advanced formatting
        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            # Write DataFrame to Excel with specified sheet name, excluding DataFrame index
            df.to_excel(writer, sheet_name="Write-Off Annexure", index=False)

            # Get workbook and worksheet references for post-processing formatting
            workbook = writer.book
            worksheet = writer.sheets["Write-Off Annexure"]

            # Format amount column as South African currency (R with commas and 2 decimals)
            from openpyxl.styles import NamedStyle

            currency_style = NamedStyle(name="currency", number_format="R #,##0.00")
            workbook.add_named_style(currency_style)

            # Apply currency formatting to Amount column (find column by name, apply to data rows)
            amount_col = None
            for col_num, column_title in enumerate(df.columns, 1):
                if column_title == "Amount":
                    amount_col = col_num
                    break

            if amount_col:
                for row_num in range(2, len(df) + 2):  # Start from row 2 (after header)
                    cell = worksheet.cell(row=row_num, column=amount_col)
                    cell.style = "currency"

            # Auto-adjust column widths based on content length
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(
                    max_length + 2, 50
                )  # Cap at 50 characters for readability
                worksheet.column_dimensions[column_letter].width = adjusted_width

            # Add summary information at the top of the worksheet
            worksheet.insert_rows(1)
            worksheet["A1"] = f"Write-Off Submission Annexure - Group: {group_id}"
            worksheet["A2"] = (
                f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            )
            worksheet["A3"] = f"Total Cases: {len(cases)}"
            worksheet["A4"] = f"Total Amount: R {sum(case[3] for case in cases):,.2f}"

            # Merge cells for title row spanning all columns
            from openpyxl.utils import range_boundaries

            worksheet.merge_cells("A1:G1")

    except ImportError:
        print(
            "Warning: pandas/openpyxl not installed. Excel annexure generation skipped."
        )
    except Exception as e:
        print(f"Error generating Excel annexure: {e}")
