from __future__ import annotations

from typing import Any, Literal

from app.core.config import settings
from mlflow.entities import Feedback
from mlflow.genai import scorer
from mlflow.genai.judges import make_judge

rag_quality_judge = make_judge(
    name="commerceops_rag_quality",
    description=(
        "Evaluates whether a CommerceOps RAG response is "
        "correct, grounded, and appropriate for the user's question."
    ),
    instructions="""
You are evaluating a CommerceOps RAG response.

Evaluate the response against:

1. The user's question.
2. The retrieved knowledge-base context.
3. The expected facts.
4. The expected answer behavior.

A response is PASS only when:

- It directly answers the user's question.
- Its important claims are supported by the retrieved context.
- It does not contradict the expected facts.
- It does not invent policy information.
- It handles an unanswerable question correctly when no
  relevant knowledge exists.
- For a conversational question, it correctly resolves the
  conversation context.

A response is PARTIAL when the main answer is correct but
important information is missing or an unsupported minor claim
is included.

A response is FAIL when the answer is incorrect, contradicts
the knowledge base, hallucinates important information, or
fails to answer the question.

User input:
{{ inputs }}

Expected behavior:
{{ expectations }}

Actual response:
{{ outputs }}

Return exactly one category:

PASS
PARTIAL
FAIL
""",
    model=settings.EVAL_JUDGE_MODEL,
    feedback_value_type=Literal[
        "PASS",
        "PARTIAL",
        "FAIL",
    ],
)


@scorer
def source_recall(
    *,
    outputs: Any | None,
    expectations: dict[str, Any] | None,
) -> Feedback:

    if not isinstance(outputs, dict):
        return Feedback(
            value=0.0,
            rationale=(
                "Prediction output is not a dictionary, "
                "so retrieved sources could not be evaluated."
            ),
        )

    if not isinstance(expectations, dict):
        return Feedback(
            value=0.0,
            rationale="No evaluation expectations were provided.",
        )

    required_sources = set(
        expectations.get(
            "required_sources",
            [],
        )
    )

    actual_sources = {
        source.get("source")
        for source in outputs.get(
            "sources",
            [],
        )
        if isinstance(source, dict) and source.get("source")
    }

    if not required_sources:
        return Feedback(
            value=1.0,
            rationale=(
                "No required sources were defined for this test case. "
                "Source recall is not applicable."
            ),
        )

    matched = required_sources.intersection(
        actual_sources,
    )

    score = len(matched) / len(required_sources)

    missing = required_sources - actual_sources

    return Feedback(
        value=score,
        rationale=(
            f"Matched sources: {sorted(matched)}. Missing sources: {sorted(missing)}."
        ),
    )


@scorer
def rag_quality_score(
    *,
    outputs: Any | None,
    expectations: dict[str, Any] | None,
) -> Feedback:

    if not isinstance(outputs, dict):
        return Feedback(
            value=0.0,
            rationale="Invalid RAG output.",
        )

    answer = str(outputs.get("answer", "")).strip()

    if not answer:
        return Feedback(
            value=0.0,
            rationale="The RAG system returned an empty answer.",
        )

    return Feedback(
        value=1.0,
        rationale=(
            "Response is present. Final correctness is evaluated "
            "separately by the LLM judge."
        ),
    )
