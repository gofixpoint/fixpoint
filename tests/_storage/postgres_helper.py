"""Utility functions for the database"""

from typing import Any
from psycopg import Connection
from psycopg.rows import TupleRow
from psycopg.sql import SQL, Identifier, Composed


def execute_sql(connection: Connection[TupleRow], sql: Composed) -> None:
    """Utility function to execute SQL commands."""
    with connection.cursor() as cursor:
        cursor.execute(sql)
        connection.commit()


def truncate_table(connection: Connection[TupleRow], table_name: str) -> None:
    """Truncate a table."""
    sql = SQL("TRUNCATE TABLE {table};").format(table=Identifier(table_name))
    execute_sql(connection, sql)
    print(f"Table {table_name} truncated successfully.")


def drop_table(connection: Connection[TupleRow], table_name: str) -> None:
    """Drop a table."""
    sql = SQL("DROP TABLE IF EXISTS {table};").format(table=Identifier(table_name))
    execute_sql(connection, sql)
    print(f"Table {table_name} dropped successfully.")


def drop_schema(connection: Connection[TupleRow], schema_name: str) -> None:
    """Drop a schema."""
    sql = SQL("DROP SCHEMA IF EXISTS {schema_name} CASCADE;").format(
        schema_name=Identifier(schema_name)
    )
    execute_sql(connection, sql)
    print(f"Schema {schema_name} dropped successfully.")
