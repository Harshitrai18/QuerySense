
import sqlite3
from pathlib import Path

# Store the database beside this Python file.
DB_PATH = Path(__file__).with_name("querypilot.db")


def setup_database():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # Enable foreign-key enforcement.
    cursor.execute("PRAGMA foreign_keys = ON")

    # Reset tables so the script can be safely rerun.
    cursor.executescript("""
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS customers;

        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            signup_date TEXT NOT NULL
        );

        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL CHECK (price >= 0)
        );

        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            status TEXT NOT NULL
                CHECK (status IN (
                    'pending', 'completed', 'cancelled'
                )),
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );

        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            unit_price REAL NOT NULL CHECK (unit_price >= 0),
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
    """)

    customers = [
        (1, "Aarav Sharma", "Delhi", "2025-01-10"),
        (2, "Priya Verma", "Mumbai", "2025-02-15"),
        (3, "Rohan Singh", "Delhi", "2025-03-20"),
        (4, "Ananya Gupta", "Lucknow", "2025-04-05"),
        (5, "Kabir Khan", "Mumbai", "2025-05-12"),
        (6, "Meera Patel", "Jaipur", "2025-06-18"),
    ]

    products = [
        (1, "Laptop", "Electronics", 55000.00),
        (2, "Headphones", "Electronics", 2500.00),
        (3, "Office Chair", "Furniture", 7500.00),
        (4, "Notebook", "Stationery", 100.00),
        (5, "Desk Lamp", "Home", 1200.00),
    ]

    orders = [
        (101, 1, "2026-01-05", "completed"),
        (102, 2, "2026-01-12", "completed"),
        (103, 1, "2026-02-03", "completed"),
        (104, 3, "2026-02-15", "pending"),
        (105, 4, "2026-03-02", "completed"),
        (106, 5, "2026-03-10", "cancelled"),
        (107, 2, "2026-04-08", "completed"),
        (108, 6, "2026-04-20", "completed"),
    ]

    order_items = [
        (1, 101, 1, 1, 55000.00),
        (2, 101, 2, 2, 2500.00),
        (3, 102, 3, 1, 7500.00),
        (4, 103, 2, 1, 2500.00),
        (5, 103, 4, 5, 100.00),
        (6, 104, 1, 1, 55000.00),
        (7, 105, 5, 2, 1200.00),
        (8, 105, 4, 10, 100.00),
        (9, 106, 1, 1, 55000.00),
        (10, 107, 3, 2, 7500.00),
        (11, 108, 2, 3, 2500.00),
        (12, 108, 5, 1, 1200.00),
    ]

    cursor.executemany(
        "INSERT INTO customers VALUES (?, ?, ?, ?)",
        customers,
    )

    cursor.executemany(
        "INSERT INTO products VALUES (?, ?, ?, ?)",
        products,
    )

    cursor.executemany(
        "INSERT INTO orders VALUES (?, ?, ?, ?)",
        orders,
    )

    cursor.executemany(
        "INSERT INTO order_items VALUES (?, ?, ?, ?, ?)",
        order_items,
    )

    connection.commit()
    connection.close()

    print(f"Database created successfully: {DB_PATH}")
    print("Customers: 6")
    print("Products: 5")
    print("Orders: 8")
    print("Order items: 12")


if __name__ == "__main__":
    setup_database()
