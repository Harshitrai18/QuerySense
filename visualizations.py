
import pandas as pd


def detect_chart_type(dataframe):
    """Choose a suitable chart type for a query result."""

    if dataframe.empty or len(dataframe.columns) < 2:
        return None

    if len(dataframe) < 2 or len(dataframe) > 50:
        return None

    numeric_columns = dataframe.select_dtypes(
        include="number"
    ).columns.tolist()

    if not numeric_columns:
        return None

    first_column = str(dataframe.columns[0]).lower()
    date_words = ("date", "day", "month", "year", "time")

    if any(word in first_column for word in date_words):
        return "line"

    first_column_values = dataframe.iloc[:, 0]
    unique_count = first_column_values.nunique()

    if 2 <= unique_count <= 20:
        return "bar"

    return None
