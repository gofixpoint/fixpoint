"""
This module defines the protocol for a storage interface.
"""

from typing import Any, Dict, List, Protocol


class SupportsCRUD(Protocol):
    """
    Base class for a storage interface.
    """

    def connect(self) -> None:
        """
        Connect to the storage system.
        """

    def disconnect(self) -> None:
        """
        Disconnect from the storage system.
        """

    def create(self, resource_path: str, data: Dict[Any, Any]) -> None:
        """
        Write a record to the specified resource path.
        """

    def read(self, resource_path: str, identifier: Any) -> Dict[Any, Any]:
        """
        Read a record from the specified resource path.
        """

    def update(self, resource_path: str, identifier: Any, data: Dict[Any, Any]) -> None:
        """
        Update a record in the specified resource path.
        """

    def delete(self, resource_path: str, identifier: Any) -> None:
        """
        Delete a record from the specified resource path.
        """


class SupportsTransactionalDatabase(SupportsCRUD, Protocol):
    """
    Interface for databases supporting transactions.
    """

    def begin_transaction(self) -> None:
        """
        Begin a transaction.
        """

    def commit_transaction(self) -> None:
        """
        Commit a transaction.
        """

    def rollback_transaction(self) -> None:
        """
        Rollback a transaction.
        """


class SupportsRelationalDatabase(SupportsTransactionalDatabase, Protocol):
    """
    Interface for relational database storage.
    """

    def create_table(self, table_name: str, schema: Dict[str, Any]) -> None:
        """
        Create a table with the specified name and schema.
        """

    def drop_table(self, table_name: str) -> None:
        """
        Drop a table with the specified name.
        """

    def alter_table(self, table_name: str, changes: Dict[str, Any]) -> None:
        """
        Alter a table with the specified changes.
        """

    def create_index(
        self, table_name: str, index_name: str, columns: List[str], unique: bool = False
    ) -> None:
        """
        Create an index on the specified table.
        """

    def drop_index(self, index_name: str) -> None:
        """
        Drop an index with the specified name.
        """

    def add_constraint(
        self, table_name: str, constraint_name: str, constraint_sql: str
    ) -> None:
        """
        Add a constraint to the specified table.
        """

    def drop_constraint(self, table_name: str, constraint_name: str) -> None:
        """
        Drop a constraint from the specified table.
        """


class SupportsPostgreSQL(SupportsRelationalDatabase, Protocol):
    """
    Interface for PostgreSQL database storage.
    """

    def create_schema(self, schema_name: str) -> None:
        """
        Create a new schema in the PostgreSQL database.
        """

    def drop_schema(self, schema_name: str) -> None:
        """
        Drop an existing schema from the PostgreSQL database.
        """

    def execute_psycopg_command(self, command: str, params: Any = None) -> Any:
        """
        Execute a command using psycopg, a PostgreSQL database adapter for Python.
        """

    def enable_extension(self, extension_name: str) -> None:
        """
        Enable a PostgreSQL extension.
        """

    def disable_extension(self, extension_name: str) -> None:
        """
        Disable a PostgreSQL extension.
        """

    def vacuum(self, analyze: bool = False) -> None:
        """
        Run the VACUUM command to clean up the database. If 'analyze' is True, also run ANALYZE.
        """


class SupportsSupabase(SupportsPostgreSQL, Protocol):
    """
    Interface specifically for Supabase storage.
    """
