from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RagConfig:
    top_k: int = 5
    score_threshold: float = 0.35
    max_context_documents: int = 4
