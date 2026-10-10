from app.ai.rag import (
    EmbeddingProvider,
    QdrantKnowledgeStore,
)


def print_results(
    title: str,
    results,
) -> None:
    print("\n" + "=" * 70)
    print(title)

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


def main() -> None:
    embedding_provider = EmbeddingProvider()

    vector_store = QdrantKnowledgeStore(
        embeddings=embedding_provider.embeddings,
    )

    vector_store.connect_existing()

    queries = [
        "What is the refund policy for a damaged product?",
        "What evidence is required for a damaged product refund?",
        "What steps does support need to follow for a damaged product refund?",
        "When should a delayed shipment be escalated?",
    ]

    for query in queries:
        baseline = vector_store.similarity_search_with_threshold(
            query=query,
            k=6,
            score_threshold=0.35,
        )

        mmr = vector_store.mmr_search_with_threshold(
            query=query,
            k=6,
            fetch_k=12,
            lambda_mult=0.75,
            score_threshold=0.35,
        )

        print_results(
            f"BASELINE\nQuery: {query}",
            baseline,
        )

        print_results(
            f"MMR\nQuery: {query}",
            mmr,
        )


if __name__ == "__main__":
    main()
