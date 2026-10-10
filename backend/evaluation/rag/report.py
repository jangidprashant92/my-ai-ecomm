from pathlib import Path

import pandas as pd

RESULTS_FILE = Path(__file__).resolve().parent / "results.csv"


def main() -> None:
    df = pd.read_csv(RESULTS_FILE)

    print("\n=== RAG EVALUATION SUMMARY ===\n")

    print(f"Total cases: {len(df)}")

    # ---------------------------------------------------------
    # Source metrics
    # ---------------------------------------------------------

    print(f"Source recall: {df['source_recall/value'].mean():.2f}")

    print(f"Source precision: {df['source_precision/value'].mean():.2f}")

    # ---------------------------------------------------------
    # RAG quality
    # ---------------------------------------------------------

    quality = df["commerceops_rag_quality/value"]

    print(f"RAG quality PASS: {(quality == 'PASS').sum()}/{len(df)}")

    print(f"RAG quality PARTIAL: {(quality == 'PARTIAL').sum()}/{len(df)}")

    print(f"RAG quality FAIL: {(quality == 'FAIL').sum()}/{len(df)}")

    # ---------------------------------------------------------
    # Abstention
    # ---------------------------------------------------------

    abstention = df["abstention_quality/value"].dropna()

    if not abstention.empty:
        print(f"Abstention PASS: {(abstention == 'PASS').sum()}/{len(abstention)}")

    # ---------------------------------------------------------
    # Correctness
    # ---------------------------------------------------------

    correctness = df["correctness/value"].dropna()

    print(f"Correctness YES: {(correctness == 'yes').sum()}/{len(correctness)}")

    # ---------------------------------------------------------
    # Retrieval precision
    # ---------------------------------------------------------

    precision = df["retrieval_relevance/precision/value"].dropna()

    if not precision.empty:
        print(f"Retrieval precision: {precision.mean():.2f}")

    print("\n=== CASES NEEDING ATTENTION ===\n")

    attention = df[
        (df["commerceops_rag_quality/value"] != "PASS")
        | (df["retrieval_relevance/precision/value"].fillna(1.0) < 1.0)
    ]

    if attention.empty:
        print("None")
    else:
        for _, row in attention.iterrows():
            print(row["request"])


if __name__ == "__main__":
    main()
