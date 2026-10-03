from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RagConfig:
    candidate_top_k: int = 6
    score_threshold: float = 0.35
    max_rerank_documents: int = 10
    max_context_documents: int = 4
