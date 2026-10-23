
from database import get_schema, validate_sql, execute_readonly
from text_to_sql import generate_sql


def main():
    print("=" * 50)
    print("QUERYPILOT PIPELINE TEST")
    print("=" * 50)

    # Test 1: Automatic schema discovery
    print("\n1. DISCOVERED DATABASE SCHEMA\n")
    print(get_schema())

    # Test 2: Generate SQL with Groq
    question = "Show me all customers from Delhi"

    print("\n2. USER QUESTION")
    print(question)

    sql = generate_sql(question)

    print("\n3. GENERATED SQL")
    print(sql)

    # Test 3: Validate the generated SQL
    safe_sql = validate_sql(sql)
    print("\n4. SQL VALIDATION")
    print("PASS: Query passed validation.")

    # Test 4: Execute against SQLite
    result = execute_readonly(safe_sql)

    print("\n5. QUERY RESULTS")
    print("Columns:", result["columns"])

    for row in result["rows"]:
        print(row)

    if result["truncated"]:
        print(f"Showing only the first 200 rows.")

    print("\nPipeline test completed successfully.")


if __name__ == "__main__":
    main()
