
import pandas as pd
from visualizations import detect_chart_type


def test_bar_chart_detection():
    dataframe = pd.DataFrame({
        "city": ["Delhi", "Mumbai", "Pune"],
        "revenue": [1200, 900, 700],
    })

    assert detect_chart_type(dataframe) == "bar"


def test_line_chart_detection():
    dataframe = pd.DataFrame({
        "order_date": ["2026-10-01", "2026-10-02", "2026-10-03"],
        "total_orders": [3, 5, 4],
    })

    assert detect_chart_type(dataframe) == "line"


def test_no_chart_for_single_column():
    dataframe = pd.DataFrame({
        "customer_name": ["Aman", "Riya", "Karan"],
    })

    assert detect_chart_type(dataframe) is None


def test_no_chart_for_empty_data():
    dataframe = pd.DataFrame({
        "city": [],
        "revenue": [],
    })

    assert detect_chart_type(dataframe) is None


if __name__ == "__main__":
    test_bar_chart_detection()
    test_line_chart_detection()
    test_no_chart_for_single_column()
    test_no_chart_for_empty_data()

    print("All chart detection tests passed!")
