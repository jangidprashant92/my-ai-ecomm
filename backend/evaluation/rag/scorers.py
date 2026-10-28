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
            value="N/A",
            rationale=(
                "Prediction output is not a dictionary, "
                "so retrieved sources could not be evaluated."
            ),
        )

    if not isinstance(expectations, dict):
        return Feedback(
            value="N/A",
            rationale="No evaluation expectations were provided.",
        )

    raw_required_sources = expectations.get("required_sources", [])

    if not isinstance(raw_required_sources, list):
        return Feedback(
            value="N/A",
            rationale="Required sources must be provided as a list.",
        )

    required_sources = {
        source.strip()
        for source in raw_required_sources
        if isinstance(source, str) and source.strip()
    }

    if not required_sources:
        return Feedback(
            value="N/A",
            rationale=(
                "No required sources were defined for this test case. "
                "Source recall is not applicable."
            ),
        )

    raw_sources = outputs.get("sources", [])

    if not isinstance(raw_sources, list):
        return Feedback(
            value="N/A",
            rationale="Retrieved sources must be provided as a list.",
        )

    actual_sources = {
        source["source"].strip()
        for source in raw_sources
        if (
            isinstance(source, dict)
            and isinstance(source.get("source"), str)
            and source["source"].strip()
        )
    }

    matched = required_sources.intersection(actual_sources)
    missing = required_sources - actual_sources

    score = len(matched) / len(required_sources)

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


@scorer
def abstention_quality(
    *,
    outputs: Any | None,
    expectations: dict[str, Any] | None,
) -> Feedback:

    if not isinstance(outputs, dict):
        return Feedback(
            value="FAIL",
            rationale="Prediction output is not a dictionary.",
        )

    if not isinstance(expectations, dict):
        return Feedback(
            value="FAIL",
            rationale="No evaluation expectations were provided.",
        )

    expected_facts = expectations.get(
        "expected_facts",
        [],
    )

    required_sources = expectations.get(
        "required_sources",
        [],
    )

    # This scorer is only meaningful for negative / unanswerable cases.
    if expected_facts or required_sources:
        return Feedback(
            value="N/A",
            rationale=(
                "This is an answerable test case. Abstention quality is not applicable."
            ),
        )

    sources = outputs.get(
        "sources",
        [],
    )

    answer = (
        str(
            outputs.get(
                "answer",
                "",
            )
        )
        .strip()
        .lower()
    )

    abstention_phrases = (
        "could not find relevant information",
        "does not contain enough information",
        "not available in the knowledge base",
        "not found in the knowledge base",
        "knowledge base does not contain",
    )

    correctly_abstained = any(phrase in answer for phrase in abstention_phrases)

    no_sources_retrieved = not sources

    if no_sources_retrieved and correctly_abstained:
        return Feedback(
            value="PASS",
            rationale=(
                "No documents were retrieved and the assistant correctly "
                "stated that the knowledge base does not contain enough information."
            ),
        )

    if sources and correctly_abstained:
        return Feedback(
            value="FAIL",
            rationale=(
                "The assistant correctly abstained, but the retriever returned "
                "documents for an unanswerable question. Retrieval abstention failed."
            ),
        )

    return Feedback(
        value="FAIL",
        rationale=(
            "The test case is unanswerable, but the assistant did not "
            "correctly abstain."
        ),
    )


@scorer
def source_precision(
    *,
    outputs: Any | None,
    expectations: dict[str, Any] | None,
) -> Feedback:
    """Measure how many retrieved source documents are relevant."""

    if not isinstance(outputs, dict):
        return Feedback(
            value=0.0,
            rationale="Prediction output is not a dictionary.",
        )

    if not isinstance(expectations, dict):
        return Feedback(
            value="N/A",
            rationale="No evaluation expectations were provided.",
        )

    # Prefer the complete set of relevant sources.
    # Fall back to required_sources for older dataset entries.
    source_list = expectations.get("relevant_sources")

    if source_list is None:
        source_list = expectations.get("required_sources", [])

    if not isinstance(source_list, list):
        return Feedback(
            value="N/A",
            rationale="Relevant sources must be provided as a list.",
        )

    raw_sources = outputs.get("sources", [])

    if not isinstance(raw_sources, list):
        return Feedback(
            value="N/A",
            rationale="Retrieved sources must be provided as a list.",
        )

    relevant_sources = {
        str(source)
        for source in source_list
        if isinstance(source, str) and source.strip()
    }

    actual_sources = {
        str(source["source"])
        for source in outputs.get("sources", [])
        if isinstance(source, dict)
        and isinstance(source.get("source"), str)
        and source["source"].strip()
    }

    # A source precision score is not meaningful without
    # an annotated set of relevant sources.
    if not relevant_sources:
        return Feedback(
            value="N/A",
            rationale=(
                "No relevant or required sources were defined. "
                "Source precision is not applicable."
            ),
        )

    if not actual_sources:
        return Feedback(
            value=0.0,
            rationale=(
                "Relevant sources were defined, but no documents were retrieved."
            ),
        )

    matched = relevant_sources.intersection(actual_sources)
    extra_sources = actual_sources - relevant_sources

    precision = len(matched) / len(actual_sources)

    return Feedback(
        value=precision,
        rationale=(
            f"Matched relevant sources: {sorted(matched)}. "
            f"Retrieved sources not annotated as relevant: "
            f"{sorted(extra_sources)}. "
            f"Relevant sources not retrieved: "
            f"{sorted(relevant_sources - actual_sources)}."
        ),
    )
