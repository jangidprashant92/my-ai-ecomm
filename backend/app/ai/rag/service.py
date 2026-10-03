import logging
from collections.abc import Sequence
from dataclasses import dataclass

import mlflow
from app.ai.rag.config import RagConfig
from app.ai.rag.query_rewriter import ContextualQueryRewriter
from app.ai.rag.reranker import LLMDocumentReRanker
from app.ai.rag.vector_store import QdrantKnowledgeStore
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from mlflow.entities import SpanType

logger = logging.getLogger(__name__)

RAG_SYSTEM_PROMPT = """
You are CommerceOps AI.

Answer the user's question using only the provided
CommerceOps knowledge-base context.

Rules:

1. Do not invent information.
2. Do not use knowledge outside the provided context.
3. Do not add procedures, actions, guarantees, or explanations
   that are not explicitly supported by the context.
4. If the context does not contain the answer, say that the
   knowledge base does not contain enough information.
5. Never attribute CommerceOps policies to another company,
   brand, organization, or website.
6. If the user asks about an external organization and the
   context does not explicitly describe that organization,
   say that the information is not available in the knowledge base.
7. Do not claim that a business action was performed.
8. Answer only the user's specific question.
9. Do not include related policies unless they are necessary
   to answer the question.
10. If multiple policies are present in the context, use only
    the policy relevant to the user's question.
11. Do not compare different policy types unless the user
    explicitly asks for a comparison.

Return a concise, directly supported answer.
"""


@dataclass(slots=True)
class RetrievedDocument:
    """Retrieved document with its similarity score."""

    content: str
    metadata: dict
    score: float


class RagService:
    """Standalone retrieval-augmented generation service."""

    def __init__(
        self,
        vector_store: QdrantKnowledgeStore,
        model: BaseChatModel,
        query_rewriter: ContextualQueryRewriter,
        config: RagConfig | None = None,
    ) -> None:
        self.vector_store = vector_store
        self.model = model
        self.config = config or RagConfig()
        self.query_rewriter = query_rewriter
        self.reranker = LLMDocumentReRanker(
            model=model,
        )

    async def answer(
        self,
        query: str,
        history: Sequence[BaseMessage] | None = None,
    ) -> tuple[str, list[RetrievedDocument]]:
        history = history or []

        retrieval_query = await self.query_rewriter.rewrite(
            query=query,
            history=history,
        )

        retrieval_queries = [
            retrieval_query,
            query,
        ]

        logger.info(
            "RAG queries | original=%r | rewritten=%r",
            query,
            retrieval_query,
        )

        documents = await self.aretrieve_documents(
            queries=retrieval_queries,
            rerank_query=retrieval_query,
        )

        if not documents:
            return (
                "I could not find relevant information in the knowledge base.",
                [],
            )

        context = "\n\n---\n\n".join(
            (f"Source: {doc.metadata.get('source')}\n{doc.content}")
            for doc in documents
        )

        response = await self.model.ainvoke(
            [
                SystemMessage(
                    content=RAG_SYSTEM_PROMPT,
                ),
                HumanMessage(
                    content=(
                        f"Question:\n{query}\n\nKnowledge Base Context:\n{context}"
                    ),
                ),
            ],
        )

        return (
            str(response.content),
            documents,
        )

    def answer_sync(
        self,
        query: str,
        history: Sequence[BaseMessage] | None = None,
    ) -> tuple[str, list[RetrievedDocument]]:

        history = history or []

        retrieval_query = self.query_rewriter.rewrite_sync(
            query=query,
            history=history,
        )

        retrieval_queries = [
            retrieval_query,
            query,
        ]

        logger.info(
            "RAG evaluation queries | original=%r | rewritten=%r",
            query,
            retrieval_query,
        )

        documents = self.retrieve_documents(
            queries=retrieval_queries,
            rerank_query=retrieval_query,
        )

        if not documents:
            return (
                "I could not find relevant information in the knowledge base.",
                [],
            )

        context = "\n\n---\n\n".join(
            (f"Source: {doc.metadata.get('source')}\n{doc.content}")
            for doc in documents
        )

        response = self.model.invoke(
            [
                SystemMessage(
                    content=RAG_SYSTEM_PROMPT,
                ),
                HumanMessage(
                    content=(
                        f"Question:\n{query}\n\nKnowledge Base Context:\n{context}"
                    ),
                ),
            ],
        )

        return (
            str(response.content),
            documents,
        )

    def retrieve_candidates(
        self,
        queries: Sequence[str],
    ) -> list[RetrievedDocument]:

        unique_queries: list[str] = []

        for query in queries:
            normalized = query.strip()

            if normalized and normalized not in unique_queries:
                unique_queries.append(normalized)

        retrieved: dict[tuple[str, str], RetrievedDocument] = {}

        for query in unique_queries:
            results = self.vector_store.similarity_search_with_threshold(
                query=query,
                k=self.config.candidate_top_k,
                score_threshold=self.config.score_threshold,
            )

            for document, score in results:
                source = str(
                    document.metadata.get(
                        "source",
                        "",
                    )
                )

                content = document.page_content

                key = (
                    source,
                    content,
                )

                retrieved_document = RetrievedDocument(
                    content=content,
                    metadata=document.metadata,
                    score=float(score),
                )

                existing = retrieved.get(key)

                if existing is None or retrieved_document.score > existing.score:
                    retrieved[key] = retrieved_document

        documents = sorted(
            retrieved.values(),
            key=lambda document: document.score,
            reverse=True,
        )

        return documents[: self.config.max_rerank_documents]

    def rerank_documents(
        self,
        query: str,
        documents: Sequence[RetrievedDocument],
    ) -> list[RetrievedDocument]:

        ranked_indices = self.reranker.rerank(
            query=query,
            documents=documents,
        )

        reranked_documents: list[RetrievedDocument] = []

        for rank, index in enumerate(ranked_indices):
            document = documents[index]

            reranked_documents.append(
                RetrievedDocument(
                    content=document.content,
                    metadata={
                        **document.metadata,
                        "vector_score": document.score,
                        "rerank_rank": rank + 1,
                    },
                    score=document.score,
                )
            )

            if len(reranked_documents) >= self.config.max_context_documents:
                break

        return reranked_documents

    async def arerank_documents(
        self,
        query: str,
        documents: Sequence[RetrievedDocument],
    ) -> list[RetrievedDocument]:

        ranked_indices = await self.reranker.arerank(
            query=query,
            documents=documents,
        )

        reranked_documents: list[RetrievedDocument] = []

        for rank, index in enumerate(ranked_indices):
            document = documents[index]

            reranked_documents.append(
                RetrievedDocument(
                    content=document.content,
                    metadata={
                        **document.metadata,
                        "vector_score": document.score,
                        "rerank_rank": rank + 1,
                    },
                    score=document.score,
                )
            )

            if len(reranked_documents) >= self.config.max_context_documents:
                break

        return reranked_documents

    @mlflow.trace(
        name="rag_retrieval",
        span_type=SpanType.RETRIEVER,
    )
    def retrieve_documents(
        self,
        *,
        queries: Sequence[str],
        rerank_query: str,
    ) -> list[RetrievedDocument]:

        candidate_documents = RagService.retrieve_candidates(
            self,
            queries=queries,
        )

        documents = RagService.rerank_documents(
            self,
            query=rerank_query,
            documents=candidate_documents,
        )

        span = mlflow.get_current_active_span()

        if span is not None:
            span.set_outputs(
                [
                    {
                        "page_content": document.content,
                        "metadata": {
                            "doc_uri": document.metadata.get("source"),
                            "document_id": document.metadata.get("document_id"),
                            "document_type": document.metadata.get("document_type"),
                            "category": document.metadata.get("category"),
                            "vector_score": document.metadata.get("vector_score"),
                            "rerank_rank": document.metadata.get("rerank_rank"),
                        },
                    }
                    for document in documents
                ]
            )

        return documents

    @mlflow.trace(
        name="rag_retrieval",
        span_type=SpanType.RETRIEVER,
    )
    async def aretrieve_documents(
        self,
        *,
        queries: Sequence[str],
        rerank_query: str,
    ) -> list[RetrievedDocument]:

        candidate_documents = RagService.retrieve_candidates(
            self,
            queries=queries,
        )

        documents = await RagService.arerank_documents(
            self,
            query=rerank_query,
            documents=candidate_documents,
        )

        span = mlflow.get_current_active_span()

        if span is not None:
            span.set_outputs(
                [
                    {
                        "page_content": document.content,
                        "metadata": {
                            "doc_uri": document.metadata.get("source"),
                            "document_id": document.metadata.get("document_id"),
                            "document_type": document.metadata.get("document_type"),
                            "category": document.metadata.get("category"),
                            "vector_score": document.metadata.get("vector_score"),
                            "rerank_rank": document.metadata.get("rerank_rank"),
                        },
                    }
                    for document in documents
                ]
            )

        return documents
