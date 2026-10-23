from app.ai.rag.embeddings import EmbeddingProvider
from app.ai.rag.vector_store import QdrantKnowledgeStore
from app.core.config import settings


def main() -> None:
    print("Step 1: Testing embedding deployment...")

    embedding_provider = EmbeddingProvider()
    embeddings = embedding_provider.embeddings

    vector = embeddings.embed_query("Test embedding for CommerceOps AI retrieval.")

    print(f"Embedding request succeeded: {len(vector)} dimensions")

    if len(vector) != settings.EMBEDDING_DIMENSIONS:
        raise ValueError(
            "Embedding dimension mismatch: "
            f"configured={settings.EMBEDDING_DIMENSIONS}, "
            f"actual={len(vector)}"
        )

    print("Step 2: Testing Qdrant connection...")

    vector_store = QdrantKnowledgeStore(
        embeddings=embeddings,
    )

    vector_store.connect_existing()

    print(
        "Qdrant connection succeeded for collection:",
        settings.QDRANT_COLLECTION,
    )

    print("All RAG dependency checks passed.")


if __name__ == "__main__":
    main()
