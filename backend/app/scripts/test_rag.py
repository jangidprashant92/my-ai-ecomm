import asyncio

from app.ai.llm.factory import LLMFactory
from app.ai.rag import (
    EmbeddingProvider,
    QdrantKnowledgeStore,
    RagService,
)
from app.ai.rag.config import RagConfig
from app.ai.rag.query_rewriter import ContextualQueryRewriter
from app.core.config import settings


async def main() -> None:
    embedding_provider = EmbeddingProvider()

    vector_store = QdrantKnowledgeStore(
        embeddings=embedding_provider.embeddings,
    )

    vector_store.connect_existing()

    model = LLMFactory.create()

    query_rewriter = ContextualQueryRewriter(
        model=model,
    )

    rag_config = RagConfig(
        mmr_enabled=settings.RAG_USE_MMR,
        mmr_fetch_k=settings.RAG_MMR_FETCH_K,
        mmr_lambda_mult=settings.RAG_MMR_LAMBDA_MULT,
    )

    rag_service = RagService(
        vector_store=vector_store,
        model=model,
        query_rewriter=query_rewriter,
        config=rag_config,
    )

    questions = [
        "What is the refund policy for a damaged product?",
        "How many days do I have to return an eligible product?",
        "When should a delayed shipment be escalated?",
        "Do refunds above BRL 500 require approval?",
    ]

    for question in questions:
        print("\n" + "=" * 60)
        print(f"Question: {question}")

        answer, documents = await rag_service.answer(
            query=question,
        )

        print("\nAnswer:")
        print(answer)

        print("\nSources:")

        for document in documents:
            source = document.metadata.get("source", "unknown")

            print(f"- {source}")


if __name__ == "__main__":
    asyncio.run(main())
