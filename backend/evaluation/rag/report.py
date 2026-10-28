from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RESULTS_FILE = BASE_DIR / "results.csv"


def numeric_series(df: pd.DataFrame, column: str) -> pd.Series:
    """Return numeric values only, ignoring N/A and missing values."""
    if column not in df.columns:
        return pd.Series(dtype="float64")

    return pd.to_numeric(df[column], errors="coerce").dropna()


def split_by_category(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split evaluation results into answerable and negative cases."""
    if "case_category" not in df.columns:
        raise ValueError(
            "case_category is missing from results.csv. "
            "Update evaluation/rag/run.py and rerun evaluation."
        )

    categories = df["case_category"].fillna("").astype(str).str.strip().str.lower()

    if categories.eq("").any() or categories.eq("unknown").any():
        raise ValueError(
            "Every evaluation row must have a valid case_category. "
            "Check dataset.json and run.py."
        )

    answerable = df.loc[categories != "negative"].copy()
    negative = df.loc[categories == "negative"].copy()

    return answerable, negative


def print_mean_metric(
    df: pd.DataFrame,
    column: str,
    label: str,
) -> None:
    """Print a metric average and the number of scored cases."""
    values = numeric_series(df, column)

    if values.empty:
        print(f"{label}: N/A (no numeric scores)")
        return

    print(f"{label}: {values.mean():.2f} ({len(values)}/{len(df)} cases scored)")


def print_categorical_metric(
    df: pd.DataFrame,
    column: str,
    label: str,
    expected_values: tuple[str, ...],
) -> None:
    """Print counts for a categorical evaluation metric."""
    if column not in df.columns:
        print(f"{label}: column not found")
        return

    values = df[column].dropna().astype(str).str.strip().str.upper()

    if values.empty:
        print(f"{label}: N/A (no scored cases)")
        return

    counts = [f"{value}={(values == value).sum()}" for value in expected_values]

    print(f"{label}: {', '.join(counts)} ({len(values)} cases with a value)")


def get_case_label(row: pd.Series, index: object) -> str:
    """Find a useful test-case identifier from available columns."""
    for column in (
        "case_id",
        "id",
        "request",
        "inputs/question",
        "question",
    ):
        if column in row.index and pd.notna(row[column]):
            return f"{column}={row[column]}"

    return f"row={index}"


def main() -> None:
    if not RESULTS_FILE.exists():
        raise FileNotFoundError(
            f"Evaluation results were not found: {RESULTS_FILE}\n"
            "Run the RAG evaluation first."
        )

    df = pd.read_csv(RESULTS_FILE)

    if df.empty:
        print("The evaluation results file contains no rows.")
        return

    answerable_df, negative_df = split_by_category(df)

    print("\n=== RAG EVALUATION SUMMARY ===\n")
    print(f"Results file: {RESULTS_FILE}")
    print(f"Total cases: {len(df)}")
    print(f"Answerable cases: {len(answerable_df)}")
    print(f"Negative cases: {len(negative_df)}")

    # ---------------------------------------------------------
    # Retrieval source metrics
    # ---------------------------------------------------------

    print("\n--- Source metrics ---")

    print_mean_metric(
        df,
        "source_recall/value",
        "Source recall",
    )

    print_mean_metric(
        df,
        "source_precision/value",
        "Source precision",
    )

    # ---------------------------------------------------------
    # Overall RAG quality
    # ---------------------------------------------------------

    print("\n--- Overall RAG quality ---")

    print_categorical_metric(
        df,
        "commerceops_rag_quality/value",
        "RAG quality",
        ("PASS", "PARTIAL", "FAIL"),
    )

    # ---------------------------------------------------------
    # Answerable-case judge metrics
    # ---------------------------------------------------------

    print("\n--- Answerable cases: judge metrics ---")

    print_categorical_metric(
        answerable_df,
        "correctness/value",
        "Correctness",
        ("YES", "NO", "N/A"),
    )

    print_categorical_metric(
        answerable_df,
        "retrieval_groundedness/value",
        "Groundedness",
        ("YES", "NO", "N/A"),
    )

    print_categorical_metric(
        answerable_df,
        "retrieval_sufficiency/value",
        "Retrieval sufficiency",
        ("YES", "NO", "N/A"),
    )

    print_mean_metric(
        answerable_df,
        "retrieval_relevance/precision/value",
        "Retrieval relevance precision (diagnostic)",
    )

    # ---------------------------------------------------------
    # Negative-case abstention metrics
    # ---------------------------------------------------------

    print("\n--- Negative cases: abstention ---")

    print_categorical_metric(
        negative_df,
        "abstention_quality/value",
        "Abstention quality",
        ("PASS", "FAIL", "N/A"),
    )

    print_categorical_metric(
        negative_df,
        "commerceops_rag_quality/value",
        "Negative-case RAG quality",
        ("PASS", "PARTIAL", "FAIL"),
    )

    # ---------------------------------------------------------
    # Identify cases needing attention
    # ---------------------------------------------------------

    print("\n=== CASES NEEDING ATTENTION ===\n")

    attention = pd.Series(False, index=df.index)

    # Overall quality failures or incomplete answers.
    quality_column = "commerceops_rag_quality/value"

    if quality_column in df.columns:
        quality = df[quality_column].fillna("").astype(str).str.strip().str.upper()
        attention |= quality.isin(("PARTIAL", "FAIL"))

    # Source precision and recall are review criteria.
    # Retrieval relevance is diagnostic and does not flag a case alone.
    for column in (
        "source_precision/value",
        "source_recall/value",
    ):
        values = numeric_series(df, column).reindex(df.index)
        attention |= values.notna() & (values < 1.0)

    # Judge failures are assessed only for answerable cases.
    for column in (
        "correctness/value",
        "retrieval_groundedness/value",
        "retrieval_sufficiency/value",
    ):
        if column not in answerable_df.columns:
            continue

        values = answerable_df[column].fillna("").astype(str).str.strip().str.lower()

        failed_indices = values.index[values.eq("no")]
        attention.loc[failed_indices] = True

    # A negative case needs review if abstention failed.
    abstention_column = "abstention_quality/value"

    if abstention_column in negative_df.columns:
        abstention = (
            negative_df[abstention_column]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        failed_indices = abstention.index[abstention.eq("FAIL")]
        attention.loc[failed_indices] = True

    flagged = df.loc[attention]

    if flagged.empty:
        print("No cases were flagged by the configured rules.")
    else:
        for index, row in flagged.iterrows():
            print(f"- {get_case_label(row, index)}")

            for column in (
                "case_category",
                "commerceops_rag_quality/value",
                "source_recall/value",
                "source_precision/value",
                "retrieval_relevance/precision/value",
                "correctness/value",
                "retrieval_groundedness/value",
                "retrieval_sufficiency/value",
                "abstention_quality/value",
            ):
                if column in row.index and pd.notna(row[column]):
                    print(f"    {column}: {row[column]}")

    print(
        "\nNote: Retrieval relevance precision is shown as a diagnostic "
        "metric and does not independently flag a case. Review scorer "
        "rationales and retrieved context before changing retrieval settings."
    )


if __name__ == "__main__":
    main()
