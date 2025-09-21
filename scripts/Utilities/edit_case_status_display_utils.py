"""
Utilities for Edit Case Dialog status display.
Handles grid updates for List Status Information.
"""

def update_list_status_display(dialog_instance) -> None:
    """
    Update the List Status Information grid based on database statuses
    for consistent display across all views.

    Args:
        dialog_instance: The EditCaseDialog instance.
    """
    # Always use database statuses for consistency across views
    current_assessment_status: str = dialog_instance.assessment_status
    current_lc_status: str | None = dialog_instance.lc_status

    # Assume suffixes based on database statuses
    assumed_suffixes: list[str] = []
    if current_assessment_status == "Confirmed":
        assumed_suffixes.append("-LS")
    if current_lc_status == "Recovered":
        assumed_suffixes.append("-REC")
    if current_lc_status == "Write Off Recommended":
        assumed_suffixes.append("-WOR")
    assumed_suffix_list: list[str] = assumed_suffixes

    # Calculate statuses for each list using assumed suffixes
    headers: list[str] = ["Checklist", "Lead Schedule", "Recovered", "Write-Off Recommended", "Written Off", "Deleted Cases"]
    list_statuses: list[str] = []
    for header in headers:
        if header == "Checklist":
            list_statuses.append(current_assessment_status)
        elif header == "Lead Schedule":
            if "-LS" in assumed_suffix_list:
                list_statuses.append(current_lc_status or "Awaiting LC determination")
            else:
                list_statuses.append("N/A")
        elif header == "Recovered":
            list_statuses.append("Recovered" if "-REC" in assumed_suffix_list else "N/A")
        elif header == "Write-Off Recommended":
            list_statuses.append("Write Off Recommended" if "-WOR" in assumed_suffix_list else "N/A")
        elif header == "Written Off":
            list_statuses.append("Written Off" if "-WO" in assumed_suffix_list else "N/A")
        elif header == "Deleted Cases":
            list_statuses.append("Active")

    # Update the QLabel texts
    for i, status in enumerate(list_statuses):
        if i < len(dialog_instance.status_labels):
            dialog_instance.status_labels[i].setText(status)