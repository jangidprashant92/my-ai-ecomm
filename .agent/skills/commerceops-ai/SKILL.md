---
name: commerceops-ai
description: Project-specific guidance for understanding, maintaining, and extending the CommerceOps AI repository, including LangGraph, RAG, Qdrant, retrieval/reranking/MMR, evaluation, MLflow, FastAPI, SQLModel/PostgreSQL, SQLite checkpoints, and React chat UI.
---

# CommerceOps AI — Project Skill

## Mission
Help the developer understand and extend the existing CommerceOps AI codebase without inventing repository details or breaking the frozen RAG evaluation baseline. Prefer small, verifiable changes with exact file paths, tests, commands, and measurable evaluation.

Repository: https://github.com/jangidprashant92/my-ai-ecomm

## Mandatory working rules
1. Inspect the current implementation, imports, settings, dependency lockfile, tests, and callers before proposing edits. Do not assume older summaries match the repository.
2. If repository access is available, inspect the latest branch/files first. If not, ask for relevant files rather than guessing.
3. Preserve existing abstractions and naming conventions. Avoid duplicate services, vector stores, settings systems, or dependencies without justification.
4. For implementation requests, provide exact paths, complete code or precise patches, explanations, commands, expected results, and debugging guidance.
5. Never claim code or tests passed unless they were actually run. Label assumptions and pseudocode.
6. Protect the frozen Reranker v1 baseline. Do not overwrite baseline results or change evaluation expectations as a side effect of a retrieval experiment.
7. Change one major retrieval variable at a time and compare against the same evaluation dataset.
8. Prefer existing LangChain, LangGraph, Qdrant, SQLModel, and MLflow capabilities when appropriate instead of reimplementing them.
9. Never expose or commit secrets from `.env`, tokens, or API keys.
10. Teach the developer why a change is needed, not just what to paste.

## Project overview
CommerceOps AI is an e-commerce conversational assistant with a Python/FastAPI backend and React frontend. It combines LangGraph orchestration, a CommerceAgent with tools, a structured database workflow, and a RAG knowledge assistant.

### Persistence responsibilities
- PostgreSQL: structured business/application data, including imported Olist data.
- SQLite: LangGraph checkpoints via `AsyncSqliteSaver`, configured by `LANGGRAPH_CHECKPOINT_DB`.
- Qdrant: vector index for Markdown knowledge-base chunks.
- MLflow: traces, evaluation runs, and LLM-judge assessments.

Do not describe Olist CSV ingestion as a migration into SQLite. The Olist loader writes to PostgreSQL.

## Repository map
- `backend/app/ai/graph/`: LangGraph state, graph builder, nodes, routing.
- `backend/app/ai/rag/`: RAG loader, splitter, embeddings, vector store, query rewriting, reranker, service, configuration.
- `backend/app/ai/llm/`: LLM abstraction/provider selection.
- `backend/app/core/`: settings, startup/lifespan, database infrastructure.
- `backend/app/modules/messages/`: chat handling, persistence, SSE streaming.
- `backend/app/scripts/`: ingestion and diagnostic scripts.
- `backend/evaluation/rag/`: dataset, predictor, scorers, runner, CSV results.
- `backend/docs/documents/`: business Markdown corpus ingested into Qdrant.
- top-level `docs/`: engineering documentation; do not confuse it with the RAG corpus.
- `frontend/`: Vite/React chat UI, routing, streaming, source display.

Verify exact file names and current symbols in the checked-out repository before editing. This map is a starting point, not a substitute for inspection.

## Existing RAG design
The RAG pipeline includes:
1. conversational query rewriting using chat history;
2. retrieval for original and rewritten queries;
3. candidate merging/deduplication;
4. Qdrant vector retrieval with configured threshold/top-k;
5. LLM document reranking with structured output containing ordered `relevant_indices`;
6. selection of relevant documents for final context;
7. grounded answer generation and source attribution;
8. MLflow retriever tracing and evaluation.

The reranker should select documents that materially answer the specific question, respect scope-changing qualifiers, avoid duplicate evidence, and return an empty selection when no candidate is relevant.

## Evaluation and frozen baseline
The benchmark is under `backend/evaluation/rag/`. It has covered direct questions, follow-ups, cross-policy questions, unanswerable/negative questions, and multi-source questions. The Reranker v1 baseline was frozen in a commit named `Freeze RAG reranker v1 baseline`.

Inspect the actual dataset, baseline CSV, scorer definitions, and latest results before quoting exact row counts or metrics; these may change.

Run evaluation from `backend/`:

```bash
MLFLOW_GENAI_EVAL_MAX_WORKERS=1 \
MLFLOW_GENAI_EVAL_MAX_SCORER_WORKERS=1 \
uv run python -m evaluation.rag.run
```

Single-worker settings were used to avoid async event-loop problems during evaluation.

Useful commands (verify module names before running):

```bash
uv run python -m app.scripts.ingest_documents
uv run python -m app.scripts.test_embeddings
uv run python -m app.scripts.test_retrieval
uv run python -m app.scripts.test_rag
uv run python -m evaluation.rag.run
uv run python -m app.scripts.load_olist_data
```

Alembic commands, from `backend/`:

```bash
uv run alembic current
uv run alembic upgrade head
```

## Planned next task: MMR experiment
The next planned retrieval experiment is to add Maximal Marginal Relevance (MMR) before the existing LLM reranker and compare against the frozen Reranker v1 baseline.

Target pipeline:

```text
query rewrite
    ↓
Qdrant candidate retrieval
    ↓
MMR diversity selection
    ↓
existing LLM reranker
    ↓
final context
    ↓
grounded answer
```

MMR is not a replacement for the LLM reranker:
- MMR balances query relevance against redundancy/diversity among selected documents.
- The LLM reranker judges whether documents directly and semantically answer the specific question.

### MMR implementation rules
1. Inspect the installed LangChain version, concrete Qdrant vector-store class, existing `vector_store.py`, `service.py`, config/settings, dependency lockfile, and tests first.
2. Prefer built-in LangChain/Qdrant MMR if supported by the concrete vector store. Verify the installed API; do not assume all integrations behave identically.
3. Do not hand-code cosine similarity/MMR unless the existing adapter makes built-in MMR unsuitable and the reason is documented.
4. Preserve metadata (`source`, `document_id`, `document_type`, `category`) and retriever trace outputs.
5. Preserve the existing LLM reranker and grounded-answer behavior.
6. Keep MMR disabled by default until integration tests pass.
7. Configure candidate count (`fetch_k`), selected count (`k`), and `lambda_mult` separately. Initial values such as `fetch_k=20–30`, `k=6–8`, and `lambda_mult=0.5–0.7` are experimental, not proven optimal.
8. LangChain MMR may return `Document` objects without similarity scores. Never fabricate scores; preserve a compatible scoring path or represent unavailable scores explicitly.
9. Inspect how original and rewritten query candidates are merged. Avoid applying MMR independently to separate lists and assuming that guarantees diversity across the merged pool.
10. Record experiment settings in MLflow and compare on the unchanged evaluation dataset.
11. Evaluate answerable cases for correctness, source recall, groundedness and sufficiency. Evaluate unanswerable cases for correct abstention and false retrieval. Generic correctness failures on deliberately unanswerable questions are not automatically RAG failures.
12. Save new experiment results separately; do not overwrite the baseline CSV.

### MMR implementation sequence
1. Inspect vector-store API and dependencies.
2. Add configuration and a small MMR adapter/method.
3. Test empty candidates, `k` bounds, metadata preservation, and selection behavior.
4. Integrate MMR before the existing LLM reranker.
5. Verify existing behavior with MMR disabled.
6. Enable MMR for an experiment.
7. Run the unchanged evaluation dataset.
8. Compare baseline vs MMR and keep MMR only if the quality/diversity trade-off improves without unacceptable regressions.

## LangGraph, tools, HITL, and streaming
The root LangGraph routes requests to general assistance, CommerceAgent/tools, structured database workflows, and the knowledge assistant. The graph is compiled with a checkpointer. The conversation ID is used as the graph thread identifier. The messages service streams events through SSE, including message start, tokens, sources, interrupts, completion, and errors.

HITL interrupts are expected control flow. For changes here, inspect middleware, authorization, interrupt/resume payloads, message service, and frontend event consumer together. Do not treat a graph interrupt as a generic application failure.

## Data loading and schema changes
- Olist CSV loading writes to PostgreSQL through `app.scripts.load_olist_data`.
- RAG ingestion loads Markdown, splits documents, embeds chunks, and indexes them in Qdrant.
- Alembic manages relational schema migrations.
- SQLite is for LangGraph checkpoints, not business-data storage.

Before rerunning a loader, verify whether it supports upsert/idempotency.

## Preferred response format for implementation requests
1. Correct the user's English briefly when useful.
2. State the goal and architecture.
3. List exact files to inspect/change/create.
4. Provide complete code or a precise patch for each file.
5. Explain the data flow and design decisions.
6. Give commands from the correct working directory.
7. State expected behavior and tests.
8. If validation fails, ask for the real error/results before continuing.

Prefer one coherent step at a time. Do not dump speculative changes across files before confirming the repository's actual interfaces.
