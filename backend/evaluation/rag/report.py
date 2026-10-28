from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RESULTS_FILE = BASE_DIR / "results.csv"


def numeric_series(
    df: pd.DataFrame,
    column: str,
) -> pd.Series:
    """Return numeric values only, ignoring N/A and missing values."""

    if column not in df.columns:
        return pd.Series(dtype="float64")

    return pd.to_numeric(df[column], errors="coerce").dropna()


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


def get_case_label(
    row: pd.Series,
    index: object,
) -> str:
    """Find a useful test-case identifier from the available columns."""

    for column in ("id", "request", "inputs/question", "question"):
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

    print("\n=== RAG EVALUATION SUMMARY ===\n")
    print(f"Results file: {RESULTS_FILE}")
    print(f"Total cases: {len(df)}")

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
    # Abstention
    # ---------------------------------------------------------

    print("\n--- Abstention ---")

    print_categorical_metric(
        df,
        "abstention_quality/value",
        "Abstention quality",
        ("PASS", "FAIL", "N/A"),
    )

    # ---------------------------------------------------------
    # Answer and retrieval judge metrics
    # ---------------------------------------------------------

    print("\n--- Judge metrics ---")

    print_categorical_metric(
        df,
        "correctness/value",
        "Correctness",
        ("YES", "NO", "N/A"),
    )

    print_categorical_metric(
        df,
        "retrieval_groundedness/value",
        "Groundedness",
        ("YES", "NO", "N/A"),
    )

    print_categorical_metric(
        df,
        "retrieval_sufficiency/value",
        "Retrieval sufficiency",
        ("YES", "NO", "N/A"),
    )

    print_mean_metric(
        df,
        "retrieval_relevance/precision/value",
        "Retrieval relevance precision",
    )

    # ---------------------------------------------------------
    # Identify cases needing attention
    # ---------------------------------------------------------

    print("\n=== CASES NEEDING ATTENTION ===\n")

    attention = pd.Series(False, index=df.index)

    # Overall quality failures or incomplete answers.
    if "commerceops_rag_quality/value" in df.columns:
        quality = (
            df["commerceops_rag_quality/value"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )
        attention |= quality.isin(("PARTIAL", "FAIL"))

    # Low numeric source precision or recall.
    for column in (
        "source_precision/value",
        "source_recall/value",
        "retrieval_relevance/precision/value",
    ):
        values = numeric_series(df, column).reindex(df.index)
        attention |= values.notna() & (values < 1.0)

    # Judge failures. N/A is deliberately not treated as a failure.
    for column in (
        "correctness/value",
        "retrieval_groundedness/value",
        "retrieval_sufficiency/value",
    ):
        if column not in df.columns:
            continue

        values = df[column].fillna("").astype(str).str.strip().str.lower()
        attention |= values.eq("no")

    flagged = df.loc[attention]

    if flagged.empty:
        print("No cases were flagged by the configured rules.")
    else:
        for index, row in flagged.iterrows():
            print(f"- {get_case_label(row, index)}")

            for column in (
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
        "\nNote: A case can be flagged for review even when abstention "
        "is correct. Review the question type and scorer rationale before "
        "changing retrieval settings."
    )


if __name__ == "__main__":
    main()
