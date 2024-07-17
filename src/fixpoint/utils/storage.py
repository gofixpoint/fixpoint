"""Storage layer utilities"""

__all__ = ["new_sqlite_conn"]

import sqlite3
import sys


def new_sqlite_conn(dbpath: str) -> sqlite3.Connection:
    """Create an SQLite connection with preferred settings"""

    if sys.version_info >= (3, 12):
        return sqlite3.connect(database=dbpath, autocommit=False)
    return sqlite3.connect(database=dbpath)
