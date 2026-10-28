import pandas as pd
import pytest
from evaluation.rag.report import (
    get_case_label,
    numeric_series,
    split_by_category,
)


def test_split_by_category_separates_answerable_and_negative_cases():
    df = pd.DataFrame(
        {
            "case_id": ["rag-001", "rag-009", "rag-004"],
            "case_category": ["direct", "negative", "cross_policy"],
        }
    )

    answerable_df, negative_df = split_by_category(df)

    assert answerable_df["case_id"].tolist() == [
        "rag-001",
        "rag-004",
    ]
    assert negative_df["case_id"].tolist() == ["rag-009"]


def test_split_by_category_requires_category_column():
    df = pd.DataFrame(
        {
            "case_id": ["rag-001"],
        }
    )

    with pytest.raises(ValueError, match="case_category"):
        split_by_category(df)


def test_numeric_series_ignores_na_and_invalid_values():
    df = pd.DataFrame(
        {
            "source_recall/value": [1.0, "N/A", None, 0.5, "invalid"],
        }
    )

    values = numeric_series(df, "source_recall/value")

    assert values.tolist() == [1.0, 0.5]
    assert values.mean() == pytest.approx(0.75)


def test_numeric_series_returns_empty_for_missing_column():
    df = pd.DataFrame({"case_id": ["rag-001"]})

    values = numeric_series(df, "missing_metric/value")

    assert values.empty


def test_get_case_label_prefers_case_id():
    row = pd.Series(
        {
            "case_id": "rag-004",
            "request": "{'question': 'Compare deadlines'}",
        }
    )

    assert get_case_label(row, 3) == "case_id=rag-004"


def test_get_case_label_falls_back_to_row_index():
    row = pd.Series({"case_id": None})

    assert get_case_label(row, 7) == "row=7"


def test_split_by_category_rejects_unknown_category():
    df = pd.DataFrame(
        {
            "case_id": ["rag-001"],
            "case_category": ["unknown"],
        }
    )

    with pytest.raises(ValueError, match="valid case_category"):
        split_by_category(df)
