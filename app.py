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
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# Visual styling
# --------------------------------------------------

st.markdown(
    """
    <style>
    :root {
        --qp-blue: #3157D5;
        --qp-blue-dark: #2445B3;
        --qp-ink: #172033;
        --qp-muted: #64748B;
        --qp-border: #E2E8F0;
        --qp-panel: #F8FAFC;
    }

    .block-container {
        max-width: 1240px;
        padding-top: 3rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid var(--qp-border);
    }

    [data-testid="stSidebar"] .block-container {
        padding-top: 1.6rem;
    }

    .qp-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 8px;
    }

    .qp-brand-icon {
        width: 46px;
        height: 46px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 24px;
        background: linear-gradient(135deg, #4268E8 0%, #2747B8 100%);
        box-shadow: 0 7px 18px rgba(49, 87, 213, 0.22);
    }

    .qp-brand-name {
        color: var(--qp-ink);
        font-size: 1.75rem;
        font-weight: 750;
        letter-spacing: -0.045em;
        line-height: 1.1;
    }

    .qp-brand-subtitle {
        color: var(--qp-muted);
        font-size: 0.92rem;
        margin-top: 5px;
    }

    .qp-eyebrow {
        color: var(--qp-blue);
        font-size: 0.75rem;
        font-weight: 750;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.4rem;
    }

    .qp-hero-title {
        color: var(--qp-ink);
        font-size: clamp(1.8rem, 3vw, 2.45rem);
        font-weight: 760;
        letter-spacing: -0.05em;
        line-height: 1.13;
        margin: 0 0 0.6rem 0;
    }

    .qp-hero-copy {
        color: var(--qp-muted);
        font-size: 1.02rem;
        line-height: 1.6;
        margin-bottom: 1.4rem;
    }

    .qp-section-title {
        color: var(--qp-ink);
        font-size: 1.2rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        margin-bottom: 0.2rem;
    }

    .qp-section-copy {
        color: var(--qp-muted);
        font-size: 0.9rem;
        margin-bottom: 0.9rem;
    }

    .qp-status {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        color: #166534;
        background: #F0FDF4;
        border: 1px solid #BBF7D0;
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 650;
        white-space: nowrap;
    }

    .qp-status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #22C55E;
    }

    div[data-testid="stForm"] {
        border: 1px solid var(--qp-border);
        border-radius: 18px;
        padding: 1.2rem 1.25rem 1rem 1.25rem;
        background: var(--qp-panel);
    }

    div[data-testid="stTextInput"] label,
    div[data-testid="stRadio"] label {
        font-weight: 650;
    }

    div[data-testid="stTextInput"] input {
        border-radius: 10px;
        min-height: 46px;
    }

    .stButton > button,
    div[data-testid="stFormSubmitButton"] > button {
        border-radius: 10px;
        min-height: 43px;
        font-weight: 650;
        transition: all 0.15s ease-in-out;
    }

    div[data-testid="stFormSubmitButton"] > button[kind="primary"],
    .stButton > button[kind="primary"] {
        box-shadow: 0 5px 12px rgba(49, 87, 213, 0.16);
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 15px;
    }

    div[data-testid="stExpander"] {
        border-radius: 11px;
        border-color: var(--qp-border);
    }

    [data-testid="stDataFrame"] {
        border: 1px solid var(--qp-border);
        border-radius: 11px;
        overflow: hidden;
    }

    hr {
        border-color: var(--qp-border);
    }

    @media (max-width: 700px) {
        .block-container {
            padding-top: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .qp-brand-name {
            font-size: 1.5rem;
        }

        div[data-testid="stForm"] {
            padding: 0.9rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
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
    st.markdown(
        """
        <div class="qp-brand">
            <div class="qp-brand-icon">⌕</div>
            <div>
                <div class="qp-brand-name">QueryPilot</div>
                <div class="qp-brand-subtitle">Text-to-SQL assistant</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("#### How it works")
    st.markdown(
        """
        <div style="color:#64748B; font-size:0.9rem; line-height:1.75;">
        <b style="color:#3157D5;">01</b> &nbsp; Ask in plain English<br>
        <b style="color:#3157D5;">02</b> &nbsp; Clarify if needed<br>
        <b style="color:#3157D5;">03</b> &nbsp; Generate and validate SQL<br>
        <b style="color:#3157D5;">04</b> &nbsp; Explore results and charts
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("#### System information")
    st.caption("Database · SQLite")
    st.caption("SQL validation · SQLGlot")
    st.caption("AI provider · Groq")
    st.caption("Clarification · Rules + AI")

    st.divider()

    st.markdown("#### Query history")
    st.caption(
        f"{len(st.session_state.history)} "
        f"{'query' if len(st.session_state.history) == 1 else 'queries'} "
        "in this session"
    )

    if st.button("Clear query history", use_container_width=True):
        st.session_state.history = []
        st.session_state.pending_clarification = None
        st.rerun()


# --------------------------------------------------
# Main header
# --------------------------------------------------

header_left, header_right = st.columns([5, 1.4], vertical_alignment="center")

with header_left:
    st.markdown('<div class="qp-eyebrow">YOUR DATABASE, IN PLAIN ENGLISH</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="qp-hero-title">Ask questions. Get answers.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="qp-hero-copy">Turn everyday questions into database results '
        'with AI-assisted SQL generation.</div>',
        unsafe_allow_html=True,
    )

with header_right:
    st.markdown(
        '<div style="text-align:right; padding-bottom:1.1rem;">'
        '<span class="qp-status"><span class="qp-status-dot"></span>Ready to query</span>'
        '</div>',
        unsafe_allow_html=True,
    )


# --------------------------------------------------
# Ask a question
# --------------------------------------------------

st.markdown('<div class="qp-section-title">Ask your database</div>',
            unsafe_allow_html=True)
st.markdown(
    '<div class="qp-section-copy">Enter a question about customers, products, '
    'orders, or order items.</div>',
    unsafe_allow_html=True,
)

with st.form("query_form"):
    question = st.text_input(
        "Your question",
        placeholder="e.g. Which products generate the most revenue?",
    )

    submitted = st.form_submit_button(
        "✦  Generate answer",
        type="primary",
        use_container_width=True,
    )


if submitted:
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        # Check existing rule-based patterns first, then AI-based ambiguity.
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
    st.markdown("---")
    st.markdown('<div class="qp-section-title">Let’s clarify your question</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="qp-section-copy">Choose the interpretation that best '
        'matches what you want to know.</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown("**Your question**")
        st.info(pending["original_question"])
        st.markdown(f"**{pending['clarification']}**")

        if pending.get("source") == "ai":
            st.caption(
                "QueryPilot detected a possible ambiguity using AI. "
                "Choose the interpretation that best matches your intent."
            )

        with st.form("clarification_form"):
            choice = st.radio(
                "Choose an interpretation",
                options=list(pending["options"].keys()),
                format_func=lambda key: pending["options"][key],
                key="clarification_choice",
            )

            confirmed = st.form_submit_button(
                "Confirm and run query",
                type="primary",
                use_container_width=True,
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
    st.markdown("---")
    st.markdown('<div class="qp-section-title">Query results</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="qp-section-copy">Your latest questions and their results '
        'appear first.</div>',
        unsafe_allow_html=True,
    )

    for index, item in enumerate(reversed(st.session_state.history), start=1):
        with st.container(border=True):
            question_col, status_col = st.columns([5, 1.2], vertical_alignment="center")

            with question_col:
                st.markdown(f"**{item['question']}**")
                if item["clarified_question"]:
                    st.caption(
                        "Interpreted as: " + item["clarified_question"]
                    )

            with status_col:
                if item["error"]:
                    st.caption("Request needs attention")
                else:
                    st.caption("Query complete")

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

                    if chart_type == "bar":
                        st.markdown("**Data visualization**")
                        chart_data = dataframe.set_index(dataframe.columns[0])
                        st.bar_chart(
                            chart_data,
                            x_label=str(dataframe.columns[0]),
                            y_label="Value",
                        )

                    elif chart_type == "line":
                        st.markdown("**Data visualization**")
                        chart_data = dataframe.copy()
                        date_column = chart_data.columns[0]

                        chart_data[date_column] = pd.to_datetime(
                            chart_data[date_column],
                            errors="coerce",
                        )

                        chart_data = chart_data.dropna(subset=[date_column])

                        if not chart_data.empty:
                            chart_data = chart_data.set_index(date_column)
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

                    st.markdown("**Results table**")
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
                st.warning("Only the first 200 rows are displayed.")

st.markdown(
    """
    <div style="text-align:center; color:#94A3B8; font-size:0.78rem;
                padding-top:2.5rem;">
        QueryPilot · AI-assisted database querying with read-only SQL validation
    </div>
    """,
    unsafe_allow_html=True,
)
