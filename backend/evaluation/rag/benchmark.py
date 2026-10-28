"""Controlled retrieval benchmark: baseline vs MMR vs hybrid.

Each strategy runs `evaluation.rag.run` in its own subprocess with its own
environment variables, so cached retrievers and import-time settings cannot
leak between strategies.

Usage (from backend/):
    uv run python -m evaluation.rag.benchmark
    uv run python -m evaluation.rag.benchmark --reuse   # re-aggregate saved CSVs
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parents[1]
OUT_DIR = BASE_DIR / "benchmarks"

# ASSUMPTION: verify these values against what your retriever factory accepts
# (see app/ai/rag/vector_store.py / service.py). "baseline" must reproduce the
# frozen Reranker v1 configuration exactly.
STRATEGIES: dict[str, dict[str, str]] = {
    "baseline": {"RAG_RETRIEVAL_TYPE": "similarity", "RAG_USE_MMR": "false"},
    "mmr": {"RAG_RETRIEVAL_TYPE": "mmr", "RAG_USE_MMR": "true"},
    "hybrid": {"RAG_RETRIEVAL_TYPE": "hybrid", "RAG_USE_MMR": "false"},
}

# ASSUMPTION: adjust to the category values used in dataset.json.
NEGATIVE_CATEGORIES = {"negative", "unanswerable"}

ANSWERABLE_METRICS = {
    "source_recall": "source_recall/value",
    "source_precision": "source_precision/value",
    "correctness": "correctness/value",
    "groundedness": "retrieval_groundedness/value",
    "sufficiency": "retrieval_sufficiency/value",
    "rag_quality": "commerceops_rag_quality/value",
    "relevance_precision": "retrieval_relevance/precision/value",
}
NEGATIVE_METRICS = {"abstention": "abstention_quality/value"}

# Acceptance gates. A candidate must pass ALL to be eligible.
MIN_ABSTENTION = 1.0
MIN_ABSOLUTE_QUALITY = 0.9  # correctness, groundedness, sufficiency
MAX_P95_LATENCY_RATIO = 1.5  # vs baseline
NO_REGRESSION_METRICS = [
    "source_recall",
    "correctness",
    "groundedness",
    "sufficiency",
    "rag_quality",
]


def to_score(value) -> float | None:
    """Normalise MLflow/custom scorer outputs (yes/no, pass/fail, numbers) to floats."""
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return None
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().lower()
    if text in {"yes", "true", "pass", "passed"}:
        return 1.0
    if text in {"no", "false", "fail", "failed"}:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return None


def _mean(df: pd.DataFrame, column: str) -> float | None:
    if column not in df.columns:
        return None
    scores = [s for s in (to_score(v) for v in df[column]) if s is not None]
    return sum(scores) / len(scores) if scores else None


def summarize(df: pd.DataFrame, latencies_ms: list[float]) -> dict:
    if "case_category" not in df.columns:
        raise ValueError("results are missing 'case_category'")
    is_negative = df["case_category"].astype(str).str.lower().isin(NEGATIVE_CATEGORIES)
    answerable, negative = df[~is_negative], df[is_negative]

    summary: dict = {
        "n_answerable": len(answerable),
        "n_negative": len(negative),
    }
    for name, col in ANSWERABLE_METRICS.items():
        summary[name] = _mean(answerable, col)
    for name, col in NEGATIVE_METRICS.items():
        summary[name] = _mean(negative, col)

    lat = pd.Series(latencies_ms, dtype=float)
    summary["latency_p50_ms"] = float(lat.quantile(0.5)) if len(lat) else None
    summary["latency_p95_ms"] = float(lat.quantile(0.95)) if len(lat) else None
    return summary


def evaluate_gates(baseline: dict, candidate: dict) -> list[str]:
    """Return a list of failed-gate messages; empty list means the candidate passes."""
    failures: list[str] = []

    for metric in NO_REGRESSION_METRICS:
        b, c = baseline.get(metric), candidate.get(metric)
        if b is None or c is None:
            failures.append(f"{metric}: missing value")
        elif c < b - 1e-9:
            failures.append(f"{metric}: {c:.3f} < baseline {b:.3f}")

    for metric in ("correctness", "groundedness", "sufficiency"):
        c = candidate.get(metric)
        if c is not None and c < MIN_ABSOLUTE_QUALITY:
            failures.append(f"{metric}: {c:.3f} < floor {MIN_ABSOLUTE_QUALITY}")

    abst = candidate.get("abstention")
    if abst is None or abst < MIN_ABSTENTION:
        failures.append(f"abstention: {abst} < {MIN_ABSTENTION}")

    b95, c95 = baseline.get("latency_p95_ms"), candidate.get("latency_p95_ms")
    if b95 and c95 and c95 > b95 * MAX_P95_LATENCY_RATIO:
        failures.append(
            f"latency_p95: {c95:.0f}ms > {MAX_P95_LATENCY_RATIO}x baseline {b95:.0f}ms"
        )

    return failures


def select_winner(summaries: dict[str, dict], failures: dict[str, list[str]]) -> str:
    """Baseline wins ties. A candidate must pass every gate AND strictly improve the ranking key."""

    def key(s: dict) -> tuple[float, float]:
        precision = round(s.get("source_precision") or 0.0, 3)
        latency_bucket = round((s.get("latency_p50_ms") or 0.0) / 100)
        return (precision, -latency_bucket)

    best = "baseline"
    for name, summary in summaries.items():
        if name == "baseline" or failures.get(name):
            continue
        if key(summary) > key(summaries[best]):
            best = name
    return best


def _fmt(value) -> str:
    if value is None:
        return "n/a"
    return (
        f"{value:.3f}" if isinstance(value, float) and value <= 1.5 else f"{value:.0f}"
    )


def render_markdown(summaries: dict, failures: dict, winner: str) -> str:
    metrics = [
        *ANSWERABLE_METRICS,
        *NEGATIVE_METRICS,
        "latency_p50_ms",
        "latency_p95_ms",
    ]
    names = list(summaries)
    lines = [
        "# RAG Retrieval Benchmark",
        "",
        "| Metric | " + " | ".join(names) + " |",
        "|---|" + "---|" * len(names),
    ]
    for metric in metrics:
        lines.append(
            f"| {metric} | "
            + " | ".join(_fmt(summaries[n].get(metric)) for n in names)
            + " |"
        )
    lines += ["", "## Gate results", ""]
    for name in names:
        if name == "baseline":
            lines.append("- **baseline**: reference")
        elif failures[name]:
            lines.append(f"- **{name}**: FAIL — " + "; ".join(failures[name]))
        else:
            lines.append(f"- **{name}**: PASS")
    lines += ["", f"## Selected strategy: `{winner}`", ""]
    lines.append(
        "Note: the dataset has few cases, so small differences are noise. "
        "Ties go to the baseline."
    )
    return "\n".join(lines)


def run_strategy(name: str, env_overrides: dict[str, str]) -> None:
    output = OUT_DIR / f"{name}.csv"
    env = {**os.environ, **env_overrides}
    cmd = [
        sys.executable,
        "-m",
        "evaluation.rag.run",
        "--output",
        str(output),
        "--label",
        f"benchmark-{name}",
    ]
    print(f"\n=== Running strategy: {name} ({env_overrides}) ===")
    subprocess.run(cmd, cwd=BACKEND_DIR, env=env, check=True)


def load_strategy(name: str) -> tuple[pd.DataFrame, list[float]]:
    csv_path = OUT_DIR / f"{name}.csv"
    latency_path = csv_path.with_suffix(".latency.json")
    df = pd.read_csv(csv_path)
    latencies = json.loads(latency_path.read_text(encoding="utf-8"))["latencies_ms"]
    if len(latencies) > 1:
        latencies = latencies[
            1:
        ]  # drop the cold validation call (same for every strategy)
    return df, latencies


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reuse", action="store_true", help="skip runs; aggregate saved CSVs"
    )
    parser.add_argument(
        "--only", nargs="*", choices=list(STRATEGIES), help="run a subset"
    )
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not args.reuse:
        for name in args.only or STRATEGIES:
            run_strategy(name, STRATEGIES[name])

    available = [n for n in STRATEGIES if (OUT_DIR / f"{n}.csv").exists()]
    if "baseline" not in available:
        raise SystemExit("baseline.csv missing: run `--only baseline` first")

    summaries = {}
    for name in available:
        df, latencies = load_strategy(name)
        summaries[name] = summarize(df, latencies)

    failures = {
        n: evaluate_gates(summaries["baseline"], s)
        for n, s in summaries.items()
        if n != "baseline"
    }
    winner = select_winner(summaries, failures)

    report = render_markdown(summaries, {"baseline": [], **failures}, winner)
    (OUT_DIR / "benchmark_report.md").write_text(report, encoding="utf-8")
    (OUT_DIR / "benchmark_summary.json").write_text(
        json.dumps(
            {"summaries": summaries, "failures": failures, "winner": winner}, indent=2
        ),
        encoding="utf-8",
    )
    print("\n" + report)


if __name__ == "__main__":
    main()
