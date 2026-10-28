from __future__ import annotations

import argparse
import functools
import json
import time
from pathlib import Path

import mlflow
from app.core.config import settings
from dotenv import load_dotenv
from evaluation.rag.predictor import predict
from evaluation.rag.scorers import (
    abstention_quality,
    rag_quality_judge,
    source_precision,
    source_recall,
)
from mlflow.genai import evaluate
from mlflow.genai.scorers import (
    Correctness,
    RetrievalGroundedness,
    RetrievalRelevance,
    RetrievalSufficiency,
)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset.json"
DEFAULT_OUTPUT = BASE_DIR / "results.csv"


def load_dataset() -> list[dict]:
    with DATASET_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def main(output_path: Path = DEFAULT_OUTPUT, label: str | None = None) -> None:
    dataset = load_dataset()

    mlflow.set_tracking_uri("http://127.0.0.1:8080")
    mlflow.set_experiment("CommerceOps RAG Evaluation")

    retrieval_type = settings.RAG_RETRIEVAL_TYPE.strip().lower()
    print(f"Retrieval strategy: {retrieval_type}")
    run_name = label or f"rag-{retrieval_type}"

    # MLflow may call predict_fn from several threads; list.append is thread-safe.
    latencies_ms: list[float] = []

    @functools.wraps(predict)
    def timed_predict(*args, **kwargs):
        start = time.perf_counter()
        try:
            return predict(*args, **kwargs)
        finally:
            latencies_ms.append((time.perf_counter() - start) * 1000)

    with mlflow.start_run(run_name=run_name):
        mlflow.log_param("rag_retrieval_type", retrieval_type)
        mlflow.log_param("rag_hybrid_rrf_k", settings.RAG_HYBRID_RRF_K)
        mlflow.log_param("rag_use_mmr", settings.RAG_USE_MMR)
        mlflow.log_param("rag_mmr_fetch_k", settings.RAG_MMR_FETCH_K)
        mlflow.log_param("rag_mmr_lambda_mult", settings.RAG_MMR_LAMBDA_MULT)

        results = evaluate(
            data=dataset,
            predict_fn=timed_predict,
            scorers=[
                source_recall,
                source_precision,
                abstention_quality,
                rag_quality_judge,
                RetrievalRelevance(model=settings.EVAL_JUDGE_MODEL),
                RetrievalGroundedness(model=settings.EVAL_JUDGE_MODEL),
                RetrievalSufficiency(model=settings.EVAL_JUDGE_MODEL),
                Correctness(model=settings.EVAL_JUDGE_MODEL),
            ],
        )

        print("\nEvaluation complete.")
        print(results)

        columns = [
            "trace_id",
            "source_recall/value",
            "abstention_quality/value",
            "commerceops_rag_quality/value",
            "retrieval_relevance/value",
            "retrieval_relevance/precision/value",
            "retrieval_groundedness/value",
            "retrieval_sufficiency/value",
            "correctness/value",
            "source_precision/value",
        ]
        available = [c for c in columns if c in results.result_df.columns]  # type: ignore
        print(results.result_df[available].to_string(index=False))  # type: ignore

        result_df = results.result_df.copy()
        if len(result_df) != len(dataset):
            raise RuntimeError(
                f"Evaluation returned {len(result_df)} rows for "
                f"{len(dataset)} dataset cases. Cannot safely attach case metadata."
            )

        result_df = result_df.drop(
            columns=["case_id", "case_category"], errors="ignore"
        )
        result_df.insert(
            0, "case_id", [c.get("id", f"case-{i + 1}") for i, c in enumerate(dataset)]
        )
        result_df.insert(
            1, "case_category", [c.get("category", "unknown") for c in dataset]
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        result_df.to_csv(output_path, index=False)

        latency_path = output_path.with_suffix(".latency.json")
        latency_path.write_text(
            json.dumps({"label": run_name, "latencies_ms": latencies_ms}, indent=2),
            encoding="utf-8",
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--label", type=str, default=None)
    args = parser.parse_args()
    main(output_path=args.output, label=args.label)
