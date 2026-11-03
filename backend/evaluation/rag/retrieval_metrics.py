from __future__ import annotations

from collections.abc import Sequence
from typing import Any


def _get_source(document: dict[str, Any]) -> str:
    source = document.get("source")
    return str(source).strip() if source else ""


def _get_content(document: dict[str, Any]) -> str:
    content = document.get("content")
    return str(content).strip() if content else ""


def calculate_retrieval_metrics(
    documents: Sequence[dict[str, Any]],
) -> dict[str, float | int]:
    """
    Calculate deterministic diversity metrics for retrieved documents.

    Documents should contain:
        source: knowledge-base source path
        content: retrieved chunk content
    """
    total_documents = len(documents)

    if total_documents == 0:
        return {
            "retrieved_count": 0,
            "unique_source_count": 0,
            "source_diversity": 0.0,
            "duplicate_chunk_ratio": 0.0,
        }

    sources = [_get_source(document) for document in documents]

    contents = [_get_content(document) for document in documents]

    unique_sources = {source for source in sources if source}

    unique_contents = {content for content in contents if content}

    # source_counts = Counter(source for source in sources if source)

    source_diversity = len(unique_sources) / total_documents

    duplicate_chunk_ratio = 1 - len(unique_contents) / total_documents

    return {
        "retrieved_count": total_documents,
        "unique_source_count": len(unique_sources),
        "source_diversity": round(source_diversity, 4),
        "duplicate_chunk_ratio": round(
            duplicate_chunk_ratio,
            4,
        ),
    }
