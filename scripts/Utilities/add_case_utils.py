from PyQt5.QtWidgets import QMessageBox


def validate_add_data(dialog):
    """Validate the data entered in the add case dialog"""
    # Get form values
    bas_payment_no = dialog.bas_payment_no_edit.text().strip()
    bas_journal_no = dialog.bas_journal_no_edit.text().strip()
    persal_no = dialog.persal_no_edit.text().strip()
    amount_text = dialog.amount_edit.text().strip()

    # Get compulsory settings from selected category
    category_name = dialog.category_combo.currentText()
    category = next((c for c in dialog.categories if c["name"] == category_name), None)
    if category:
        bas_comp = category.get("bas_payment_compulsory", False)
        persal_comp = category.get("persal_compulsory", False)
    else:
        bas_comp = False
        persal_comp = False

    # Validate compulsory fields
    missing_fields = []
    if bas_comp:
        # Require either BAS Payment details or BAS Journal details
        has_payment_details = bas_payment_no.strip() != ""
        has_journal_details = bas_journal_no.strip() != ""
        if not (has_payment_details or has_journal_details):
            missing_fields.append("BAS Payment No or BAS Journal No")
    if persal_comp and not persal_no:
        missing_fields.append("Persal No")
    if not amount_text:
        missing_fields.append("Amount")

    if missing_fields:
        QMessageBox.warning(dialog, "Invalid Input", f"The following fields are required: {', '.join(missing_fields)}")
        return False

    # Validate amount
    try:
        amount = float(amount_text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        QMessageBox.warning(dialog, "Invalid Input", "Amount must be a positive number.")
        return False

    # Validate responsibility selection
    if not dialog.selected_responsibility_id:
        QMessageBox.warning(dialog, "Invalid Input", "Please select a responsibility.")
        return False

    # Validate supporting evidence if compulsory
    if dialog.supporting_evidence_compulsory and not dialog.file_path_edit.text().strip():
        QMessageBox.warning(dialog, "Assessment Evidence Required",
                          "Assessment Evidence is compulsory for Valid/Confirmed status cases.\n\n"
                          "Please select a file before saving.")
        return False

    return True


def get_case_data(dialog):
    """Extract case data from the dialog"""
    # Convert dates
    date_incurred_str = dialog.date_incurred_edit.date().toString("yyyy-MM-dd")
    date_identified_str = dialog.date_identified_edit.date().toString("yyyy-MM-dd")
    date_reported_str = dialog.date_reported_edit.date().toString("yyyy-MM-dd")
    bas_payment_date_str = dialog.bas_payment_date_edit.date().toString("yyyy-MM-dd")
    bas_journal_date_str = dialog.bas_journal_date_edit.date().toString("yyyy-MM-dd")
    assessment_date_str = dialog.assessment_date_edit.date().toString("yyyy-MM-dd")

    # Get combo box values
    category_text = dialog.category_combo.currentText()
    status_text = dialog.status_combo.currentText()
    list_text = dialog.list_combo.currentText()

    # Handle case suffixes based on status
    transaction_no_with_suffix = dialog.transaction_no
    if status_text == "Confirmed":
        # Add -LS suffix for Lead Schedule cases
        transaction_no_with_suffix = f"{dialog.transaction_no}-LS"
        list_text = "Lead Schedule"
    elif status_text == "Write-Off Recommended":
        # Add -WOR suffix for Write-Off Recommended cases
        transaction_no_with_suffix = f"{dialog.transaction_no}-WOR"
        list_text = "Write-Off Recommended"

    # Get compulsory settings
    category_name = dialog.category_combo.currentText()
    category = next((c for c in dialog.categories if c["name"] == category_name), None)
    if category:
        bas_comp = category.get("bas_payment_compulsory", False)
    else:
        bas_comp = False

    bas_payment_no = dialog.bas_payment_no_edit.text().strip()
    bas_journal_no = dialog.bas_journal_no_edit.text().strip()
    has_payment_details = bas_payment_no.strip() != ""
    has_journal_details = bas_journal_no.strip() != ""

    # Determine status
    final_status = status_text
    if bas_comp and has_journal_details and not has_payment_details:
        final_status = "Outstanding BAS Details"

    return {
        "transaction_no": transaction_no_with_suffix,
        "date_incurred": str(date_incurred_str),
        "date_identified": str(date_identified_str),
        "date_reported": str(date_reported_str),
        "description": dialog.description_edit.toPlainText().strip(),
        "bas_payment_no": bas_payment_no,
        "bas_payment_date": str(bas_payment_date_str),
        "bas_journal_no": bas_journal_no,
        "bas_journal_date": str(bas_journal_date_str),
        "persal_no": dialog.persal_no_edit.text().strip(),
        "category": category_text,
        "responsibility_id": dialog.selected_responsibility_id,
        "amount": float(dialog.amount_edit.text().strip()),
        "source_document": dialog.source_doc_edit.text().strip(),
        "minutes": dialog.minutes_edit.text().strip(),
        "evidence_path": dialog.evidence_edit.text().strip(),
        "supporting_evidence_path": dialog.supporting_evidence_edit.text().strip(),
        "attachments": "[]",
        "status": final_status,
        "list": list_text,
        "assessment_assessed_by": dialog.assessed_by_edit.text().strip(),
        "assessment_date": str(assessment_date_str),
        "assessment_result": "",
        "prevention_steps": dialog.prevention_steps_edit.toPlainText().strip(),
        "original_list": list_text
    }


def handle_file_operations(case, fy, transaction_no):
    """Handle file copying and moving for the case"""
    import os
    from scripts.Utilities.financial_utils import create_year_folder
    import shutil

    year_folder = create_year_folder(fy)
    supporting_evidence_folder = os.path.join(year_folder, "Supporting Evidence")
    case_folder = os.path.join(supporting_evidence_folder, f"Case {transaction_no}")
    os.makedirs(case_folder, exist_ok=True)

    # Map fields to proper file names
    file_mappings = {
        "source_document": f"{transaction_no} Source Document.pdf",
        "minutes": f"{transaction_no} Loss Control Minutes.pdf",
        "evidence_path": f"{transaction_no} Assessment Evidence.pdf",
        "supporting_evidence_path": f"{transaction_no} Supporting Evidence.pdf"
    }

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
                if not source_path.lower().endswith('.pdf'):
                    print(f"Warning: Skipping non-PDF file for {field}: {source_path}")
                    continue

                try:
                    # Ensure destination directory exists
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    # Try to copy the file first (safer than move)
                    shutil.copy2(source_path, dest_path)
                    case[field] = dest_path
                except Exception as e:
                    QMessageBox.warning(None, "File Save Error",
                                      f"Failed to save {field} file: {str(e)}")
                    return False
            else:
                QMessageBox.warning(None, "File Not Found",
                                  f"The selected {field} file could not be found: {source_path}")
                return False
    return True


def reset_form_fields(dialog):
    """Reset all form fields to default values"""
    from PyQt5.QtCore import QDate
    from scripts.Utilities.financial_utils import generate_transaction_no

    # Generate new transaction number
    dialog.transaction_no = generate_transaction_no(dialog.fy)
    dialog.trans_no_edit.setText(dialog.transaction_no)

    # Clear text fields
    dialog.description_edit.clear()
    dialog.bas_payment_no_edit.clear()
    dialog.bas_journal_no_edit.clear()
    dialog.persal_no_edit.clear()
    dialog.amount_edit.clear()
    dialog.evidence_edit.clear()
    dialog.supporting_evidence_edit.clear()
    dialog.source_doc_edit.clear()
    dialog.minutes_edit.clear()
    dialog.assessed_by_edit.clear()

    # Reset combo boxes to defaults
    dialog.status_combo.setCurrentText("Alleged")
    dialog.prevention_steps_edit.clear()

    # Always reset list combo to Checklist
    if "Checklist" in [l["name"] for l in dialog.lists if l.get("is_system", False) and l["name"] != "Deleted Cases"]:
        dialog.list_combo.setCurrentText("Checklist")

    # Reset dates to current date
    current_date = QDate.currentDate()
    dialog.date_incurred_edit.setDate(current_date)
    dialog.date_identified_edit.setDate(current_date)
    dialog.date_reported_edit.setDate(current_date)
    dialog.bas_payment_date_edit.setDate(current_date)
    dialog.bas_journal_date_edit.setDate(current_date)
    dialog.assessment_date_edit.setDate(current_date)

    # Clear responsibility selection
    dialog.responsibility_edit.clear()
    dialog.selected_responsibility_id = None

    # Clear attachments (keeping empty array for database)
    pass

    # Reset focus to first field
    dialog.responsibility_edit.setFocus()