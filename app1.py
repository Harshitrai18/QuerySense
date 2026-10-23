

import streamlit as st
import pandas as pd

from text_to_sql import generate_sql
from database import execute_readonly
from clarification import apply_clarification
from ai_clarification import detect_ai_clarification
from visualizations import detect_chart_type


st.set_page_config(
    page_title="QueryPilot",
    page_icon="🔎",
    layout="wide",
)

st.title("🔎 QueryPilot")
st.caption(
    "Ask questions about your database in plain English."
)


# --------------------------------------------------
# Session state
# --------------------------------------------------

if "history" not in st.session_state:
    st.session_state.history = []

if "pending_clarification" not in st.session_state:
    st.session_state.pending_clarification = None


# --------------------------------------------------
# Query execution
# --------------------------------------------------

def run_query(question, original_question=None):
    """Generate SQL, validate it, execute it, and save results."""

    with st.spinner("Generating SQL and querying the database..."):
        try:
            sql = generate_sql(question)
            result = execute_readonly(sql)

            st.session_state.history.append({
                "question": original_question or question,
                "clarified_question": (
                    question if original_question else None
                ),
                "sql": sql,
                "columns": result["columns"],
                "rows": result["rows"],
                "truncated": result["truncated"],
                "error": None,
            })

        except Exception as error:
            print(
                f"QueryPilot error: "
                f"{type(error).__name__}: {error}"
            )

            error_message = str(error)

            if isinstance(error, TimeoutError):
                friendly_message = (
                    "This query took too long to execute. "
                    "Try a simpler question."
                )

            elif (
                "cannot be answered using the current schema"
                in error_message.lower()
                or "cannot_answer" in error_message.lower()
            ):
                friendly_message = (
                    "I can't answer this question using the current "
                    "database. I can answer questions about customers, "
                    "products, orders, and order items. Try asking "
                    "about one of those."
                )

            elif isinstance(error, ValueError):
                friendly_message = (
                    f"I couldn't process that query: {error}"
                )

            else:
                friendly_message = (
                    "QueryPilot couldn't complete this request. "
                    "Check the VS Code terminal for the technical error."
                )

            st.session_state.history.append({
                "question": original_question or question,
                "clarified_question": (
                    question if original_question else None
                ),
                "sql": None,
                "columns": [],
                "rows": [],
                "truncated": False,
                "error": friendly_message,
            })


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

with st.sidebar:
    st.header("QueryPilot")
    st.write("Text-to-SQL Assistant")

    st.divider()

    st.write("**How it works**")
    st.write("1. Ask a question.")
    st.write("2. Check for ambiguity using rules and AI.")
    st.write("3. Generate and validate SQL.")
    st.write("4. Display results and charts.")

    st.divider()

    st.caption("Database: SQLite")
    st.caption("SQL validation: SQLGlot")
    st.caption("AI provider: Groq")
    st.caption("Clarification: Rules + AI")

    if st.button("Clear query history"):
        st.session_state.history = []
        st.session_state.pending_clarification = None
        st.rerun()


# --------------------------------------------------
# Ask a question
# --------------------------------------------------

st.subheader("Ask your database")

with st.form("query_form"):
    question = st.text_input(
        "Your question",
        placeholder="e.g. Who are my best customers?",
    )

    submitted = st.form_submit_button(
        "Submit question",
        type="primary",
    )


if submitted:
    if not question.strip():
        st.warning("Please enter a question.")

    else:
        # This checks existing rule-based patterns first.
        # If no rule matches, it asks Groq to detect ambiguity.
        # If AI detection fails, the detector returns None and the
        # normal SQL-generation flow can continue.
        clarification = detect_ai_clarification(question)

        if clarification:
            st.session_state.pending_clarification = clarification
            st.rerun()

        else:
            st.session_state.pending_clarification = None
            run_query(question)
            st.rerun()


# --------------------------------------------------
# Clarification interface
# --------------------------------------------------

pending = st.session_state.pending_clarification

if pending:
    st.divider()
    st.subheader("Let's clarify your question")

    st.write(f"**You asked:** {pending['original_question']}")
    st.write(pending["clarification"])

    if pending.get("source") == "ai":
        st.caption(
            "QueryPilot detected a possible ambiguity using AI. "
            "Choose the interpretation that best matches your intent."
        )

    with st.form("clarification_form"):
        choice = st.radio(
            "Choose an interpretation:",
            options=list(pending["options"].keys()),
            format_func=lambda key: pending["options"][key],
            key="clarification_choice",
        )

        confirmed = st.form_submit_button(
            "Confirm and run query",
            type="primary",
        )

    if confirmed:
        original_question = pending["original_question"]

        try:
            clarified_question = apply_clarification(
                original_question,
                choice,
                category=pending["category"],
            )

        except ValueError as error:
            st.error(f"Could not apply that choice: {error}")

        else:
            st.session_state.pending_clarification = None

            run_query(
                clarified_question,
                original_question=original_question,
            )

            st.rerun()


# --------------------------------------------------
# Query results, visualizations, and history
# --------------------------------------------------

if st.session_state.history:
    st.divider()
    st.subheader("Query results")

    for item in reversed(st.session_state.history):
        with st.container(border=True):

            st.markdown(f"**Question:** {item['question']}")

            if item["clarified_question"]:
                st.caption(
                    "Interpreted as: "
                    + item["clarified_question"]
                )

            if item["error"]:
                st.warning(item["error"])

            else:
                with st.expander("View generated SQL"):
                    st.code(item["sql"], language="sql")

                if item["rows"]:
                    dataframe = pd.DataFrame(
                        item["rows"],
                        columns=item["columns"],
                    )

                    chart_type = detect_chart_type(dataframe)

                    # Automatically display a bar chart.
                    if chart_type == "bar":
                        st.subheader("Data visualization")

                        chart_data = dataframe.set_index(
                            dataframe.columns[0]
                        )

                        st.bar_chart(
                            chart_data,
                            x_label=str(dataframe.columns[0]),
                            y_label="Value",
                        )

                    # Automatically display a line chart for date-like data.
                    elif chart_type == "line":
                        st.subheader("Data visualization")

                        chart_data = dataframe.copy()
                        date_column = chart_data.columns[0]

                        chart_data[date_column] = pd.to_datetime(
                            chart_data[date_column],
                            errors="coerce",
                        )

                        chart_data = chart_data.dropna(
                            subset=[date_column]
                        )

                        if not chart_data.empty:
                            chart_data = chart_data.set_index(
                                date_column
                            )

                            numeric_columns = (
                                chart_data.select_dtypes(
                                    include="number"
                                ).columns.tolist()
                            )

                            if numeric_columns:
                                st.line_chart(
                                    chart_data[numeric_columns],
                                    y_label="Value",
                                )

                    # Always retain the original data table.
                    st.subheader("Query results table")

                    st.dataframe(
                        dataframe,
                        use_container_width=True,
                        hide_index=True,
                    )

                else:
                    st.info(
                        "The query ran successfully but returned no rows."
                    )

            if item["truncated"]:
                st.warning(
                    "Only the first 200 rows are displayed."
                )
