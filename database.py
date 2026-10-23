
import sqlite3
import time
from pathlib import Path

import sqlglot
from sqlglot import exp


DB_PATH = Path(__file__).with_name("querypilot.db")

MAX_ROWS = 200
QUERY_TIMEOUT_SECONDS = 2.0
PROGRESS_HANDLER_INTERVAL = 1000

ALLOWED_TABLES = {
    "customers",
    "products",
    "orders",
    "order_items",
}


def get_connection():
    """Open the database in read-only mode."""

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}. "
            "Run setup_database.py first."
        )

    connection = sqlite3.connect(
        f"{DB_PATH.as_uri()}?mode=ro",
        uri=True,
        timeout=5,
    )

    connection.execute("PRAGMA query_only = ON")
    connection.execute("PRAGMA busy_timeout = 5000")

    return connection


def get_schema():
    """Return the application's database schema."""

    connection = get_connection()

    try:
        tables = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()

        schema_parts = []

        for (table_name,) in tables:
            quoted_name = (
                '"' + table_name.replace('"', '""') + '"'
            )

            columns = connection.execute(
                f"PRAGMA table_info({quoted_name})"
            ).fetchall()

            foreign_keys = connection.execute(
                f"PRAGMA foreign_key_list({quoted_name})"
            ).fetchall()

            schema_parts.append(f"TABLE: {table_name}")
            schema_parts.append("COLUMNS:")

            for column in columns:
                (
                    _,
                    name,
                    data_type,
                    not_null,
                    default,
                    primary_key,
                ) = column

                schema_parts.append(
                    f"  {name} ({data_type or 'UNDECLARED TYPE'})"
                    f"{' PRIMARY KEY' if primary_key else ''}"
                    f"{' NOT NULL' if not_null else ''}"
                )

            if foreign_keys:
                schema_parts.append("FOREIGN KEYS:")

                for fk in foreign_keys:
                    (
                        _,
                        _,
                        referenced_table,
                        from_column,
                        to_column,
                        *_,
                    ) = fk

                    schema_parts.append(
                        f"  {from_column} -> "
                        f"{referenced_table}.{to_column}"
                    )

            schema_parts.append("")

        return "\n".join(schema_parts)

    finally:
        connection.close()


def validate_sql(query):
    """Validate one read-only SELECT using approved database tables."""

    if not query or not query.strip():
        raise ValueError("The generated SQL is empty.")

    try:
        statements = sqlglot.parse(query, read="sqlite")
    except sqlglot.errors.ParseError as error:
        raise ValueError(
            f"Invalid SQL syntax: {error}"
        ) from error

    if len(statements) != 1 or statements[0] is None:
        raise ValueError(
            "Exactly one SQL statement is allowed."
        )

    tree = statements[0]

    if not isinstance(tree, exp.Select):
        raise ValueError("Only SELECT queries are allowed.")

    if tree.args.get("into") is not None:
        raise ValueError("SELECT INTO is not allowed.")

    # Block unsupported SQL constructs.
    blocked_types = tuple(
        getattr(exp, name)
        for name in (
            "Command",
            "Copy",
            "Attach",
            "Detach",
            "Pragma",
            "Transaction",
            "Lock",
        )
        if hasattr(exp, name)
    )

    for node in tree.walk():
        if isinstance(node, blocked_types):
            raise ValueError(
                f"Unsupported SQL construct: "
                f"{type(node).__name__}"
            )

    # Collect CTE names so they are not mistaken for database tables.
    cte_names = {
        cte.alias_or_name.lower()
        for cte in tree.find_all(exp.CTE)
    }

    # Allow only approved tables and references to declared CTEs.
    for table in tree.find_all(exp.Table):
        table_name = table.name.lower()

        if table.db or table.catalog:
            raise ValueError(
                "Database-qualified table names are not allowed."
            )

        if table_name in cte_names:
            continue

        if table_name not in ALLOWED_TABLES:
            raise ValueError(
                f"Table '{table.name}' is not allowed. "
                f"Approved tables: "
                f"{', '.join(sorted(ALLOWED_TABLES))}."
            )

    safe_query = tree.sql(dialect="sqlite")

    # Validate SQL against SQLite without executing its results.
    connection = get_connection()

    try:
        connection.execute(
            "EXPLAIN QUERY PLAN " + safe_query
        )
    except sqlite3.Error as error:
        raise ValueError(
            f"Invalid SQLite query: {error}"
        ) from error
    finally:
        connection.close()

    return safe_query


def execute_readonly(query):
    """Execute a validated query with time and row limits."""

    safe_query = validate_sql(query)
    connection = get_connection()

    deadline = time.monotonic() + QUERY_TIMEOUT_SECONDS
    timed_out = False

    def interrupt_if_timed_out():
        nonlocal timed_out

        if time.monotonic() >= deadline:
            timed_out = True
            return 1

        return 0

    connection.set_progress_handler(
        interrupt_if_timed_out,
        PROGRESS_HANDLER_INTERVAL,
    )

    try:
        cursor = connection.execute(safe_query)

        if cursor.description is None:
            raise ValueError(
                "The query did not return a result set."
            )

        columns = [
            item[0] for item in cursor.description
        ]

        rows = cursor.fetchmany(MAX_ROWS + 1)

        truncated = len(rows) > MAX_ROWS
        rows = rows[:MAX_ROWS]

        return {
            "columns": columns,
            "rows": rows,
            "truncated": truncated,
        }

    except sqlite3.OperationalError as error:
        if timed_out:
            raise TimeoutError(
                "Query exceeded the execution time limit "
                f"of {QUERY_TIMEOUT_SECONDS} seconds."
            ) from error

        raise

    finally:
        connection.set_progress_handler(None, 0)
        connection.close()
