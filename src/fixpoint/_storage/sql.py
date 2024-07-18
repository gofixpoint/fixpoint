"""SQL utility code"""

__all__ = ["format_where_clause"]

from typing import Any, Dict


def format_where_clause(conditions: Dict[str, Any]) -> str:
    """Format a WHERE clause for an SQL query"""
    conditions_parts = []
    for key in conditions.keys():
        conditions_parts.append(f"{key} = :{key}")

    conditions_str = " AND ".join(conditions_parts)
    return f"WHERE {conditions_str}"
