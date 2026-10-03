from __future__ import annotations

from collections.abc import Sequence

from app.core.config import settings
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient


class QdrantKnowledgeStore:
    """Qdrant vector store for the CommerceOps knowledge base."""

    def __init__(
        self,
        embeddings: Embeddings,
        collection_name: str | None = None,
    ) -> None:
        self.embeddings = embeddings
        self.collection_name = collection_name or settings.QDRANT_COLLECTION
        self.vector_store: QdrantVectorStore | None = None

        self.client = QdrantClient(
            url=settings.QDRANT_URL,
        )

    def recreate_from_documents(
        self,
        documents: Sequence[Document],
    ) -> None:
        """Delete the existing collection and recreate it from documents."""

        if self.client.collection_exists(collection_name=self.collection_name):
            self.client.delete_collection(collection_name=self.collection_name)

        self.vector_store = QdrantVectorStore.from_documents(
            documents=list(documents),
            embedding=self.embeddings,
            url=settings.QDRANT_URL,
            collection_name=self.collection_name,
        )

    def connect_existing(self) -> None:
        """Connect to an already-created Qdrant collection."""

        self.vector_store = QdrantVectorStore.from_existing_collection(
            embedding=self.embeddings,
            collection_name=self.collection_name,
            url=settings.QDRANT_URL,
        )

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
    ):
        """Search the existing knowledge base."""

        if self.vector_store is None:
            raise RuntimeError(
                "Qdrant vector store is not initialized. Call connect_existing() first."
            )

        return self.vector_store.similarity_search_with_score(
            query,
            k=k,
        )

    def similarity_search_with_threshold(
        self,
        query: str,
        k: int = 5,
        score_threshold: float = 0.35,
    ):
        return self.search_with_threshold(
            query=query,
            k=k,
            score_threshold=score_threshold,
        )

    def search_with_threshold(
        self,
        query: str,
        k: int = 5,
        score_threshold: float = 0.35,
    ):
        if self.vector_store is None:
            raise RuntimeError(
                "Qdrant vector store is not initialized. Call connect_existing() first."
            )

        results = self.vector_store.similarity_search_with_score(
            query,
            k=k,
        )

        filtered = [
            (document, float(score))
            for document, score in results
            if float(score) >= score_threshold
        ]

        # ---------------------------------------------
        # Preserve the existing application contract.
        #
        # RagService expects:
        # [(Document, score), ...]
        # ---------------------------------------------

        return filtered
