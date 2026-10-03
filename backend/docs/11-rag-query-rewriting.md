# 11 — RAG Query Rewriting

Follow-up questions can be poor vector queries.

Example:

```text
What is the refund policy for damaged products?
→ 7 days

How long can I request it?
```

The second query is ambiguous without conversation context.

`backend/app/ai/rag/query_rewriter.py` resolves references such as:

- it
- that
- the rule

and produces a standalone retrieval query.

Example:

```text
How long after delivery can I request a refund for a damaged product?
```

The RAG service retrieves using both rewritten and original queries.

This protects recall if the rewriting model changes wording poorly.

The rewriter is tagged `rag_query_rewrite`; the SSE layer filters this internal output from the user.

Test:

```bash
cd backend
uv run python -m app.scripts.test_rag
uv run python -m evaluation.rag.run
```
