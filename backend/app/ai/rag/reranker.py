from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

RERANK_SYSTEM_PROMPT = """
You are a document reranker for a CommerceOps knowledge base.

Your job is to determine which candidate documents are relevant
to the user's SPECIFIC question.

Important rules:

1. Judge semantic relevance, not just keyword overlap.

2. A document is relevant only if it directly helps answer the
   user's specific question.

3. A document about a related policy is NOT relevant unless it
   directly contributes to answering the question.

4. When the question contains a specific qualifier such as:
   - international
   - damaged
   - standard
   - cancelled
   - delayed
   - refund
   - return

   the document must explicitly cover that qualifier to be
   considered relevant.

5. Do not infer missing policy scope.

   Example:
   A general shipping policy is NOT sufficient for a question
   about international shipping unless the document explicitly
   discusses international shipping.

6. For unanswerable questions, unrelated documents should be
   classified as irrelevant.

7. Every candidate document must appear exactly once in the result.

8. Scores must be between 0 and 1.

Scoring:

1.0 = directly answers the question
0.8 = strongly relevant
0.6 = partially relevant
0.3 = weakly related
0.0 = irrelevant
"""


class RankedDocument(BaseModel):
    index: int = Field(description="Zero-based candidate document index.")

    relevance: Literal[
        "relevant",
        "irrelevant",
    ] = Field(
        description=(
            "Whether the document directly helps answer the user's specific question."
        )
    )

    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Semantic relevance score between 0 and 1.",
    )


class RerankResponse(BaseModel):
    results: list[RankedDocument]


class LLMDocumentReRanker:
    """LLM-based document reranker."""

    def __init__(
        self,
        model: BaseChatModel,
    ) -> None:
        self.model = model.with_structured_output(
            RerankResponse,
        )

    def _build_candidates(
        self,
        documents: Sequence,
    ) -> str:
        return "\n\n".join(
            (
                f"DOCUMENT {index}\n"
                f"Source: {document.metadata.get('source', '')}\n"
                f"{document.content}"
            )
            for index, document in enumerate(documents)
        )

    @staticmethod
    def _normalize_rankings(
        response: RerankResponse,
        document_count: int,
    ) -> list[tuple[int, str, float]]:
        """
        Convert the structured LLM response into:

            (index, relevance, score)

        Every candidate is guaranteed to appear exactly once.
        Missing candidates are treated as irrelevant with score 0.
        """

        rankings: dict[int, tuple[str, float]] = {}

        for item in response.results:
            if not 0 <= item.index < document_count:
                continue

            # Guard against duplicate indexes from the model.
            if item.index in rankings:
                continue

            rankings[item.index] = (
                item.relevance,
                float(item.score),
            )

        normalized: list[tuple[int, str, float]] = []

        for index in range(document_count):
            relevance, score = rankings.get(
                index,
                ("irrelevant", 0.0),
            )

            normalized.append(
                (
                    index,
                    relevance,
                    score,
                )
            )

        # Highest relevance score first.
        normalized.sort(
            key=lambda item: item[2],
            reverse=True,
        )

        return normalized

    def rerank(
        self,
        query: str,
        documents: Sequence,
    ) -> list[tuple[int, str, float]]:
        """Synchronous reranking."""

        if not documents:
            return []

        candidates = self._build_candidates(documents)

        response = self.model.invoke(
            [
                SystemMessage(
                    content=RERANK_SYSTEM_PROMPT,
                ),
                HumanMessage(
                    content=(
                        f"User Query:\n{query}\n\nCandidate Documents:\n{candidates}"
                    ),
                ),
            ],
        )

        return self._normalize_rankings(
            response=response,
            document_count=len(documents),
        )

    async def arerank(
        self,
        query: str,
        documents: Sequence,
    ) -> list[tuple[int, str, float]]:
        """Asynchronous reranking."""

        if not documents:
            return []

        candidates = self._build_candidates(documents)

        response = await self.model.ainvoke(
            [
                SystemMessage(
                    content=RERANK_SYSTEM_PROMPT,
                ),
                HumanMessage(
                    content=(
                        f"User Query:\n{query}\n\nCandidate Documents:\n{candidates}"
                    ),
                ),
            ],
        )

        return self._normalize_rankings(
            response=response,
            document_count=len(documents),
        )
