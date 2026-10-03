from __future__ import annotations

import json
from pathlib import Path

import mlflow
from app.core.config import settings
from evaluation.rag.predictor import predict
from evaluation.rag.scorers import (
    rag_quality_judge,
    source_recall,
)
from mlflow.genai import evaluate
from mlflow.genai.scorers import (
    RetrievalGroundedness,
    RetrievalRelevance,
    RetrievalSufficiency,
)

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset.json"


def load_dataset() -> list[dict]:
    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def main() -> None:
    dataset = load_dataset()

    mlflow.set_tracking_uri(
        "http://127.0.0.1:8080",
    )

    mlflow.set_experiment(
        "CommerceOps RAG Evaluation",
    )

    with mlflow.start_run(
        run_name="rag-baseline",
    ):
        results = evaluate(
            data=dataset,
            predict_fn=predict,
            scorers=[
                source_recall,
                rag_quality_judge,
                RetrievalRelevance(
                    model=settings.EVAL_JUDGE_MODEL,
                ),
                RetrievalGroundedness(
                    model=settings.EVAL_JUDGE_MODEL,
                ),
                RetrievalSufficiency(
                    model=settings.EVAL_JUDGE_MODEL,
                ),
            ],
        )

        print("\nEvaluation complete.")
        print(results)

        print("\nResult DataFrame columns:")
        print(
            results.result_df.columns.tolist(),
        )

        # print("\nPer-row evaluation results:")
        # print(
        #     results.result_df.to_string(
        #         index=False,
        #     )
        # )


if __name__ == "__main__":
    main()
