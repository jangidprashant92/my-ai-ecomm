from hashlib import sha256

from app.ai.rag import (
    EmbeddingProvider,
    QdrantKnowledgeStore,
)
from langchain_core.documents import Document

TOP_K = 6
FETCH_K_VALUES = (12, 20)
LAMBDA_MULT = 0.75
SCORE_THRESHOLD = 0.35


SearchResults = list[tuple[Document, float]]


QUERIES = [
    "What is the refund policy for a damaged product?",
    "What evidence is required for a damaged product refund?",
    "What steps does support need to follow for a damaged product refund?",
    "When should a delayed shipment be escalated?",
]


def document_key(document: Document) -> str:
    """Identify a document chunk by its source and content."""
    source = str(document.metadata.get("source", ""))
    digest = sha256(document.page_content.encode("utf-8")).hexdigest()[:10]

    return f"{source} [{digest}]"


def print_results(
    title: str,
    results: SearchResults,
) -> None:
    print(f"\n--- {title} ---")

    if not results:
        print("No documents returned.")
        return

    for rank, (document, score) in enumerate(
        results,
        start=1,
    ):
        preview = " ".join(document.page_content.split())[:100]

        print(f"{rank}. score={score:.4f} | {document_key(document)}")
        print(f"   {preview}")


def result_keys(
    results: SearchResults,
) -> set[str]:
    return {document_key(document) for document, _ in results}


def compare_results(
    title: str,
    left: SearchResults,
    right: SearchResults,
) -> None:
    left_keys = result_keys(left)
    right_keys = result_keys(right)

    shared = left_keys & right_keys
    union = left_keys | right_keys

    jaccard = len(shared) / len(union) if union else 1.0

    print(f"\n{title}")
    print(f"Left candidate count: {len(left_keys)}")
    print(f"Right candidate count: {len(right_keys)}")
    print(f"Shared chunks: {len(shared)}")
    print(f"Jaccard overlap: {jaccard:.3f}")

    only_left = sorted(left_keys - right_keys)
    only_right = sorted(right_keys - left_keys)

    print("Only in left:")
    for item in only_left:
        print(f"  - {item}")

    print("Only in right:")
    for item in only_right:
        print(f"  - {item}")


def main() -> None:
    embedding_provider = EmbeddingProvider()

    vector_store = QdrantKnowledgeStore(
        embeddings=embedding_provider.embeddings,
    )
    vector_store.connect_existing()

    for query in QUERIES:
        print("\n" + "=" * 80)
        print(f"Query: {query}")

        baseline = vector_store.similarity_search_with_threshold(
            query=query,
            k=TOP_K,
            score_threshold=SCORE_THRESHOLD,
        )

        print_results("SIMILARITY BASELINE", baseline)

        mmr_results: dict[int, SearchResults] = {}

        for fetch_k in FETCH_K_VALUES:
            results = vector_store.mmr_search_with_threshold(
                query=query,
                k=TOP_K,
                fetch_k=fetch_k,
                lambda_mult=LAMBDA_MULT,
                score_threshold=SCORE_THRESHOLD,
            )

            mmr_results[fetch_k] = results

            print_results(
                f"MMR fetch_k={fetch_k}",
                results,
            )

            compare_results(
                f"Baseline vs MMR fetch_k={fetch_k}",
                baseline,
                results,
            )

        compare_results(
            "MMR fetch_k=12 vs fetch_k=20",
            mmr_results[12],
            mmr_results[20],
        )


if __name__ == "__main__":
    main()
