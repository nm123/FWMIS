"""
File operation utilities for case saving.
"""

import os
import shutil
import time

from PyQt5.QtWidgets import QMessageBox

from scripts.Utilities.financial_utils import create_year_folder


def handle_file_operations(dialog_instance, case: dict) -> dict:
    """Create folders and copy evidence files."""
    # Handle file operations - create case-specific folder structure
    # Optimized file upload: minimize file copying, use efficient database writes
    upload_start_time = time.time()

    # Temporarily disconnect ALL signals to prevent excessive emissions during upload
    try:
        dialog_instance.category_combo.currentTextChanged.disconnect(
            dialog_instance.schedule_update_conditional_fields
        )
        dialog_instance.assessment_status_combo.currentTextChanged.disconnect(
            dialog_instance.on_assessment_status_changed
        )
        dialog_instance.lc_status_combo.currentTextChanged.disconnect(
            dialog_instance.on_lc_status_changed
        )
        dialog_instance.list_combo.currentTextChanged.disconnect()  # Disconnect any list combo signals
    except TypeError:
        pass  # Signals may not be connected

    year_folder = create_year_folder(dialog_instance.fy)
    supporting_evidence_folder = os.path.join(year_folder, "Supporting Evidence")
    case_folder = os.path.join(
        supporting_evidence_folder, f"Case {dialog_instance.base_transaction_no}"
    )
    os.makedirs(case_folder, exist_ok=True)

    # Map fields to proper file names
    file_mappings = {
        "source_document": f"{dialog_instance.base_transaction_no} Source Document.pdf",
        "supporting_evidence_path": f"{dialog_instance.base_transaction_no} Supporting Evidence.pdf",
        "minutes": f"{dialog_instance.base_transaction_no} Loss Control Minutes.pdf",
        "evidence_path": f"{dialog_instance.base_transaction_no} Assessment Evidence.pdf",
        "recovery_evidence_path": f"{dialog_instance.base_transaction_no} Recovery Evidence.pdf",
    }

    # Batch file operations for efficiency
    files_to_copy = []
    for field, filename in file_mappings.items():
        if case[field] and case[field].strip():
            source_path = case[field].strip()
            dest_path = os.path.join(case_folder, filename)

            # Check if source and destination are the same
            if os.path.abspath(source_path) == os.path.abspath(dest_path):
                case[field] = dest_path
                continue

            if os.path.exists(source_path):
                # Check if it's a PDF file (only copy PDF files to avoid corruption)
                if not source_path.lower().endswith(".pdf"):
                    print(f"Warning: Skipping non-PDF file for {field}: {source_path}")
                    continue

                files_to_copy.append((field, source_path, dest_path))

    # Perform file copies efficiently
    for field, source_path, dest_path in files_to_copy:
        try:
            # Ensure destination directory exists
            dest_dir = os.path.dirname(dest_path)
            os.makedirs(dest_dir, exist_ok=True)

            # Check if destination file already exists and is read-only
            if os.path.exists(dest_path):
                try:
                    # Test if we can write to the file
                    with open(dest_path, "ab") as test_file:
                        pass
                except PermissionError:
                    QMessageBox.critical(
                        dialog_instance,
                        "File Permission Error",
                        f"Cannot overwrite existing {field} file.\n\n"
                        f"File: {dest_path}\n\n"
                        "The file may be read-only or in use by another program.",
                    )
                    # Reconnect signals before returning
                    dialog_instance.category_combo.currentTextChanged.connect(
                        dialog_instance.schedule_update_conditional_fields
                    )
                    dialog_instance.assessment_status_combo.currentTextChanged.connect(
                        dialog_instance.on_assessment_status_changed
                    )
                    return case

            # Try to copy the file (safer than move)
            shutil.copy2(source_path, dest_path)
            case[field] = dest_path

        except PermissionError:
            QMessageBox.critical(
                dialog_instance,
                "File Copy Permission Error",
                f"Cannot copy {field} file due to permission restrictions.\n\n"
                f"Source: {source_path}\n"
                f"Destination: {dest_path}\n\n"
                "Please check file permissions and ensure the source file is not in use.",
            )
            # Reconnect signals before returning
            dialog_instance.category_combo.currentTextChanged.connect(
                dialog_instance.schedule_update_conditional_fields
            )
            dialog_instance.assessment_status_combo.currentTextChanged.connect(
                dialog_instance.on_assessment_status_changed
            )
            return case
        except OSError as os_error:
            QMessageBox.critical(
                dialog_instance,
                "File System Error",
                f"Failed to copy {field} file due to file system error.\n\n"
                f"Source: {source_path}\n"
                f"Destination: {dest_path}\n\n"
                f"Error: {str(os_error)}",
            )
            # Reconnect signals before returning
            dialog_instance.category_combo.currentTextChanged.connect(
                dialog_instance.schedule_update_conditional_fields
            )
            dialog_instance.assessment_status_combo.currentTextChanged.connect(
                dialog_instance.on_assessment_status_changed
            )
            return case
        except Exception as copy_error:
            QMessageBox.critical(
                dialog_instance,
                "File Copy Error",
                f"Unexpected error while copying {field} file.\n\n"
                f"Source: {source_path}\n"
                f"Destination: {dest_path}\n\n"
                f"Error: {str(copy_error)}",
            )
            # Reconnect signals before returning
            dialog_instance.category_combo.currentTextChanged.connect(
                dialog_instance.schedule_update_conditional_fields
            )
            dialog_instance.assessment_status_combo.currentTextChanged.connect(
                dialog_instance.on_assessment_status_changed
            )
            return case

    # Reconnect signals after upload
    dialog_instance.category_combo.currentTextChanged.connect(
        dialog_instance.schedule_update_conditional_fields
    )
    dialog_instance.assessment_status_combo.currentTextChanged.connect(
        dialog_instance.on_assessment_status_changed
    )
    dialog_instance.lc_status_combo.currentTextChanged.connect(
        dialog_instance.on_lc_status_changed
    )

    upload_time = time.time() - upload_start_time
    print(
        f"LOG: Uploaded evidence for case {dialog_instance.base_transaction_no} in {upload_time:.2f}s"
    )

    return case
