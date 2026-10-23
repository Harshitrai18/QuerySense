# QueryPilot

**QueryPilot** is a natural-language interface for querying a sample
SQLite database. Users ask questions in plain English; the application
uses Groq to generate SQL, validates the SQL before execution, and
presents results in tables and supported charts.

## Project objectives

-   Make database querying more accessible to users who do not know SQL.
-   Detect common ambiguous questions and ask the user to clarify their
    intended metric.
-   Use AI-assisted text-to-SQL generation with a validation layer
    before execution.
-   Present query results in a Streamlit interface.
-   Restrict database access to read-only queries.

## Current features

-   Natural-language question input.
-   SQL generation using the Groq API.
-   SQLite database querying.
-   SQL validation using SQLGlot and read-only execution safeguards.
-   Rule-based and AI-assisted clarification for supported ambiguous
    questions.
-   Tabular query results.
-   Automatic chart detection for supported result shapes.
-   In-session query history and generated-SQL inspection.
-   Friendly error messages for common failure cases.

## Technology stack

  Component                    Technology
  ---------------------------- ---------------
  User interface               Streamlit
  Language                     Python
  Language model API           Groq
  Database                     SQLite
  SQL parsing and validation   SQLGlot
  Data handling                pandas
  Environment configuration    python-dotenv

## Architecture overview

1.  The user submits a question through Streamlit.
2.  The clarification engine checks whether the question needs a more
    specific interpretation.
3.  If clarification is needed, the user selects an available
    interpretation.
4.  The text-to-SQL module asks Groq to generate SQL using the database
    schema as context.
5.  The database layer validates the SQL and applies read-only
    safeguards.
6.  The validated query runs against SQLite.
7.  QueryPilot displays the results as a table and, where supported, a
    chart. The session history retains the question, SQL, and result.

See `architecture.mmd` for a Mermaid architecture diagram.

## Database used for the project

The current sample database contains these tables:

-   `customers`
-   `products`
-   `orders`
-   `order_items`

The database is intended for demonstration and testing. Results are only
as accurate as the supplied schema and data.

## Requirements

-   Python 3.10 or a compatible Python version supported by the
    installed dependencies.
-   A Groq API key and a model name available to your Groq account.
-   The project source files and SQLite database.

## Setup on Windows

Open PowerShell or the VS Code terminal in the project directory.

### 1. Create and activate a virtual environment

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use the terminal configuration you
normally use for your existing virtual environment.

### 2. Install dependencies

If the project already has a `requirements.txt`, use:

``` powershell
pip install -r requirements.txt
```

Otherwise install the dependencies used by the application:

``` powershell
pip install streamlit pandas groq sqlglot python-dotenv
```

### 3. Configure environment variables

Create a `.env` file in the project root:

``` text
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=your_supported_groq_model_name
```

Use a model identifier supported by your Groq account and the current
project configuration. Do not commit `.env` to source control or share
your API key in screenshots.

### 4. Run the application

``` powershell
streamlit run app.py
```

Streamlit will print a local URL in the terminal, commonly
`http://localhost:8501`.

## Running tests

Run the project's existing tests from the activated virtual environment:

``` powershell
python test_clarification_edge_cases.py
python test_security.py
python test_charts.py
```

These tests cover clarification edge cases, SQL security safeguards, and
chart detection. Record the actual test results when preparing a
submission; do not claim tests passed unless they have been run
successfully.

## Example questions

Try questions such as:

-   `Show all customers`
-   `Show total revenue by product`
-   `Which customers are doing well?`

The clarification example should prompt the user to choose a supported
interpretation before the query runs.

## Security and limitations

-   QueryPilot is a demonstration project, not a production database
    administration tool.
-   The application is designed to execute validated read-only queries;
    the validation and execution code should be reviewed before
    connecting any real or sensitive database.
-   The language model may produce incorrect or unsupported SQL.
    Validation can reduce risk but cannot guarantee that every generated
    answer is semantically correct.
-   The sample database has a limited schema and data, so not every
    question can be answered.
-   AI clarification depends on network access, valid environment
    configuration, and provider availability.
-   Query history is maintained in the current Streamlit session; it is
    not a persistent audit log.
-   Do not place secrets, personal information, or confidential data in
    prompts.

## Suggested demonstration flow

1.  Open QueryPilot and introduce the natural-language query interface.
2.  Submit `Show all customers` and show the results table.
3.  Submit `Which customers are doing well?` and select a metric in the
    clarification panel.
4.  Submit `Show total revenue by product` and show the results and any
    detected chart.
5.  Expand the generated SQL section to explain how a natural-language
    question maps to SQL.
6.  Briefly explain that SQL validation and read-only execution
    safeguards are applied before a query reaches SQLite.

## Project status

The current project scope focuses on natural-language SQL generation,
clarification, safe query execution, and result presentation. The
project is intentionally not expanded with additional features during
finalization.
