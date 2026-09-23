import asyncio

from app.ai.llm.factory import LLMFactory
from app.ai.rag import (
    EmbeddingProvider,
    QdrantKnowledgeStore,
    RagService,
)


async def main() -> None:
    embedding_provider = EmbeddingProvider()

    vector_store = QdrantKnowledgeStore(
        embeddings=embedding_provider.embeddings,
    )

    vector_store.connect_existing()

    model = LLMFactory.create()

    rag_service = RagService(
        vector_store=vector_store,
        model=model,
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
            k=4,
        )

        print("\nAnswer:")
        print(answer)

        print("\nSources:")

        for document in documents:
            source = document.metadata.get("source", "unknown")

            print(f"- {source}")


if __name__ == "__main__":
    asyncio.run(main())
