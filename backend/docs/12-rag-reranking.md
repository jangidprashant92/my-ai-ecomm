# 12 — RAG Reranking

Reranking is the second retrieval stage.

## Stage 1

Qdrant produces candidate documents.

```text
candidate_top_k = 6
```

Candidates from original and rewritten queries are merged and deduplicated.

## Stage 2

The LLM reranker receives:

- question
- candidate index
- source
- content

and returns:

```json
{
  "relevant_indices": [0, 2]
}
```

The service maps indices back to candidate documents.

## Why this contract?

An earlier design returned `(index, relevance, score)`. That was unnecessarily fragile.

The current contract asks only for ordered relevant indices.

This simplifies:

```text
question
 ↓
candidates
 ↓
relevant indices
 ↓
final context
```

## Minimal context

The reranker should retain the smallest set of documents sufficient to answer the question.

This reduces:

- duplicate context
- irrelevant policy context
- token cost
- answer-model confusion

Freeze a reranker version before changing it again; evaluate changes against the same benchmark.
