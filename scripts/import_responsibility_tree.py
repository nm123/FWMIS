import sqlite3
import re
import sys
import os

# Add the scripts directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Utilities.config import DB_PATH

def parse_responsibility_line(line):
    """Parse a single line from the responsibility tree text"""
    line = line.strip()
    if not line or line.startswith('#'):
        return None

    parts = line.split('|')
    if len(parts) < 13:
        return None

    try:
        level = int(parts[0].strip())
        resp_id = int(parts[1].strip())
        name = parts[2].strip()
        posting_flag = parts[12].strip() == 'Y'

        return {
            'level': level,
            'id': resp_id,
            'name': name,
            'is_posting_level': posting_flag
        }
    except (ValueError, IndexError):
        return None

def build_responsibility_tree(text_lines):
    """Build a tree structure from the text lines"""
    responsibilities = []
    level_stack = []

    for line in text_lines:
        if not line.strip():
            continue

        resp = parse_responsibility_line(line)
        if not resp:
            continue

        # Find parent by going up the level stack
        parent_id = None
        for i in range(len(level_stack) - 1, -1, -1):
            if level_stack[i]['level'] < resp['level']:
                parent_id = level_stack[i]['id']
                break

        resp['parent_id'] = parent_id
        responsibilities.append(resp)

        # Update level stack
        # Remove items from stack that are at the same or higher level
        while level_stack and level_stack[-1]['level'] >= resp['level']:
            level_stack.pop()

        level_stack.append(resp)

    return responsibilities

def insert_responsibilities(responsibilities):
    """Insert responsibilities into the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Set journal mode to WAL
    cursor.execute("PRAGMA journal_mode=WAL;")

    # Get next sort_order for each level
    sort_orders = {}

    for resp in responsibilities:
        level = resp['level']
        if level not in sort_orders:
            sort_orders[level] = 0

        # Insert responsibility
        cursor.execute("""
            INSERT INTO responsibilities (id, name, parent_id, is_posting_level, sort_order)
            VALUES (?, ?, ?, ?, ?)
        """, (
            resp['id'],
            resp['name'],
            resp['parent_id'],
            resp['is_posting_level'],
            sort_orders[level]
        ))

        sort_orders[level] += 1
        print(f"Inserted: {resp['name']} (ID: {resp['id']}, Parent: {resp['parent_id']}, Posting: {resp['is_posting_level']})")

    conn.commit()
    conn.close()
    print(f"Successfully inserted {len(responsibilities)} responsibilities")

def main():
    # Read the responsibility tree text from file
    try:
        with open('responsibility_tree.txt', 'r', encoding='utf-8') as f:
            responsibility_tree_text = f.read()
    except FileNotFoundError:
        print("Error: responsibility_tree.txt file not found.")
        print("Please create a file named 'responsibility_tree.txt' in the same directory as this script")
        print("and paste your responsibility tree text into it.")
        return

    text_lines = responsibility_tree_text.strip().split('\n')
    responsibilities = build_responsibility_tree(text_lines)

    if not responsibilities:
        print("No valid responsibilities found in the text file.")
        return

    print(f"Parsed {len(responsibilities)} responsibilities from text file.")

    # Confirm before inserting
    response = input(f"Do you want to insert {len(responsibilities)} responsibilities into the database? (y/N): ")
    if response.lower() != 'y':
        print("Operation cancelled.")
        return

    insert_responsibilities(responsibilities)

if __name__ == "__main__":
    main()