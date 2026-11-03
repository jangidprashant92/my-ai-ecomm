from evaluation.rag.retrieval_metrics import (
    calculate_retrieval_metrics,
)


def test_source_diversity_with_multiple_sources():
    documents = [
        {
            "source": "policies/refund_policy.md",
            "content": "Refund within 7 days",
        },
        {
            "source": "support/damaged_product_sop.md",
            "content": "Verify order ID",
        },
        {
            "source": "policies/return_policy.md",
            "content": "Return within 30 days",
        },
        {
            "source": "policies/refund_policy.md",
            "content": "Refund above threshold",
        },
    ]

    result = calculate_retrieval_metrics(documents)

    assert result["retrieved_count"] == 4
    assert result["unique_source_count"] == 3
    assert result["source_diversity"] == 0.75
    assert result["duplicate_chunk_ratio"] == 0.0


def test_duplicate_chunks():
    documents = [
        {
            "source": "policies/refund_policy.md",
            "content": "Refund within 7 days",
        },
        {
            "source": "policies/refund_policy.md",
            "content": "Refund within 7 days",
        },
    ]

    result = calculate_retrieval_metrics(documents)

    assert result["source_diversity"] == 0.5
    assert result["duplicate_chunk_ratio"] == 0.5


def test_empty_documents():
    result = calculate_retrieval_metrics([])

    assert result["retrieved_count"] == 0
    assert result["unique_source_count"] == 0
    assert result["source_diversity"] == 0.0
    assert result["duplicate_chunk_ratio"] == 0.0
