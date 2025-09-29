"""
Responsibility Tree Utilities

Common functions for building and managing responsibility tree widgets across the application.
"""

from collections import defaultdict

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QTreeWidgetItem


def build_responsibility_tree(tree_widget, responsibilities, show_posting_only=False, highlight_ids=None):
    """
    Build a responsibility tree in the given QTreeWidget.

    Args:
        tree_widget: QTreeWidget to populate
        responsibilities: List of responsibility dictionaries
        show_posting_only: If True, only show posting level responsibilities
        highlight_ids: Set of responsibility IDs to highlight in bold

    Returns:
        dict: Mapping of responsibility IDs to tree items
    """
    tree_widget.clear()

    # Filter responsibilities if needed
    if show_posting_only:
        filtered_resp = [r for r in responsibilities if r.get("is_posting_level", 0)]
    else:
        filtered_resp = responsibilities

    # Create parent map
    parent_map = defaultdict(list)
    for resp in filtered_resp:
        parent_map[resp["parent_id"]].append(resp)

    # Mapping of IDs to items for later reference
    resp_items = {}

    def add_tree_item(resp, parent_item=None):
        """Recursively add responsibility to tree"""
        item = QTreeWidgetItem([resp["name"]])
        item.setData(0, Qt.UserRole, resp["id"])
        item.setData(1, Qt.UserRole, resp.get("is_posting_level", 0))

        # Highlight if in highlight_ids
        if highlight_ids and resp["id"] in highlight_ids:
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)

        # Visual styling for non-posting items
        if resp.get("is_posting_level", 0) == 0:
            font = item.font(0)
            font.setItalic(True)
            item.setFont(0, font)

        # Add to tree
        if parent_item is None:
            tree_widget.addTopLevelItem(item)
        else:
            parent_item.addChild(item)

        # Store reference
        resp_items[resp["id"]] = item

        # Add children
        children = sorted(parent_map[resp["id"]], key=lambda x: (x.get("sort_order", 999), x["name"]))
        for child in children:
            add_tree_item(child, item)

    # Add top-level items (no parent)
    top_level = sorted(parent_map[None], key=lambda x: (x.get("sort_order", 999), x["name"]))
    for resp in top_level:
        add_tree_item(resp)

    return resp_items


def find_responsibility_item(tree_widget, resp_id):
    """
    Find a tree item by responsibility ID.

    Args:
        tree_widget: QTreeWidget to search
        resp_id: Responsibility ID to find

    Returns:
        QTreeWidgetItem or None
    """
    def search_items(parent_item):
        """Recursively search for item with given resp_id"""
        for i in range(parent_item.childCount() if parent_item else tree_widget.topLevelItemCount()):
            item = parent_item.child(i) if parent_item else tree_widget.topLevelItem(i)
            if item.data(0, Qt.UserRole) == resp_id:
                return item

            # Search children
            result = search_items(item)
            if result:
                return result

        return None

    return search_items(None)


def get_responsibility_path(tree_widget, resp_id):
    """
    Get the full path of a responsibility in the tree.

    Args:
        tree_widget: QTreeWidget containing the responsibility
        resp_id: Responsibility ID

    Returns:
        str: Full path (e.g., "Parent > Child > Grandchild")
    """
    item = find_responsibility_item(tree_widget, resp_id)
    if not item:
        return ""

    path = []
    current = item
    while current:
        path.insert(0, current.text(0))
        current = current.parent()

    return " > ".join(path)


def expand_to_responsibility(tree_widget, resp_id):
    """
    Expand the tree to show the given responsibility.

    Args:
        tree_widget: QTreeWidget to expand
        resp_id: Responsibility ID to expand to
    """
    item = find_responsibility_item(tree_widget, resp_id)
    if item:
        # Expand all parents
        current = item.parent()
        while current:
            current.setExpanded(True)
            current = current.parent()

        # Select the item
        tree_widget.setCurrentItem(item)
        tree_widget.scrollToItem(item)


def get_subtree_responsibility_ids(tree_widget, resp_id):
    """
    Get all responsibility IDs in the subtree rooted at the given responsibility.

    Args:
        tree_widget: QTreeWidget containing the responsibilities
        resp_id: Root responsibility ID

    Returns:
        set: Set of responsibility IDs in the subtree
    """
    item = find_responsibility_item(tree_widget, resp_id)
    if not item:
        return set()

    ids = {resp_id}

    def collect_children(parent_item):
        """Recursively collect all child responsibility IDs"""
        for i in range(parent_item.childCount()):
            child_item = parent_item.child(i)
            child_id = child_item.data(0, Qt.UserRole)
            ids.add(child_id)
            collect_children(child_item)

    collect_children(item)
    return ids

