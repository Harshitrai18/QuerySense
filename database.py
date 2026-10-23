import re
import sqlite3
import time
from pathlib import Path

import pandas as pd
import sqlglot
from sqlglot import exp

DB_PATH = Path(__file__).with_name("querypilot.db")
UPLOAD_DIR = Path(__file__).with_name("uploaded_datasets")
MAX_ROWS = 200
QUERY_TIMEOUT_SECONDS = 2.0
PROGRESS_HANDLER_INTERVAL = 1000

# Default database allowlist is preserved for the bundled sample database.
ALLOWED_TABLES = {"customers", "products", "orders", "order_items"}


def _resolve_db_path(db_path=None):
    path = Path(db_path) if db_path else DB_PATH
    if not path.exists():
        if path == DB_PATH:
            raise FileNotFoundError(
                f"Database not found: {path}. Run setup_database.py first."
            )
        raise FileNotFoundError(f"Selected database not found: {path}")
    return path.resolve()


def get_connection(db_path=None):
    """Open the selected SQLite database in read-only mode."""
    path = _resolve_db_path(db_path)
    connection = sqlite3.connect(
        f"{path.as_uri()}?mode=ro", uri=True, timeout=5
    )
    connection.execute("PRAGMA query_only = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _list_user_tables(connection):
    return [
        row[0] for row in connection.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()
    ]


def get_schema(db_path=None):
    """Return the schema for the selected database."""
    connection = get_connection(db_path)
    try:
        schema_parts = []
        for table_name in _list_user_tables(connection):
            quoted_name = '"' + table_name.replace('"', '""') + '"'
            columns = connection.execute(
                f"PRAGMA table_info({quoted_name})"
            ).fetchall()
            schema_parts.append(f"TABLE: {table_name}")
            schema_parts.append("COLUMNS:")
            for column in columns:
                _, name, data_type, not_null, default, primary_key = column
                schema_parts.append(
                    f"  {name} ({data_type or 'UNDECLARED TYPE'})"
                    f"{' PRIMARY KEY' if primary_key else ''}"
                    f"{' NOT NULL' if not_null else ''}"
                )
            schema_parts.append("")
        return "\n".join(schema_parts)
    finally:
        connection.close()


def import_dataset(uploaded_file):
    """Import a CSV or Excel file into a separate SQLite database.

    Excel files use the first worksheet. The uploaded content is stored in a
    separate database file so the bundled sample database remains untouched.
    """
    filename = Path(uploaded_file.name).name
    suffix = Path(filename).suffix.lower()
    if suffix not in {".csv", ".xlsx"}:
        raise ValueError("Please upload a CSV (.csv) or Excel (.xlsx) file.")

    try:
        if suffix == ".csv":
            dataframe = pd.read_csv(uploaded_file)
        else:
            dataframe = pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception as error:
        raise ValueError(
            "The file could not be read. Check that it is a valid CSV or .xlsx file."
        ) from error

    if dataframe.empty:
        raise ValueError("The uploaded dataset has no data rows.")
    if len(dataframe.columns) == 0:
        raise ValueError("The uploaded dataset has no columns.")
    if len(dataframe) > 500_000:
        raise ValueError("This version supports datasets up to 500,000 rows.")

    # Normalize headers to safe, unique SQL identifiers.
    names = []
    used = set()
    for index, column in enumerate(dataframe.columns):
        name = re.sub(r"\W+", "_", str(column).strip(), flags=re.UNICODE).strip("_")
        if not name:
            name = f"column_{index + 1}"
        if name[0].isdigit():
            name = f"col_{name}"
        candidate = name
        counter = 2
        while candidate.lower() in used:
            candidate = f"{name}_{counter}"
            counter += 1
        used.add(candidate.lower())
        names.append(candidate)
    dataframe.columns = names

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    # A random filename avoids collisions between different sessions/uploads.
    import uuid
    db_path = (UPLOAD_DIR / f"dataset_{uuid.uuid4().hex}.db").resolve()
    table_name = "uploaded_data"
    connection = sqlite3.connect(db_path)
    try:
        dataframe.to_sql(table_name, connection, if_exists="fail", index=False)
    finally:
        connection.close()

    return {
        "db_path": str(db_path),
        "table_name": table_name,
        "row_count": int(len(dataframe)),
        "columns": names,
        "source_name": filename,
    }


def _allowed_tables_for_db(db_path=None, allowed_tables=None):
    if allowed_tables is not None:
        return {name.lower() for name in allowed_tables}
    # Keep the existing strict allowlist for the default bundled database.
    if db_path is None or Path(db_path).resolve() == DB_PATH.resolve():
        return {name.lower() for name in ALLOWED_TABLES}
    # Imported databases contain only the application-created table.
    connection = get_connection(db_path)
    try:
        return {name.lower() for name in _list_user_tables(connection)}
    finally:
        connection.close()


def validate_sql(query, db_path=None, allowed_tables=None):
    """Validate one read-only SELECT using tables in the selected database."""
    if not query or not query.strip():
        raise ValueError("The generated SQL is empty.")
    try:
        statements = sqlglot.parse(query, read="sqlite")
    except sqlglot.errors.ParseError as error:
        raise ValueError(f"Invalid SQL syntax: {error}") from error
    if len(statements) != 1 or statements[0] is None:
        raise ValueError("Exactly one SQL statement is allowed.")

    tree = statements[0]
    if not isinstance(tree, exp.Select):
        raise ValueError("Only SELECT queries are allowed.")
    if tree.args.get("into") is not None:
        raise ValueError("SELECT INTO is not allowed.")

    blocked_types = tuple(
        getattr(exp, name) for name in (
            "Command", "Copy", "Attach", "Detach", "Pragma",
            "Transaction", "Lock",
        ) if hasattr(exp, name)
    )
    for node in tree.walk():
        if isinstance(node, blocked_types):
            raise ValueError(f"Unsupported SQL construct: {type(node).__name__}")

    cte_names = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
    allowed = _allowed_tables_for_db(db_path, allowed_tables)
    for table in tree.find_all(exp.Table):
        table_name = table.name.lower()
        if table.db or table.catalog:
            raise ValueError("Database-qualified table names are not allowed.")
        if table_name in cte_names:
            continue
        if table_name not in allowed:
            raise ValueError(
                f"Table '{table.name}' is not allowed. "
                f"Approved tables: {', '.join(sorted(allowed))}."
            )

    safe_query = tree.sql(dialect="sqlite")
    connection = get_connection(db_path)
    try:
        connection.execute("EXPLAIN QUERY PLAN " + safe_query)
    except sqlite3.Error as error:
        raise ValueError(f"Invalid SQLite query: {error}") from error
    finally:
        connection.close()
    return safe_query


def execute_readonly(query, db_path=None, allowed_tables=None):
    """Execute a validated query with time and row limits."""
    safe_query = validate_sql(query, db_path, allowed_tables)
    connection = get_connection(db_path)
    deadline = time.monotonic() + QUERY_TIMEOUT_SECONDS
    timed_out = False

    def interrupt_if_timed_out():
        nonlocal timed_out
        if time.monotonic() >= deadline:
            timed_out = True
            return 1
        return 0

    connection.set_progress_handler(interrupt_if_timed_out, PROGRESS_HANDLER_INTERVAL)
    try:
        cursor = connection.execute(safe_query)
        if cursor.description is None:
            raise ValueError("The query did not return a result set.")
        columns = [item[0] for item in cursor.description]
        rows = cursor.fetchmany(MAX_ROWS + 1)
        truncated = len(rows) > MAX_ROWS
        rows = rows[:MAX_ROWS]
        return {"columns": columns, "rows": rows, "truncated": truncated}
    except sqlite3.OperationalError as error:
        if timed_out:
            raise TimeoutError(
                f"Query exceeded the execution time limit of {QUERY_TIMEOUT_SECONDS} seconds."
            ) from error
        raise
    finally:
        connection.set_progress_handler(None, 0)
        connection.close()
