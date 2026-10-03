from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

import asyncio
from collections.abc import Sequence
from typing import Any

from app.ai.llm.factory import LLMFactory
from app.ai.rag.embeddings import EmbeddingProvider
from app.ai.rag.query_rewriter import ContextualQueryRewriter
from app.ai.rag.service import RagService
from app.ai.rag.vector_store import QdrantKnowledgeStore
from langchain_core.messages import AIMessage, HumanMessage


def build_rag_service() -> RagService:
    model = LLMFactory.create()

    embedding_provider = EmbeddingProvider()

    vector_store = QdrantKnowledgeStore(
        embeddings=embedding_provider.embeddings,
    )

    vector_store.connect_existing()

    query_rewriter = ContextualQueryRewriter(
        model=model,
    )

    return RagService(
        vector_store=vector_store,
        model=model,
        query_rewriter=query_rewriter,
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


rag_service = build_rag_service()


def predict(
    question: str,
    history: Sequence[dict[str, str]] | None = None,
) -> dict[str, Any]:

    conversation_history = build_history(history)

    answer, documents = asyncio.run(
        rag_service.answer(
            query=question,
            history=conversation_history,
        )
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
