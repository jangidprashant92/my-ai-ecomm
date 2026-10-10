from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RagConfig:
    candidate_top_k: int = 6
    score_threshold: float = 0.35
    max_rerank_documents: int = 10
    max_context_documents: int = 4

    # MMR
    mmr_enabled: bool = False
    mmr_fetch_k: int = 12
    mmr_lambda_mult: float = 0.75
