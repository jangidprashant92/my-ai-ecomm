from unittest.mock import Mock

from app.ai.rag.hybrid_retriever import HybridRetriever
from langchain_core.documents import Document


def test_rrf_ranks_a_document_found_by_both_retrievers_first():
    shared = Document(
        page_content="Refunds for damaged products are allowed.",
        metadata={"source": "policies/refund.md"},
    )
    dense_only = Document(
        page_content="Damaged products must be reported.",
        metadata={"source": "policies/damaged.md"},
    )
    sparse_only = Document(
        page_content="Refund requests require proof of purchase.",
        metadata={"source": "policies/proof.md"},
    )

    vector_store = Mock()
    vector_store.similarity_search_with_threshold.return_value = [
        (shared, 0.91),
        (dense_only, 0.82),
    ]

    sparse_retriever = Mock()
    sparse_retriever.invoke.return_value = [
        shared,
        sparse_only,
    ]

    retriever = HybridRetriever(
        vector_store=vector_store,
        sparse_retriever=sparse_retriever,
    )

    results = retriever.retrieve(
        "refund for damaged product",
        dense_k=10,
        sparse_k=10,
        final_k=10,
    )

    assert results[0][0].page_content == shared.page_content
    assert len(results) == 3
    assert results[0][1] > results[1][1]
    assert results[0][1] > results[2][1]


def test_hybrid_retrieval_deduplicates_same_source_and_content():
    document = Document(
        page_content="Refunds are available within 7 days.",
        metadata={"source": "policies/refund.md"},
    )

    vector_store = Mock()
    vector_store.similarity_search_with_threshold.return_value = [
        (document, 0.90),
    ]

    sparse_retriever = Mock()
    sparse_retriever.invoke.return_value = [document]

    retriever = HybridRetriever(
        vector_store=vector_store,
        sparse_retriever=sparse_retriever,
    )

    results = retriever.retrieve("refund policy")

    assert len(results) == 1


def test_empty_query_returns_no_documents():
    vector_store = Mock()
    sparse_retriever = Mock()

    retriever = HybridRetriever(
        vector_store=vector_store,
        sparse_retriever=sparse_retriever,
    )

    assert retriever.retrieve("   ") == []
    vector_store.similarity_search_with_threshold.assert_not_called()
    sparse_retriever.invoke.assert_not_called()
