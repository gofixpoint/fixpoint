"""Utility functions for the database"""

from typing import Any
from psycopg import Connection
from psycopg.rows import TupleRow


def execute_sql(connection: Connection[TupleRow], sql: str, params: Any = None) -> None:
    """Utility function to execute SQL commands."""
    with connection.cursor() as cursor:
        cursor.execute("PREPARE plan AS " + sql)
        cursor.execute("EXECUTE plan", params)
        connection.commit()


def truncate_table(connection: Connection[TupleRow], table_name: str) -> None:
    """Truncate a table."""
    sql = "TRUNCATE TABLE %s;"
    execute_sql(connection, sql, (table_name,))
    print(f"Table {table_name} truncated successfully.")


def drop_table(connection: Connection[TupleRow], table_name: str) -> None:
    """Drop a table."""
    sql = "DROP TABLE IF EXISTS %s;"
    execute_sql(connection, sql, (table_name,))
    print(f"Table {table_name} dropped successfully.")


def drop_schema(connection: Connection[TupleRow], schema_name: str) -> None:
    """Drop a schema."""
    sql = "DROP SCHEMA IF EXISTS %s CASCADE;"
    execute_sql(connection, sql, (schema_name,))
    print(f"Schema {schema_name} dropped successfully.")
