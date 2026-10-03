# 09 — RAG Architecture

Current pipeline:

```text
Question
  ↓
Contextual Query Rewriter
  ↓
Original + Rewritten retrieval
  ↓
Qdrant candidate retrieval
  ↓
deduplication
  ↓
LLM reranking
  ↓
minimal relevant context
  ↓
grounded answer
  ↓
sources
```

Current RAG configuration:

```text
candidate_top_k = 6
score_threshold = 0.35
max_rerank_documents = 10
max_context_documents = 4
```

Important modules:

```text
backend/app/ai/rag/
├── loaders.py
├── splitters.py
├── embeddings.py
├── vector_store.py
├── query_rewriter.py
├── reranker.py
├── service.py
└── config.py
```

Responsibilities:

- loader → files
- splitter → chunks
- embeddings → vectors
- vector store → candidates
- query rewriter → contextual query
- reranker → relevance filtering/order
- service → orchestration
- final LLM → grounded response
