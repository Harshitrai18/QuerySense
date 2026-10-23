
from database import (
    ALLOWED_TABLES,
    MAX_ROWS,
    execute_readonly,
    validate_sql,
)


passed = 0
failed = 0


def check(name, test_function):
    """Run one test and report its result."""

    global passed, failed

    try:
        test_function()
        print(f"PASS: {name}")
        passed += 1
    except Exception as error:
        print(f"FAIL: {name} — {error}")
        failed += 1


def should_accept(query):
    """Verify that SQL validation accepts a query."""

    validate_sql(query)


def should_reject(query):
    """Verify that SQL validation rejects a query."""

    try:
        validate_sql(query)
    except ValueError:
        return

    raise AssertionError(
        "The query was accepted unexpectedly."
    )


def test_valid_select():
    should_accept(
        "SELECT name FROM customers"
    )


def test_valid_join():
    should_accept("""
        SELECT customers.name, orders.status
        FROM customers
        JOIN orders
          ON customers.id = orders.customer_id
    """)


def test_valid_aggregation():
    should_accept("""
        SELECT status, COUNT(*) AS total
        FROM orders
        GROUP BY status
    """)


def test_reject_write_operations():
    queries = [
        "DELETE FROM customers",
        "UPDATE customers SET city = 'Delhi'",
        "INSERT INTO customers (name) VALUES ('Test')",
        "DROP TABLE customers",
        "CREATE TABLE test_table (id INTEGER)",
        "ALTER TABLE customers ADD COLUMN test TEXT",
    ]

    for query in queries:
        should_reject(query)


def test_reject_multiple_statements():
    should_reject(
        "SELECT name FROM customers; "
        "SELECT * FROM products"
    )


def test_reject_malformed_sql():
    should_reject(
        "SELECT FROM customers"
    )


def test_reject_empty_sql():
    should_reject("")


def test_reject_whitespace_sql():
    should_reject("   ")


def test_reject_comment_only():
    should_reject("-- nothing to execute")


def test_reject_pragma():
    should_reject(
        "PRAGMA table_info(customers)"
    )


def test_reject_attach():
    should_reject(
        "ATTACH DATABASE 'other.db' AS other"
    )


def test_reject_internal_table():
    should_reject(
        "SELECT * FROM sqlite_master"
    )


def test_reject_unapproved_table():
    should_reject(
        "SELECT * FROM secret_data"
    )


def test_reject_qualified_table():
    should_reject(
        "SELECT * FROM other_db.customers"
    )


def test_allowed_tables():
    expected = {
        "customers",
        "products",
        "orders",
        "order_items",
    }

    assert ALLOWED_TABLES == expected


def test_query_execution():
    result = execute_readonly(
        "SELECT name FROM customers"
    )

    assert result["columns"] == ["name"]
    assert len(result["rows"]) > 0
    assert result["truncated"] is False


def test_join_execution():
    result = execute_readonly("""
        SELECT customers.name, orders.status
        FROM customers
        JOIN orders
          ON customers.id = orders.customer_id
    """)

    assert "name" in result["columns"]
    assert "status" in result["columns"]
    assert len(result["rows"]) > 0


def test_row_limit():
    # 6 customers × 5 products × 8 orders = 240 rows.
    # All three tables are approved by the validator.
    result = execute_readonly("""
        SELECT
            customers.name,
            products.name AS product_name,
            orders.id AS order_id
        FROM customers
        CROSS JOIN products
        CROSS JOIN orders
    """)

    assert len(result["rows"]) == MAX_ROWS
    assert result["truncated"] is True


def test_write_query_does_not_execute():
    try:
        execute_readonly(
            "DELETE FROM customers"
        )
    except ValueError:
        return

    raise AssertionError(
        "A write query was not rejected."
    )


def test_query_timeout():
    # This recursive query deliberately performs excessive work.
    query = """
        WITH RECURSIVE counter(x) AS (
            VALUES(0)
            UNION ALL
            SELECT x + 1
            FROM counter
            WHERE x < 100000000
        )
        SELECT sum(x) FROM counter
    """

    try:
        execute_readonly(query)
    except TimeoutError as error:
        assert "execution time limit" in str(error).lower()
        return

    raise AssertionError(
        "The expensive query was not interrupted."
    )


tests = [
    ("Valid SELECT", test_valid_select),
    ("Valid JOIN", test_valid_join),
    ("Valid aggregation", test_valid_aggregation),
    ("Reject write operations", test_reject_write_operations),
    ("Reject multiple statements", test_reject_multiple_statements),
    ("Reject malformed SQL", test_reject_malformed_sql),
    ("Reject empty SQL", test_reject_empty_sql),
    ("Reject whitespace SQL", test_reject_whitespace_sql),
    ("Reject comment-only SQL", test_reject_comment_only),
    ("Reject PRAGMA", test_reject_pragma),
    ("Reject ATTACH", test_reject_attach),
    ("Reject SQLite internal table", test_reject_internal_table),
    ("Reject unapproved table", test_reject_unapproved_table),
    ("Reject qualified table", test_reject_qualified_table),
    ("Approved table allowlist", test_allowed_tables),
    ("Execute normal query", test_query_execution),
    ("Execute JOIN", test_join_execution),
    ("Enforce row limit", test_row_limit),
    ("Enforce query timeout", test_query_timeout),
    ("Reject write during execution", test_write_query_does_not_execute),
]


print("\nQueryPilot Security Tests")
print("=" * 45)

for name, test_function in tests:
    check(name, test_function)

print("=" * 45)
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Total:  {passed + failed}")

if failed:
    raise SystemExit(1)

print("\nAll security tests passed!")
