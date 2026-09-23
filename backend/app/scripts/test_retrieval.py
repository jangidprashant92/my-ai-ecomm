from app.ai.rag import (
    EmbeddingProvider,
    QdrantKnowledgeStore,
)


def main() -> None:
    embedding_provider = EmbeddingProvider()

    vector_store = QdrantKnowledgeStore(
        embeddings=embedding_provider.embeddings,
    )

    vector_store.connect_existing()

    query = "What is the refund policy for a damaged product?"

    results = vector_store.similarity_search_with_score(
        query=query,
        k=4,
    )

    print(f"\nQuery: {query}\n")

    for index, (document, score) in enumerate(
        results,
        start=1,
    ):
        print(f"\n--- Result {index} ---")
        print(f"Score: {score:.4f}")

        print(
            "Source:",
            document.metadata.get("source"),
        )

        print("\nContent:")
        print(document.page_content)


if __name__ == "__main__":
    main()
