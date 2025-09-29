"""
Safe SQL Builder Utility

This module provides safe SQL query building utilities to prevent SQL injection
and ensure consistent query construction across the application.
"""

from typing import Any, Dict, List, Optional, Tuple


class SQLBuilder:
    """Safe SQL query builder with parameterization."""

    @staticmethod
    def build_update_query(
        table: str,
        updates: Dict[str, Any],
        where_clause: str,
        where_params: Optional[List[Any]] = None,
    ) -> Tuple[str, List[Any]]:
        """
        Build a safe UPDATE query.

        Args:
            table: Table name
            updates: Dict of column -> value mappings
            where_clause: WHERE clause with placeholders
            where_params: Parameters for WHERE clause

        Returns:
            Tuple of (SQL query string, parameters list)
        """
        if not updates:
            raise ValueError("Updates dictionary cannot be empty")

        # Build SET clause
        set_clause = ", ".join(f"{column} = ?" for column in updates.keys())
        params = list(updates.values())

        # Build full query
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

        # Add WHERE parameters
        if where_params:
            params.extend(where_params)

        return query, params

    @staticmethod
    def build_insert_query(table: str, data: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """
        Build a safe INSERT query.

        Args:
            table: Table name
            data: Dict of column -> value mappings

        Returns:
            Tuple of (SQL query string, parameters list)
        """
        if not data:
            raise ValueError("Data dictionary cannot be empty")

        columns = ", ".join(data.keys())
        placeholders = ", ".join("?" * len(data))
        params = list(data.values())

        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        return query, params

    @staticmethod
    def build_select_query(
        table: str,
        columns: Optional[List[str]] = None,
        where_conditions: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Tuple[str, List[Any]]:
        """
        Build a safe SELECT query.

        Args:
            table: Table name
            columns: List of columns to select (default: *)
            where_conditions: Dict of column -> value conditions
            order_by: ORDER BY clause
            limit: LIMIT clause

        Returns:
            Tuple of (SQL query string, parameters list)
        """
        # Build SELECT clause
        if columns:
            select_clause = ", ".join(columns)
        else:
            select_clause = "*"

        # Build WHERE clause
        where_clause = ""
        params = []

        if where_conditions:
            conditions = []
            for column, value in where_conditions.items():
                if isinstance(value, list):
                    # IN clause
                    placeholders = ", ".join("?" * len(value))
                    conditions.append(f"{column} IN ({placeholders})")
                    params.extend(value)
                else:
                    # Simple equality
                    conditions.append(f"{column} = ?")
                    params.append(value)

            where_clause = f" WHERE {' AND '.join(conditions)}"

        # Build ORDER BY clause
        order_clause = ""
        if order_by:
            order_clause = f" ORDER BY {order_by}"

        # Build LIMIT clause
        limit_clause = ""
        if limit:
            limit_clause = f" LIMIT {limit}"

        query = f"SELECT {select_clause} FROM {table}{where_clause}{order_clause}{limit_clause}"
        return query, params

    @staticmethod
    def build_in_clause(values: List[Any]) -> Tuple[str, List[Any]]:
        """
        Build a safe IN clause.

        Args:
            values: List of values for IN clause

        Returns:
            Tuple of (IN clause string, parameters list)
        """
        if not values:
            return "IN (NULL)", []  # SQLite compatible

        placeholders = ", ".join("?" * len(values))
        return f"IN ({placeholders})", values


def safe_update(
    table: str, updates: Dict[str, Any], where_column: str, where_value: Any
) -> Tuple[str, List[Any]]:
    """
    Convenience function for simple UPDATE queries.

    Args:
        table: Table name
        updates: Dict of column -> value mappings
        where_column: WHERE column name
        where_value: WHERE column value

    Returns:
        Tuple of (SQL query string, parameters list)
    """
    return SQLBuilder.build_update_query(
        table, updates, f"{where_column} = ?", [where_value]
    )


def safe_insert(table: str, data: Dict[str, Any]) -> Tuple[str, List[Any]]:
    """
    Convenience function for INSERT queries.

    Args:
        table: Table name
        data: Dict of column -> value mappings

    Returns:
        Tuple of (SQL query string, parameters list)
    """
    return SQLBuilder.build_insert_query(table, data)


def safe_select(
    table: str,
    columns: Optional[List[str]] = None,
    where_conditions: Optional[Dict[str, Any]] = None,
) -> Tuple[str, List[Any]]:
    """
    Convenience function for SELECT queries.

    Args:
        table: Table name
        columns: List of columns to select
        where_conditions: Dict of column -> value conditions

    Returns:
        Tuple of (SQL query string, parameters list)
    """
    return SQLBuilder.build_select_query(table, columns, where_conditions)
