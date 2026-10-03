from __future__ import annotations

from collections.abc import Sequence

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

RERANK_SYSTEM_PROMPT = """
You are a document reranker for a CommerceOps knowledge base.

Your job is to rank candidate documents for the user's query.

Rank documents based on whether they contain information that is
directly useful for answering the query.

Important rules:

1. Judge semantic relevance, not just keyword overlap.
2. A document is relevant only if it helps answer the specific question.
3. A document about a related policy is not relevant unless it contributes
   directly to the requested answer.
4. Penalize documents that only share words with the query.
5. For questions about a specific subtype, prefer documents about that subtype.
6. For unanswerable questions, unrelated documents should receive very low scores.
7. Return every candidate index exactly once.
8. Scores must be between 0 and 1.

Scoring:

1.0 = directly answers the query
0.8 = strongly relevant
0.6 = partially relevant
0.3 = weakly related
0.0 = irrelevant
"""


class RankedDocument(BaseModel):
    index: int = Field(description="Zero-based candidate document index.")

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

    def rerank(
        self,
        query: str,
        documents: Sequence,
    ) -> list[tuple[int, float]]:

        if not documents:
            return []

        candidates = "\n\n".join(
            (
                f"DOCUMENT {index}\n"
                f"Source: {document.metadata.get('source', '')}\n"
                f"{document.content}"
            )
            for index, document in enumerate(documents)
        )

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

        rankings = {
            item.index: item.score
            for item in response.results  # type: ignore
            if 0 <= item.index < len(documents)
        }

        ranked = [
            (
                index,
                rankings.get(index, 0.0),
            )
            for index in range(len(documents))
        ]

        return sorted(
            ranked,
            key=lambda item: item[1],
            reverse=True,
        )

    async def arerank(
        self,
        query: str,
        documents: Sequence,
    ) -> list[tuple[int, float]]:

        if not documents:
            return []

        candidates = "\n\n".join(
            (
                f"DOCUMENT {index}\n"
                f"Source: {document.metadata.get('source', '')}\n"
                f"{document.content}"
            )
            for index, document in enumerate(documents)
        )

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
            ]
        )

        rankings = {
            item.index: item.score
            for item in response.results  # type: ignore
            if 0 <= item.index < len(documents)
        }

        ranked = [
            (
                index,
                rankings.get(index, 0.0),
            )
            for index in range(len(documents))
        ]

        return sorted(
            ranked,
            key=lambda item: item[1],
            reverse=True,
        )
