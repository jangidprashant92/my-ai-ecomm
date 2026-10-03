from __future__ import annotations

from collections.abc import Sequence

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

RERANK_SYSTEM_PROMPT = """
You are a document reranker for a CommerceOps knowledge base.

Your job is to select the candidate documents that are directly
useful for answering the user's SPECIFIC question.

Important rules:

1. Judge semantic relevance, not just keyword overlap.

2. Select a document only when it materially helps answer the
   user's specific question.

3. A document about a related policy is not relevant unless it
   directly contributes to answering the question.

4. Pay attention to scope-changing qualifiers such as:
   - international
   - domestic
   - damaged
   - cancelled
   - delayed
   - subscription
   - premium
   - enterprise

5. A generic qualifier such as "standard", "general", "normal",
   or "basic" does not require an exact textual match when the
   document is clearly the canonical policy describing the
   normal or baseline behavior.

6. Do not infer a special policy from a generic policy.

   Example:
   A general shipping policy is NOT relevant to a question about
   international shipping unless the document explicitly discusses
   international shipping.

7. A canonical policy document is relevant when it directly
   describes the normal conditions of the policy being asked about,
   even if words such as "standard" or "general" do not appear
   verbatim.

8. Include every candidate that materially contributes to answering
   the question.

9. Do not include documents that are merely related by topic.

10. If no candidate directly helps answer the question, return [].

11. Prefer the smallest set of documents that is sufficient to answer
    the user's question.

12. Do not include multiple documents that provide the same fact unless
    the additional document contains materially different information
    required to answer the question.

13. If one document completely answers a question, do not select another
    document merely because it discusses the same topic.

14. For comparison questions, select the documents representing each
    policy or concept being compared, but do not include duplicate
    supporting documents unless they add unique information.

15. Relevance means both:
    - the document is related to the question, and
    - the document adds useful information to the final answer.

16. Use the smallest sufficient evidence set.

    Example:
    If the Refund Policy completely answers:
    "What is the refund policy for a damaged product?"

    and the Damaged Product Support SOP only repeats
    information already contained in the Refund Policy,
    return only the Refund Policy document.

    Do not select the SOP unless the user's question
    specifically asks for support procedures or checks.

17. Select multiple documents only when the user's question
    requires materially different facts from those documents.

    Example:
    "For a damaged product refund, what is the customer's
    eligibility rule and what support checks are required?"

    This requires both the Refund Policy and the Damaged Product SOP.

Return the relevant document indices ordered from most relevant
to least relevant.

Examples:

Question:
"What are the standard return conditions?"

Candidates:
0 = Return Policy
1 = Refund Policy
2 = Cancellation Policy

Return:
[0]

Question:
"What is the international shipping policy?"

Candidates:
0 = General Shipping Policy
1 = Return Policy
2 = Refund Policy

Return:
[]

Question:
"What is the refund policy for a damaged product?"

Candidates:
0 = Refund Policy
1 = Damaged Product Support SOP
2 = Return Policy
3 = Cancellation Policy

Return:
[0]
"""


class RerankResponse(BaseModel):
    relevant_indices: list[int] = Field(
        description=(
            "Zero-based indices of documents that are directly relevant "
            "to the user's question, ordered from most relevant to least relevant. "
            "Return an empty list when no candidate is relevant."
        )
    )


class LLMDocumentReRanker:
    """LLM-based document reranker."""

    def __init__(
        self,
        model: BaseChatModel,
    ) -> None:
        self.model = model.with_structured_output(
            RerankResponse,
            method="json_schema",
            strict=True,
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
    def _normalize_indices(
        response: RerankResponse,
        document_count: int,
    ) -> list[int]:

        seen: set[int] = set()
        normalized: list[int] = []

        for index in response.relevant_indices:
            if not 0 <= index < document_count:
                continue

            if index in seen:
                continue

            seen.add(index)
            normalized.append(index)

        return normalized

    def rerank(
        self,
        query: str,
        documents: Sequence,
    ) -> list[int]:

        if not documents:
            return []

        candidates = self._build_candidates(
            documents,
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

        return self._normalize_indices(
            response=response,
            document_count=len(documents),
        )

    async def arerank(
        self,
        query: str,
        documents: Sequence,
    ) -> list[int]:

        if not documents:
            return []

        candidates = self._build_candidates(
            documents,
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
            ],
        )

        return self._normalize_indices(
            response=response,
            document_count=len(documents),
        )
