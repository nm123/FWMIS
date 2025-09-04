import sqlite3
import datetime
import os
import re
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem
from PyQt5.QtCore import Qt
from scripts.Utilities.config import BASE_DIR, DB_PATH
from scripts.Utilities.tree_utils import get_subtree_resp_ids
from scripts.Utilities.validation_utils import is_valid_email
from scripts.Utilities.audit_utils import save_audit_log

def add_responsibility(dialog, data):
    name = data["name"].strip()
    parent_id = data["parent_id"]
    is_posting_level = data["is_posting_level"]
    contacts = data["contacts"]
    inherited_contacts = data["inherited_contacts"]

    # Log input data
    print(f"add_responsibility input: name='{name}', parent_id={parent_id}, is_posting_level={is_posting_level}, contacts={contacts}, inherited_contacts={inherited_contacts}")

    # Validation
    if not name:
        QMessageBox.warning(dialog, "Invalid Input", "Name cannot be empty.")
        return
    if len(name) > 100:
        QMessageBox.warning(dialog, "Invalid Input", "Name cannot exceed 100 characters.")
        return
    if is_posting_level and not contacts:
        QMessageBox.warning(dialog, "Invalid Input", "Posting level responsibilities require at least one contact.")
        return
    for contact in contacts:
        # Require at least names or surname
        if not (contact.get("names") or contact.get("surname")):
            QMessageBox.warning(dialog, "Invalid Input", "Contact must have at least a name or surname.")
            return
        if contact.get("names") and len(contact["names"]) > 100:
            QMessageBox.warning(dialog, "Invalid Input", f"Contact names '{contact['names']}' cannot exceed 100 characters.")
            return
        if contact.get("surname") and len(contact["surname"]) > 100:
            QMessageBox.warning(dialog, "Invalid Input", f"Contact surname '{contact['surname']}' cannot exceed 100 characters.")
            return
        if contact.get("title") and len(contact["title"]) > 100:
            QMessageBox.warning(dialog, "Invalid Input", f"Contact title '{contact['title']}' cannot exceed 100 characters.")
            return
        if contact.get("initials") and len(contact["initials"]) > 10:
            QMessageBox.warning(dialog, "Invalid Input", f"Contact initials '{contact['initials']}' cannot exceed 10 characters.")
            return
        if contact.get("job_title") and len(contact["job_title"]) > 100:
            QMessageBox.warning(dialog, "Invalid Input", f"Contact job title '{contact['job_title']}' cannot exceed 100 characters.")
            return
        if contact.get("telephone") and not re.match(r"^[\+]?[(]?[0-9]{1,4}[)]?[-0-9\s]*$", contact["telephone"]):
            QMessageBox.warning(dialog, "Invalid Input", f"Invalid telephone format: {contact['telephone']}")
            return
        if contact.get("email") and not is_valid_email(contact["email"]):
            QMessageBox.warning(dialog, "Invalid Input", f"Invalid email format: {contact['email']}")
            return

    try:
        from scripts.Utilities.config import DB_PATH
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Set journal mode to WAL to prevent locks
        cursor.execute("PRAGMA journal_mode=WAL;")

        # Check for duplicate name (case-insensitive)
        cursor.execute("SELECT id FROM responsibilities WHERE UPPER(name) = UPPER(?)", (name,))
        if cursor.fetchone():
            QMessageBox.warning(dialog, "Invalid Input", f"A responsibility named '{name}' already exists.")
            conn.close()
            return

        # Get next responsibility ID
        cursor.execute("SELECT MAX(id) FROM responsibilities")
        max_id = cursor.fetchone()[0]
        new_id = (max_id or 0) + 1
        print(f"Generated new_id: {new_id}")

        # Get next sort_order for siblings
        cursor.execute("SELECT MAX(sort_order) FROM responsibilities WHERE parent_id IS ?",
                      (parent_id,) if parent_id else (None,))
        max_sort_order = cursor.fetchone()[0]
        new_sort_order = (max_sort_order or -1) + 1  # Start at 0 if no siblings
        print(f"Assigned sort_order: {new_sort_order}")

        # Clear any existing data for this ID (safety check)
        cursor.execute("DELETE FROM contacts WHERE responsibility_id = ?", (new_id,))
        cursor.execute("DELETE FROM responsibilities WHERE id = ?", (new_id,))

        # Insert responsibility with sort_order
        cursor.execute(
            "INSERT INTO responsibilities (id, name, parent_id, is_posting_level, sort_order) VALUES (?, ?, ?, ?, ?)",
            (new_id, name, parent_id, is_posting_level, new_sort_order)
        )
        print(f"Inserted responsibility: id={new_id}, name='{name}', sort_order={new_sort_order}")

        # Insert contacts (exactly as provided)
        inserted_contacts = []
        for contact in contacts:
            # Create combined name for backward compatibility
            combined_name = f"{contact.get('names', '')} {contact.get('surname', '')}".strip()
            cursor.execute(
                "INSERT INTO contacts (responsibility_id, name, title, initials, names, surname, job_title, telephone, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (new_id, combined_name, contact.get("title"), contact.get("initials"), contact.get("names"), contact.get("surname"), contact.get("job_title"), contact.get("telephone"), contact.get("email"))
            )
            inserted_contacts.append(contact)
        print(f"Inserted contacts for ID {new_id}: {inserted_contacts}")

        conn.commit()

        # Verify insertion
        cursor.execute("SELECT name, sort_order FROM responsibilities WHERE id = ?", (new_id,))
        inserted_name = cursor.fetchone()
        cursor.execute("SELECT title, initials, names, surname, job_title, telephone, email FROM contacts WHERE responsibility_id = ?", (new_id,))
        inserted_contacts = cursor.fetchall()
        print(f"After insertion, responsibility ID {new_id}: name='{inserted_name[0] if inserted_name else None}', sort_order={inserted_name[1] if inserted_name else None}, contacts={inserted_contacts}")

        # Log action
        try:
            save_audit_log("add_responsibility", {
                "responsibility_id": new_id,
                "name": name,
                "parent_id": parent_id,
                "is_posting_level": is_posting_level,
                "contacts": contacts,
                "inherited_contacts": inherited_contacts,
                "timestamp": datetime.datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Failed to log add_responsibility action: {e}")

        QMessageBox.information(dialog, "Success", "Responsibility added successfully.")
        dialog.refresh_tree()
        dialog.clear_form()

    except sqlite3.Error as e:
        print(f"Database error in add_responsibility: {e}")
        QMessageBox.critical(dialog, "Database Error", f"Failed to add responsibility: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def edit_responsibility(dialog):
    from responsibility_management_ui import AddResponsibilityDialog  # Import here to avoid circular import

    selected_item = dialog.tree.currentItem()
    if not selected_item:
        QMessageBox.warning(dialog, "No Selection", "Please select a responsibility to edit.")
        return

    resp_id = selected_item.data(0, Qt.UserRole)
    try:
        from scripts.Utilities.config import DB_PATH
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Set journal mode to WAL
        cursor.execute("PRAGMA journal_mode=WAL;")

        # Load current responsibility
        cursor.execute("SELECT name, parent_id, is_posting_level FROM responsibilities WHERE id = ?", (resp_id,))
        current = cursor.fetchone()
        if not current:
            QMessageBox.warning(dialog, "Error", "Selected responsibility not found.")
            conn.close()
            return
        current_name, current_parent_id, current_is_posting_level = current

        # Log current state
        print(f"Editing responsibility ID {resp_id}: current name='{current_name}', parent_id={current_parent_id}, is_posting_level={current_is_posting_level}")

        # Load parent name
        parent_name = "None"
        if current_parent_id:
            cursor.execute("SELECT name FROM responsibilities WHERE id = ?", (current_parent_id,))
            result = cursor.fetchone()
            if result:
                parent_name = result[0]

        # Load inherited and current contacts
        cursor.execute("SELECT title, initials, names, surname, job_title, telephone, email FROM contacts WHERE responsibility_id = ?", (current_parent_id,) if current_parent_id else (resp_id,))
        inherited_contacts = [{"title": row[0] or "", "initials": row[1] or "", "names": row[2] or "", "surname": row[3] or "", "job_title": row[4] or "", "telephone": row[5] or "", "email": row[6] or ""} for row in cursor.fetchall()]
        cursor.execute("SELECT title, initials, names, surname, job_title, telephone, email FROM contacts WHERE responsibility_id = ?", (resp_id,))
        current_contacts = [{"title": row[0] or "", "initials": row[1] or "", "names": row[2] or "", "surname": row[3] or "", "job_title": row[4] or "", "telephone": row[5] or "", "email": row[6] or ""} for row in cursor.fetchall()]
        print(f"Current contacts for ID {resp_id}: {current_contacts}")
        conn.close()

        # Open edit dialog - pass None as parent since MockDialog is not a QWidget
        edit_dialog = AddResponsibilityDialog(None, current_parent_id, parent_name, inherited_contacts)
        edit_dialog.setWindowTitle("Edit Responsibility")
        edit_dialog.name_edit.setText(current_name)
        edit_dialog.posting_yes.setChecked(current_is_posting_level)
        edit_dialog.posting_no.setChecked(not current_is_posting_level)
        edit_dialog.contacts_table.setRowCount(0)
        for contact in current_contacts:
            row = edit_dialog.contacts_table.rowCount()
            edit_dialog.contacts_table.insertRow(row)
            edit_dialog.contacts_table.setItem(row, 0, QTableWidgetItem(contact["title"]))
            edit_dialog.contacts_table.setItem(row, 1, QTableWidgetItem(contact["initials"]))
            edit_dialog.contacts_table.setItem(row, 2, QTableWidgetItem(contact["names"]))
            edit_dialog.contacts_table.setItem(row, 3, QTableWidgetItem(contact["surname"]))
            edit_dialog.contacts_table.setItem(row, 4, QTableWidgetItem(contact["job_title"]))
            edit_dialog.contacts_table.setItem(row, 5, QTableWidgetItem(contact["telephone"]))
            edit_dialog.contacts_table.setItem(row, 6, QTableWidgetItem(contact["email"]))

        # Add an empty row for new contact entry
        edit_dialog.contacts_table.insertRow(edit_dialog.contacts_table.rowCount())

        if edit_dialog.exec_():
            data = edit_dialog.get_data()
            name = data["name"].strip()
            is_posting_level = data["is_posting_level"]
            contacts = data["contacts"]

            # Log input data
            print(f"edit_responsibility input: name='{name}', is_posting_level={is_posting_level}, contacts={contacts}")

            # Validation
            if not name:
                QMessageBox.warning(edit_dialog, "Invalid Input", "Name cannot be empty.")
                return
            if len(name) > 100:
                QMessageBox.warning(edit_dialog, "Invalid Input", "Name cannot exceed 100 characters.")
                return
            if is_posting_level and not contacts:
                QMessageBox.warning(edit_dialog, "Invalid Input", "Posting level responsibilities require at least one contact.")
                return
            for contact in contacts:
                # Require at least names or surname
                if not (contact.get("names") or contact.get("surname")):
                    QMessageBox.warning(edit_dialog, "Invalid Input", "Contact must have at least a name or surname.")
                    return
                if contact.get("names") and len(contact["names"]) > 100:
                    QMessageBox.warning(edit_dialog, "Invalid Input", f"Contact names '{contact['names']}' cannot exceed 100 characters.")
                    return
                if contact.get("surname") and len(contact["surname"]) > 100:
                    QMessageBox.warning(edit_dialog, "Invalid Input", f"Contact surname '{contact['surname']}' cannot exceed 100 characters.")
                    return
                if contact.get("title") and len(contact["title"]) > 100:
                    QMessageBox.warning(edit_dialog, "Invalid Input", f"Contact title '{contact['title']}' cannot exceed 100 characters.")
                    return
                if contact.get("initials") and len(contact["initials"]) > 10:
                    QMessageBox.warning(edit_dialog, "Invalid Input", f"Contact initials '{contact['initials']}' cannot exceed 10 characters.")
                    return
                if contact.get("job_title") and len(contact["job_title"]) > 100:
                    QMessageBox.warning(edit_dialog, "Invalid Input", f"Contact job title '{contact['job_title']}' cannot exceed 100 characters.")
                    return
                if contact.get("telephone") and not re.match(r"^[\+]?[(]?[0-9]{1,4}[)]?[-0-9\s]*$", contact["telephone"]):
                    QMessageBox.warning(edit_dialog, "Invalid Input", f"Invalid telephone format: {contact['telephone']}")
                    return
                if contact.get("email") and not is_valid_email(contact["email"]):
                    QMessageBox.warning(edit_dialog, "Invalid Input", f"Invalid email format: {contact['email']}")
                    return

            from scripts.Utilities.config import DB_PATH
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Check for duplicate name
            cursor.execute("SELECT id FROM responsibilities WHERE UPPER(name) = UPPER(?) AND id != ?", (name, resp_id))
            if cursor.fetchone():
                QMessageBox.warning(edit_dialog, "Invalid Input", f"A responsibility named '{name}' already exists.")
                conn.close()
                return

            # Update responsibility
            cursor.execute(
                "UPDATE responsibilities SET name = ?, is_posting_level = ? WHERE id = ?",
                (name, is_posting_level, resp_id)
            )
            print(f"Updated responsibility ID {resp_id}: name='{name}'")

            # Delete existing contacts
            cursor.execute("DELETE FROM contacts WHERE responsibility_id = ?", (resp_id,))
            print(f"Deleted existing contacts for ID {resp_id}")

            # Insert updated contacts
            inserted_contacts = []
            for contact in contacts:
                # Create combined name for backward compatibility
                combined_name = f"{contact.get('names', '')} {contact.get('surname', '')}".strip()
                cursor.execute(
                    "INSERT INTO contacts (responsibility_id, name, title, initials, names, surname, job_title, telephone, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (resp_id, combined_name, contact.get("title"), contact.get("initials"), contact.get("names"), contact.get("surname"), contact.get("job_title"), contact.get("telephone"), contact.get("email"))
                )
                inserted_contacts.append(contact)
            print(f"Inserted contacts for ID {resp_id}: {inserted_contacts}")

            conn.commit()

            # Verify update
            cursor.execute("SELECT name FROM responsibilities WHERE id = ?", (resp_id,))
            updated_name = cursor.fetchone()
            cursor.execute("SELECT title, initials, names, surname, job_title, telephone, email FROM contacts WHERE responsibility_id = ?", (resp_id,))
            updated_contacts = cursor.fetchall()
            print(f"After update, responsibility ID {resp_id}: name='{updated_name[0] if updated_name else None}', contacts={updated_contacts}")

            # Log action
            try:
                save_audit_log("edit_responsibility", {
                    "responsibility_id": resp_id,
                    "name": name,
                    "parent_id": current_parent_id,
                    "is_posting_level": is_posting_level,
                    "contacts": contacts,
                    "timestamp": datetime.datetime.now().isoformat()
                })
            except Exception as e:
                print(f"Failed to log edit_responsibility action: {e}")

            QMessageBox.information(None, "Success", "Responsibility updated successfully.")
            dialog.refresh_tree()
            dialog.clear_form()

    except sqlite3.Error as e:
        print(f"Database error in edit_responsibility: {e}")
        QMessageBox.critical(None, "Database Error", f"Failed to edit responsibility: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def edit_responsibility_by_name(parent_dialog, responsibility_name):
    """Edit a responsibility directly by name, opening the edit dialog"""
    try:
        from scripts.Utilities.config import DB_PATH
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Find the responsibility by name
        cursor.execute("SELECT id, name, parent_id, is_posting_level FROM responsibilities WHERE name = ?", (responsibility_name,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            QMessageBox.warning(parent_dialog, "Not Found", f"Responsibility '{responsibility_name}' not found.")
            return

        resp_id, current_name, current_parent_id, current_is_posting_level = result

        # Create a mock dialog object with the necessary attributes
        class MockTree:
            def __init__(self, mock_item):
                self._current_item = mock_item

            def currentItem(self):
                return self._current_item

            def setCurrentItem(self, item):
                self._current_item = item

        class MockDialog:
            def __init__(self, parent, resp_id, mock_item):
                self.parent = parent
                self.resp_id = resp_id
                self.tree = MockTree(mock_item)

            def refresh_tree(self):
                # Refresh the import dialog's validation status
                if hasattr(self.parent, 'populate_transactions_table'):
                    self.parent.populate_transactions_table()

            def clear_form(self):
                pass

        # Set up the tree item data for the edit function
        from PyQt5.QtWidgets import QTreeWidgetItem
        from PyQt5.QtCore import Qt

        # Create a mock tree item
        mock_item = QTreeWidgetItem([current_name])
        mock_item.setData(0, Qt.UserRole, resp_id)

        # Create mock dialog with the mock item
        mock_dialog = MockDialog(parent_dialog, resp_id, mock_item)

        # Call the existing edit function
        edit_responsibility(mock_dialog)

    except Exception as e:
        QMessageBox.critical(parent_dialog, "Error", f"Failed to edit responsibility: {str(e)}")

def delete_responsibility(dialog):
    selected_item = dialog.tree.currentItem()
    if not selected_item:
        QMessageBox.warning(dialog, "No Selection", "Please select a responsibility to delete.")
        return

    resp_id = selected_item.data(0, Qt.UserRole)
    resp_name = selected_item.text(0)

    # Log deletion attempt
    print(f"Deleting responsibility ID {resp_id}: name='{resp_name}'")

    # Check for dependent cases
    try:
        from scripts.Utilities.config import DB_PATH
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Set journal mode to WAL
        cursor.execute("PRAGMA journal_mode=WAL;")

        subtree_ids = get_subtree_resp_ids(resp_id, dialog.responsibilities)
        cursor.execute("SELECT COUNT(*) FROM cases WHERE responsibility_id IN ({})".format(','.join('?' * len(subtree_ids))), subtree_ids)
        case_count = cursor.fetchone()[0]

        if case_count > 0:
            QMessageBox.warning(
                dialog, "Cannot Delete",
                f"Cannot delete '{resp_name}' because {case_count} case(s) are associated with it or its children."
            )
            conn.close()
            return

        # Confirm deletion
        reply = QMessageBox.question(
            dialog, "Confirm Delete",
            f"Are you sure you want to delete '{resp_name}' and its child responsibilities?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            conn.close()
            return

        # Delete responsibility and contacts
        cursor.execute("DELETE FROM contacts WHERE responsibility_id = ?", (resp_id,))
        cursor.execute("DELETE FROM responsibilities WHERE id = ?", (resp_id,))
        print(f"Deleted responsibility ID {resp_id} and its contacts")
        conn.commit()

        # Log action
        try:
            save_audit_log("delete_responsibility", {
                "responsibility_id": resp_id,
                "name": resp_name,
                "timestamp": datetime.datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Failed to log delete_responsibility action: {e}")

        QMessageBox.information(dialog, "Success", "Responsibility deleted successfully.")
        dialog.refresh_tree()
        dialog.clear_form()

    except sqlite3.Error as e:
        print(f"Database error in delete_responsibility: {e}")
        QMessageBox.critical(dialog, "Database Error", f"Failed to delete responsibility: {e}")
    finally:
        if 'conn' in locals():
            conn.close()