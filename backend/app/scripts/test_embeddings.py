from app.ai.rag import EmbeddingProvider
from app.core.config import settings


def main() -> None:
    embedding_provider = EmbeddingProvider()

    query = "What is the refund policy for a damaged product?"

    vector = embedding_provider.embeddings.embed_query(query)

    print("\nEmbedding test")
    print(f"Model: {settings.EMBEDDING_MODEL}")
    print(f"Expected dimensions: {settings.EMBEDDING_DIMENSIONS}")
    print(f"Actual dimensions: {len(vector)}")

    if len(vector) != settings.EMBEDDING_DIMENSIONS:
        raise ValueError(
            "Embedding dimension mismatch: "
            f"expected {settings.EMBEDDING_DIMENSIONS}, "
            f"got {len(vector)}"
        )

    print("Embedding test passed.")


if __name__ == "__main__":
    main()
