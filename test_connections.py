import os

import sqlglot
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from the local .env file
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key or api_key == "your_actual_groq_api_key_here":
    raise SystemExit(
        "GROQ_API_KEY is missing. Check your local .env file."
    )

# Test 1: Connect to Groq using your secret API key
try:
    client = Groq(api_key=api_key)
    models = client.models.list()
    print("PASS: Groq API connection successful.")
    print(f"Models available to your account: {len(models.data)}")
except Exception as error:
    print("FAIL: Groq API connection failed.")
    print(f"Error type: {type(error).__name__}")
    print("Check your key, internet connection, and API access.")
    raise SystemExit(1)

# Test 2: Parse a SQL query using SQLGlot
try:
    query = """
        SELECT name
        FROM customers
        WHERE active = 1
    """

    parsed_query = sqlglot.parse_one(query, read="sqlite")

    print("PASS: SQLGlot parsed the query successfully.")
    print(parsed_query.sql(dialect="sqlite"))

except Exception as error:
    print("FAIL: SQLGlot could not parse the query.")
    print(f"Error type: {type(error).__name__}")
    raise SystemExit(1)

print("\nAll connection tests passed!")