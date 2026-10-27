from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import mlflow
from app.ai.llm.factory import LLMFactory
from app.ai.rag.config import RagConfig
from app.ai.rag.embeddings import EmbeddingProvider
from app.ai.rag.hybrid_retriever import (
    HybridRetriever,
    build_bm25_retriever,
)
from app.ai.rag.query_rewriter import ContextualQueryRewriter
from app.ai.rag.service import RagService
from app.ai.rag.vector_store import QdrantKnowledgeStore
from app.core.config import settings
from langchain_core.messages import AIMessage, HumanMessage


def build_rag_service() -> RagService:
    model = LLMFactory.create()
    embedding_provider = EmbeddingProvider()

    vector_store = QdrantKnowledgeStore(
        embeddings=embedding_provider.embeddings,
    )
    vector_store.connect_existing()

    query_rewriter = ContextualQueryRewriter(model=model)

    retrieval_type = settings.RAG_RETRIEVAL_TYPE.strip().lower()
    hybrid_retriever = None

    if retrieval_type == "hybrid":
        knowledge_base_path = settings.KNOWLEDGE_BASE_PATH.strip()

        if not knowledge_base_path:
            raise ValueError(
                "KNOWLEDGE_BASE_PATH must be configured when RAG_RETRIEVAL_TYPE=hybrid."
            )

        sparse_retriever = build_bm25_retriever(
            knowledge_base_path=knowledge_base_path,
        )

        hybrid_retriever = HybridRetriever(
            vector_store=vector_store,
            sparse_retriever=sparse_retriever,
            rrf_k=settings.RAG_HYBRID_RRF_K,
        )

    rag_config = RagConfig(
        retrieval_type=retrieval_type,
        mmr_enabled=settings.RAG_USE_MMR,
        mmr_fetch_k=settings.RAG_MMR_FETCH_K,
        mmr_lambda_mult=settings.RAG_MMR_LAMBDA_MULT,
        hybrid_rrf_k=settings.RAG_HYBRID_RRF_K,
    )

    return RagService(
        vector_store=vector_store,
        model=model,
        query_rewriter=query_rewriter,
        config=rag_config,
        hybrid_retriever=hybrid_retriever,
    )


def build_history(
    history: Sequence[dict[str, str]] | None,
) -> list[HumanMessage | AIMessage]:

    if not history:
        return []

    messages: list[HumanMessage | AIMessage] = []

    for message in history:
        role = message.get("role")
        content = message.get("content", "")

        if role == "user":
            messages.append(
                HumanMessage(
                    content=content,
                )
            )

        elif role == "assistant":
            messages.append(
                AIMessage(
                    content=content,
                )
            )

    return messages


@mlflow.trace(name="rag_evaluation")
def predict(
    question: str,
    history: Sequence[dict[str, str]] | None = None,
) -> dict[str, Any]:

    rag_service = build_rag_service()

    conversation_history = build_history(history)

    answer, documents = rag_service.answer_sync(
        query=question,
        history=conversation_history,
    )

    sources = [
        {
            "source": document.metadata.get("source"),
            "document_id": document.metadata.get("document_id"),
            "score": document.score,
        }
        for document in documents
    ]

    context = [
        {
            "source": document.metadata.get("source"),
            "content": document.content,
        }
        for document in documents
    ]

    return {
        "answer": answer,
        "sources": sources,
        "context": context,
    }
