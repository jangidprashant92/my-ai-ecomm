from __future__ import annotations

import json
from pathlib import Path

import mlflow
from evaluation.rag.predictor import predict
from evaluation.rag.scorers import (
    rag_quality_judge,
    source_recall,
)
from mlflow.genai import evaluate

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
            ],
        )

        print("\nEvaluation complete.")
        print(results)

        print("\nPer-row evaluation results:")

        print(
            results.result_df[
                [
                    "inputs",
                    "outputs",
                    "source_recall",
                ]
            ].to_string(index=False)
        )


if __name__ == "__main__":
    main()
