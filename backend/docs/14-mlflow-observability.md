# 14 — MLflow Observability

`backend/main.py` configures MLflow tracing for the application.

RAG evaluation uses a separate evaluation experiment.

## RAG retrieval trace

The RAG retrieval operation is traced as a retriever span.

Useful outputs include:

- source
- document ID
- document type
- category
- vector score
- rerank rank
- final retrieved context

## HITL

`HITLAwareMlflowTracer` treats `GraphInterrupt` as expected control flow.

## What to inspect

For an evaluated RAG request:

```text
evaluation
  ├── retrieval span
  │    ├── candidates
  │    └── reranker
  └── answer LLM
```

Inspect:

- retrieved documents
- vector score
- rerank rank
- context
- answer
- latency
- token usage
- judge assessments

The local project expects MLflow at:

```text
http://127.0.0.1:8080
```
