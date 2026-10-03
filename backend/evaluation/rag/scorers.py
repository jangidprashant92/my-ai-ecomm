from __future__ import annotations

from typing import Any, Literal

from mlflow.genai import scorer
from mlflow.genai.judges import make_judge

EVAL_JUDGE_MODEL = "openai:/gpt-4.1-mini"


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
    model=EVAL_JUDGE_MODEL,
    feedback_value_type=Literal[
        "PASS",
        "PARTIAL",
        "FAIL",
    ],
)


@scorer
def source_recall(
    outputs: dict[str, Any],
    expectations: dict[str, Any],
) -> float:

    expected_sources = set(
        expectations.get(
            "expected_sources",
            [],
        )
    )

    actual_sources = {
        source.get("source")
        for source in outputs.get(
            "sources",
            [],
        )
        if source.get("source")
    }

    # No source is expected.
    if not expected_sources:
        return 1.0 if not actual_sources else 0.0

    matched = expected_sources.intersection(
        actual_sources,
    )

    return len(matched) / len(expected_sources)
