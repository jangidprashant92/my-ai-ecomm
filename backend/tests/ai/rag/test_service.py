from unittest.mock import Mock

from app.ai.rag.config import RagConfig
from app.ai.rag.service import RagService
from langchain_core.documents import Document


def make_service(mmr_enabled: bool) -> tuple[RagService, Mock]:
    vector_store = Mock()

    vector_store.similarity_search_with_threshold.return_value = [
        (
            Document(
                page_content="Refunds are available within 7 days.",
                metadata={"source": "policies/refund_policy.md"},
            ),
            0.90,
        )
    ]

    vector_store.mmr_search_with_threshold.return_value = [
        (
            Document(
                page_content="Refunds are available within 7 days.",
                metadata={"source": "policies/refund_policy.md"},
            ),
            0.90,
        )
    ]

    service = RagService(
        vector_store=vector_store,
        model=Mock(),
        query_rewriter=Mock(),
        config=RagConfig(mmr_enabled=mmr_enabled),
    )

    return service, vector_store


def test_similarity_path_is_used_when_mmr_disabled() -> None:
    service, vector_store = make_service(mmr_enabled=False)

    documents = service.retrieve_candidates(["refund policy"])

    assert len(documents) == 1
    vector_store.similarity_search_with_threshold.assert_called_once()
    vector_store.mmr_search_with_threshold.assert_not_called()


def test_mmr_path_is_used_when_mmr_enabled() -> None:
    service, vector_store = make_service(mmr_enabled=True)

    documents = service.retrieve_candidates(["refund policy"])

    assert len(documents) == 1
    vector_store.mmr_search_with_threshold.assert_called_once()
    vector_store.similarity_search_with_threshold.assert_not_called()


def test_duplicate_queries_are_not_retrieved_twice() -> None:
    service, vector_store = make_service(mmr_enabled=False)

    documents = service.retrieve_candidates(
        ["refund policy", "refund policy", "  refund policy  "]
    )

    assert len(documents) == 1
    vector_store.similarity_search_with_threshold.assert_called_once()
