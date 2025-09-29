"""
Menu Setup Module

Contains the menu creation and setup logic for the main FWMIS application window.
This helps reduce the size of the main application file and improves maintainability.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .app_main import FWManagementApp


def setup_menu(app: "FWManagementApp") -> None:
    """
    Set up the main menu bar for the FWMIS application.

    Args:
        app: The main FWManagementApp instance
    """
    menubar = app.menuBar()

    # File menu
    file_menu = menubar.addMenu("File")

    # Management actions
    responsibilities_action = app.create_menu_action(
        "Manage Responsibilities", app.manage_responsibilities
    )
    file_menu.addAction(responsibilities_action)

    email_templates_action = app.create_menu_action(
        "Manage Email Templates", app.manage_email_templates
    )
    file_menu.addAction(email_templates_action)

    file_menu.addSeparator()  # Separator before Exit

    exit_action = app.create_menu_action("Exit", app.close)
    file_menu.addAction(exit_action)

    # Cases menu
    cases_menu = menubar.addMenu("Cases")
    add_case_action = app.create_menu_action("Add New Case", app.add_new_case)
    cases_menu.addAction(add_case_action)

    import_cases_action = app.create_menu_action(
        "Import Undisclosed Cases", app.import_undisclosed_cases
    )
    cases_menu.addAction(import_cases_action)

    cases_menu.addSeparator()  # Add separator

    view_cases_action = app.create_menu_action("View Cases", app.view_cases)
    cases_menu.addAction(view_cases_action)

    edit_cases_action = app.create_menu_action("Edit Cases", app.manage_cases)
    cases_menu.addAction(edit_cases_action)

    cases_menu.addSeparator()  # Add separator

    # Write-off management
    write_off_annexure_action = app.create_menu_action(
        "Write-Off Annexure Management", app.open_write_off_annexures
    )
    cases_menu.addAction(write_off_annexure_action)

    write_off_log_action = app.create_menu_action(
        "Write-Off Annexure Log", app.open_write_off_management
    )
    cases_menu.addAction(write_off_log_action)

    finalization_dashboard_action = app.create_menu_action(
        "Finalization Dashboard", app.open_finalization_dashboard
    )
    cases_menu.addAction(finalization_dashboard_action)

    # To-Do List as standalone main menu
    todo_menu = menubar.addMenu("To-Do List")
    todo_action = app.create_menu_action("View To-Do List", app.todo_list)
    todo_menu.addAction(todo_action)

    # View menu with sub-menu items
    view_menu = menubar.addMenu("View")
    checklist_action = app.create_menu_action("Checklist", app.view_checklist)
    view_menu.addAction(checklist_action)

    lead_schedule_action = app.create_menu_action(
        "Lead Schedule", app.view_lead_schedule
    )
    view_menu.addAction(lead_schedule_action)

    deleted_items_action = app.create_menu_action(
        "Deleted Items", app.view_deleted_items
    )
    view_menu.addAction(deleted_items_action)

    deleted_cases_action = app.create_menu_action(
        "Deleted Cases", app.view_deleted_cases
    )
    view_menu.addAction(deleted_cases_action)

    # Administrator menu with Manage submenu
    admin_menu = menubar.addMenu("Administrator")
    manage_submenu = admin_menu.addMenu("Manage")

    # Add management items to Administrator > Manage
    categories_action = app.create_menu_action("Categories", app.manage_categories)
    manage_submenu.addAction(categories_action)

    lists_action = app.create_menu_action("Lists", app.manage_lists)
    manage_submenu.addAction(lists_action)

    # Add Financial Years to Administrator > Manage
    fy_action = app.create_menu_action("Financial Years", app.manage_financial_years)
    manage_submenu.addAction(fy_action)

    # Add Write-Off Delegations to Administrator > Manage
    delegations_action = app.create_menu_action(
        "Write-Off Delegations", app.manage_write_off_delegations
    )
    manage_submenu.addAction(delegations_action)

    # Add Performance Optimization Management
    optimization_action = app.create_menu_action(
        "Performance Optimization", app.open_optimization_management
    )
    optimization_action.setToolTip(
        "Configure performance optimizations for large datasets"
    )
    admin_menu.addAction(optimization_action)

    # Add separator before system management
    admin_menu.addSeparator()

    # Database Archiving Management
    archiving_action = app.create_menu_action(
        "🗄️ Database Archiving", app.open_database_archiving
    )
    archiving_action.setToolTip(
        "Manage database archiving for performance optimization"
    )
    admin_menu.addAction(archiving_action)

    # Automated Testing Management
    testing_action = app.create_menu_action(
        "🧪 Automated Testing", app.open_automated_testing
    )
    testing_action.setToolTip("Run automated tests and manage CI/CD integration")
    admin_menu.addAction(testing_action)

    # Test Verification Management
    verification_action = app.create_menu_action(
        "🔍 Test Verification", app.run_daily_test_verification
    )
    verification_action.setToolTip(
        "Run daily test verification to check coverage and integration"
    )
    admin_menu.addAction(verification_action)

    # Add separator before dangerous operations
    admin_menu.addSeparator()

    # Wipe Cases action (dangerous operation)
    wipe_cases_action = app.create_menu_action("Wipe Cases (Dangerous)", app.wipe_cases)
    wipe_cases_action.setToolTip(
        "Permanently delete all cases for a selected financial year"
    )
    admin_menu.addAction(wipe_cases_action)

    # Reports menu
    reports_menu = menubar.addMenu("Reports")
    generate_report_action = app.create_menu_action(
        "Generate Reports", app.generate_reports
    )
    reports_menu.addAction(generate_report_action)
