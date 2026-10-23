
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("querypilot.db")

connection = sqlite3.connect(DB_PATH)
connection.execute("PRAGMA foreign_keys = ON")

# Check that all four tables exist.
tables = connection.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
      AND name NOT LIKE 'sqlite_%'
    ORDER BY name
""").fetchall()

print("Tables found:")
for (table_name,) in tables:
    print(f" - {table_name}")

# Check row counts.
for table in ["customers", "products", "orders", "order_items"]:
    count = connection.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]
    print(f"{table}: {count} rows")

# Test a join across three tables.
query = """
    SELECT c.name, o.id AS order_id, o.status
    FROM customers AS c
    JOIN orders AS o ON o.customer_id = c.id
    ORDER BY o.id
"""

results = connection.execute(query).fetchall()

print("\nFirst five customer orders:")
for row in results[:5]:
    print(row)

# Check foreign-key consistency.
violations = connection.execute(
    "PRAGMA foreign_key_check"
).fetchall()

print("\nForeign-key check:", "PASS" if not violations else violations)

connection.close()
