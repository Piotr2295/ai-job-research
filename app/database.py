"""
Database utilities with proper error handling and connection management.

Provides safe database operations with automatic retry, timeout handling,
and proper exception translation.
"""

import sqlite3
import logging
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
from pathlib import Path

from app.exceptions import DatabaseError, DatabaseLockError, DuplicateRecordError

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations"""

    def __init__(self, db_path: Path, timeout: float = 10.0):
        self.db_path = db_path
        self.timeout = timeout

    @contextmanager
    def get_connection(self):
        """
        Get a database connection with proper error handling.

        Yields:
            sqlite3.Connection object

        Raises:
            DatabaseError: On connection failures
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=self.timeout)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            # Set busy timeout
            conn.execute(f"PRAGMA busy_timeout = {int(self.timeout * 1000)}")

            yield conn

        except sqlite3.OperationalError as e:
            error_msg = str(e).lower()
            if "locked" in error_msg or "busy" in error_msg:
                raise DatabaseLockError(
                    "Database is temporarily busy. Please try again."
                )
            raise DatabaseError(
                f"Database connection error: {str(e)}",
                details={"db_path": str(self.db_path)},
            )
        except Exception as e:
            logger.error(f"Unexpected database error: {str(e)}", exc_info=True)
            raise DatabaseError(f"Database error: {str(e)}")
        finally:
            if conn:
                conn.close()

    def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch_one: bool = False,
        fetch_all: bool = False,
    ) -> Optional[Any]:
        """
        Execute a SELECT query safely.

        Args:
            query: SQL query string
            params: Query parameters (use ? placeholders)
            fetch_one: If True, return single row
            fetch_all: If True, return all rows

        Returns:
            Query results or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params or ())

                if fetch_one:
                    row = cursor.fetchone()
                    return dict(row) if row else None
                elif fetch_all:
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
                else:
                    return None

            except sqlite3.Error as e:
                logger.error(
                    f"Query execution failed: {str(e)}",
                    extra={
                        "query": query,
                        "params": params,
                    },
                )
                raise DatabaseError(f"Query failed: {str(e)}")

    def execute_write(
        self,
        query: str,
        params: Optional[Tuple] = None,
        return_id: bool = False,
    ) -> Optional[int]:
        """
        Execute an INSERT/UPDATE/DELETE query safely.

        Args:
            query: SQL query string
            params: Query parameters (use ? placeholders)
            return_id: If True, return last inserted row ID

        Returns:
            Last row ID if return_id=True, else None

        Raises:
            DuplicateRecordError: On constraint violations
            DatabaseError: On other database errors
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params or ())
                conn.commit()

                if return_id:
                    return cursor.lastrowid
                else:
                    return cursor.rowcount

            except sqlite3.IntegrityError as e:
                conn.rollback()
                error_msg = str(e).lower()

                if "unique" in error_msg or "duplicate" in error_msg:
                    raise DuplicateRecordError(
                        "Record already exists with these unique values",
                        record_type="unknown",
                    )

                raise DatabaseError(
                    f"Database constraint violation: {str(e)}",
                    details={"constraint_error": True},
                )

            except sqlite3.OperationalError as e:
                conn.rollback()
                error_msg = str(e).lower()

                if "locked" in error_msg or "busy" in error_msg:
                    raise DatabaseLockError()

                raise DatabaseError(f"Database operation failed: {str(e)}")

            except Exception as e:
                conn.rollback()
                logger.error(f"Write operation failed: {str(e)}", exc_info=True)
                raise DatabaseError(f"Write operation failed: {str(e)}")

    def execute_many(
        self,
        query: str,
        params_list: List[Tuple],
    ) -> int:
        """
        Execute a query with multiple parameter sets.

        Args:
            query: SQL query string
            params_list: List of parameter tuples

        Returns:
            Number of rows affected
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount

            except sqlite3.IntegrityError:
                conn.rollback()
                raise DuplicateRecordError(
                    "One or more records already exist",
                    record_type="batch",
                )

            except sqlite3.OperationalError as e:
                conn.rollback()
                if "locked" in str(e).lower():
                    raise DatabaseLockError()
                raise DatabaseError(f"Batch operation failed: {str(e)}")

            except Exception as e:
                conn.rollback()
                logger.error(f"Batch operation failed: {str(e)}", exc_info=True)
                raise DatabaseError(f"Batch operation failed: {str(e)}")

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists"""
        try:
            result = self.execute_query(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
                """,
                (table_name,),
                fetch_one=True,
            )
            return result is not None
        except DatabaseError:
            return False

    def column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table"""
        try:
            result = self.execute_query(
                f"PRAGMA table_info({table_name})",
                fetch_all=True,
            )
            if result:
                return any(col["name"] == column_name for col in result)
            return False
        except DatabaseError:
            return False

    def add_column_if_not_exists(
        self,
        table_name: str,
        column_name: str,
        column_type: str,
        default_value: Optional[str] = None,
    ) -> bool:
        """
        Add a column to a table if it doesn't exist.

        Args:
            table_name: Name of the table
            column_name: Name of the column to add
            column_type: SQL type of the column
            default_value: Optional default value

        Returns:
            True if column was added, False if it already existed
        """
        if self.column_exists(table_name, column_name):
            logger.info(f"Column {column_name} already exists in {table_name}")
            return False

        query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        if default_value:
            query += f" DEFAULT {default_value}"

        self.execute_write(query)
        logger.info(f"Added column {column_name} to {table_name}")
        return True


def dict_to_row(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a dictionary to a database row format"""
    return {k: v for k, v in data.items() if v is not None}


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert a database row to a dictionary"""
    return dict(row) if row else {}
