from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


@dataclass
class MMRDocument:
    """
    Internal representation used by the MMR selector.
    """

    document: object
    score: float
    embedding: Sequence[float]


def cosine_similarity(
    a: Sequence[float],
    b: Sequence[float],
) -> float:
    """
    Calculate cosine similarity between two vectors.
    """

    a_vector = np.asarray(a, dtype=float)
    b_vector = np.asarray(b, dtype=float)

    a_norm = np.linalg.norm(a_vector)
    b_norm = np.linalg.norm(b_vector)

    if a_norm == 0 or b_norm == 0:
        return 0.0

    return float(np.dot(a_vector, b_vector) / (a_norm * b_norm))


def maximal_marginal_relevance(
    candidates: list[MMRDocument],
    *,
    top_k: int,
    lambda_mult: float = 0.7,
) -> list[MMRDocument]:
    """
    Select documents using Maximal Marginal Relevance.

    MMR balances:

        relevance to query
        +
        diversity between selected documents

    The candidate score is assumed to represent
    similarity between the query and the candidate.
    """

    if not candidates:
        return []

    if top_k <= 0:
        return []

    if not 0.0 <= lambda_mult <= 1.0:
        raise ValueError("lambda_mult must be between 0 and 1")

    top_k = min(top_k, len(candidates))

    selected: list[MMRDocument] = []
    remaining = list(candidates)

    while remaining and len(selected) < top_k:
        if not selected:
            best = max(
                remaining,
                key=lambda item: item.score,
            )

            selected.append(best)
            remaining.remove(best)
            continue

        best_candidate = None
        best_mmr_score = float("-inf")

        for candidate in remaining:
            relevance = candidate.score

            max_similarity_to_selected = max(
                cosine_similarity(
                    candidate.embedding,
                    selected_document.embedding,
                )
                for selected_document in selected
            )

            mmr_score = (
                lambda_mult * relevance
                - (1.0 - lambda_mult) * max_similarity_to_selected
            )

            if mmr_score > best_mmr_score:
                best_mmr_score = mmr_score
                best_candidate = candidate

        if best_candidate is None:
            break

        selected.append(best_candidate)
        remaining.remove(best_candidate)

    return selected
