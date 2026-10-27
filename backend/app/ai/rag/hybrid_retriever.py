from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from functools import lru_cache

from app.ai.rag.loaders import KnowledgeBaseLoader
from app.ai.rag.splitters import DocumentSplitter
from app.ai.rag.vector_store import QdrantKnowledgeStore
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document


def document_key(document: Document) -> tuple[str, str]:
    """Identify a chunk consistently across lexical and dense retrieval."""
    return (
        str(document.metadata.get("source", "")),
        document.page_content,
    )


@lru_cache(maxsize=4)
def build_bm25_retriever(
    knowledge_base_path: str,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> BM25Retriever:
    """Build the lexical index once per process and configuration."""
    loader = KnowledgeBaseLoader(root_path=knowledge_base_path)
    source_documents = loader.load()

    if not source_documents:
        raise ValueError(
            f"No Markdown knowledge-base documents found at: {knowledge_base_path}"
        )

    chunks = DocumentSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    ).split(source_documents)

    if not chunks:
        raise ValueError("The knowledge base produced no chunks for BM25.")

    return BM25Retriever.from_documents(
        chunks,
        k=50,
    )


class HybridRetriever:
    """Combine BM25 and Qdrant rankings using reciprocal rank fusion."""

    def __init__(
        self,
        vector_store: QdrantKnowledgeStore,
        sparse_retriever: BM25Retriever,
        rrf_k: int = 60,
    ) -> None:
        if rrf_k <= 0:
            raise ValueError("rrf_k must be greater than zero.")

        self.vector_store = vector_store
        self.sparse_retriever = sparse_retriever
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        *,
        dense_k: int = 10,
        sparse_k: int = 10,
        score_threshold: float = 0.35,
        final_k: int = 10,
    ) -> list[tuple[Document, float]]:
        """Return unique documents ranked by combined reciprocal rank."""
        if not query.strip():
            return []

        dense_results = self.vector_store.similarity_search_with_threshold(
            query=query,
            k=dense_k,
            score_threshold=score_threshold,
        )

        self.sparse_retriever.k = sparse_k
        sparse_documents = self.sparse_retriever.invoke(query)[:sparse_k]

        documents_by_key: dict[tuple[str, str], Document] = {}
        fused_scores: defaultdict[tuple[str, str], float] = defaultdict(float)

        def add_ranked_results(
            documents: Sequence[Document],
        ) -> None:
            seen_in_list: set[tuple[str, str]] = set()
            rank = 0

            for document in documents:
                key = document_key(document)

                if key in seen_in_list:
                    continue

                seen_in_list.add(key)
                rank += 1
                documents_by_key.setdefault(key, document)
                fused_scores[key] += 1.0 / (self.rrf_k + rank)

        # Each retrieval method contributes according to its rank,
        # not its raw score. This avoids mixing incomparable score scales.
        add_ranked_results([document for document, _ in dense_results])
        add_ranked_results(sparse_documents)

        ranked_keys = sorted(
            fused_scores,
            key=lambda key: fused_scores[key],
            reverse=True,
        )

        return [
            (documents_by_key[key], fused_scores[key]) for key in ranked_keys[:final_k]
        ]
