# 17 — Current Status and Learning Roadmap

**Last reviewed:** 2026-10-10  
**Repository:** jangidprashant92/my-ai-ecomm  
**Reviewed branch:** main  
**Reviewed commit:** 4c362b1 — Add MMR retrieval to RAG

## Status legend

- ✅ Implemented in the repository.
- 🟡 Partially implemented, not integrated end to end, or awaiting validation.
- ⬜ Not implemented yet.
- A check mark means code exists; it does not automatically mean production readiness or successful automated testing.

## Executive summary

The agent foundation and core RAG pipeline are implemented. The latest commit adds MMR retrieval, but an MMR-versus-similarity evaluation has not yet been established. Reranking and evaluation code exist; the benchmark and retrieval ordering need attention before MMR can be considered validated.

The memory package is currently a prototype rather than an integrated conversation-memory feature. MCP, hybrid retrieval, agentic RAG, and production hardening are still future work.

## PHASE 1 — AGENT FOUNDATION

- ✅ LangGraph foundation and root graph orchestration — **backend/app/ai/graph/builder.py**
- ✅ Conditional intent routing — **backend/app/ai/graph/nodes/classifier.py**, **backend/app/ai/graph/nodes/router.py**
- ✅ Structured output for intent classification — classifier and router schemas
- ✅ Commerce agent using create_agent — **backend/app/ai/agents/commerce_agent.py**
- ✅ Order, product, and refund tools — **backend/app/ai/tools/**
- ✅ Commerce agent integrated as a subgraph/node in the root graph
- ✅ Database workflow and temporal resolution — **backend/app/ai/graph/nodes/database*.py**
- ✅ Middleware and tool policy — **backend/app/ai/middleware/**
- ✅ Authorization allowlist and human-in-the-loop refund approval
- ✅ LangGraph checkpointing with SQLite; the conversation ID is used as the graph thread ID
- ✅ SSE streaming and message persistence — **backend/app/modules/messages/services.py**
- ✅ MLflow tracing and HITL-aware tracing
- 🟡 Production identity/authorization hardening remains: **MessagesService.send_message()** currently uses a hard-coded user UUID. Replace this with authenticated user identity and enforce conversation ownership before production use.

## PHASE 2 — RAG FOUNDATION

- ✅ Markdown knowledge-base loader — **backend/app/ai/rag/loaders.py**
- ✅ Document splitting — **backend/app/ai/rag/splitters.py**
- ✅ Embeddings — **backend/app/ai/rag/embeddings.py**
- ✅ Qdrant ingestion and retrieval — **backend/app/scripts/ingest_documents.py**, **backend/app/ai/rag/vector_store.py**
- ✅ Standalone RAG answer service — **backend/app/ai/rag/service.py**
- ✅ RAG integrated into the root LangGraph through the **knowledge_assistant** node
- ✅ Grounded answer prompt and abstention behavior
- ✅ Conversational query rewriting and retrieval over both rewritten and original queries
- ✅ Retrieved source metadata returned by the graph and source UI component present in the frontend
- ✅ LLM reranker implementation — **backend/app/ai/rag/reranker.py**
- 🟡 Reranker evaluation exists, but benchmark expectations and judge disagreements should be reviewed before freezing the benchmark.
- 🟡 MMR method is integrated through Qdrant's built-in MMR API — **backend/app/ai/rag/vector_store.py**; the feature flag is wired through **backend/app/core/config.py** and **backend/app/ai/rag/service.py**.
- 🟡 MMR is not yet validated by a controlled A/B run. **backend/app/ai/rag/service.py** merges results from rewritten and original queries and globally sorts them by scores produced for different queries, which can undo MMR's selected order. Fix candidate merging before drawing conclusions from the MMR experiment.
- 🟡 A custom selector also exists in **backend/app/ai/rag/mmr.py**, but the application retrieval path currently uses Qdrant's built-in MMR. Avoid maintaining two implementations unless the custom selector is intentionally adopted.
- ✅ Retrieval/RAG evaluation runner, dataset, and scorers exist under **backend/evaluation/rag/**.
- 🟡 The uploaded 12-case CSV is a pre-MMR baseline, not proof of MMR effectiveness. It records custom RAG quality PASS for 12/12 cases, source recall 1.00, source precision 1.00, and abstention PASS for both negative cases. Retrieval relevance precision is 0.95 across 10 scored cases, with a 0.5 result on the cross-policy question. Generic groundedness, sufficiency, and correctness each mark the two intentionally unanswerable cases as no; the custom abstention scorer marks both PASS.
- ⬜ Hybrid retrieval (for example, lexical plus vector retrieval)
- ⬜ Agentic RAG with an explicit retrieve/evaluate/refine loop
- ⬜ A dedicated search_knowledge tool
- ⬜ A dedicated tool-enabled Knowledge Agent. The current knowledge_assistant is a RAG graph node, not yet a separate tool-using knowledge agent.

## PHASE 3 — MEMORY

- 🟡 Short-term conversation state exists through LangGraph checkpoints and persisted messages, but it is not yet managed through the memory manager.
- 🟡 Rolling summary model and service prototype exist — **backend/app/models/memory.py**, **backend/app/modules/memory/services.py**. Summary generation is not connected to the chat execution flow.
- 🟡 User profile memory model and read method exist. Fact extraction currently prompts the LLM but does not parse and persist extracted facts or run as part of chat.
- ⬜ Semantic/episodic memory: **retrieve_relevant_context()** is currently a placeholder returning an empty list.
- 🟡 Memory retrieval is only partially scaffolded; summary/profile reads are not injected into the RAG or agent prompt.
- ⬜ Memory policies: ownership, consent, retention/deletion, conflict resolution, and rules for what may be saved/recalled.
- 🟡 Database migration and integration are still required for the summary and user-memory tables. Verify the generated Alembic migration against the actual database before using these models.

## PHASE 4 — ADVANCED AGENTS

- 🟡 Specialized workflows partially exist: CommerceAgent, database workflow, general assistant, and knowledge assistant. They are currently selected through intent routing.
- 🟡 Multi-step planning is implemented for the database workflow only (planning, temporal resolution, execution, and answer generation); a general-purpose planning/replanning loop is not implemented.
- 🟡 Basic tool-level failure handling and retries exist in the CommerceAgent middleware.
- ⬜ Explicit agent-to-agent handoffs/workflows
- ⬜ Dynamic tool discovery/selection beyond the tools already supplied to an agent
- ⬜ General failure recovery and replanning across graph branches
- ⬜ Deep Agents implementation

## PHASE 5 — MCP

- ⬜ MCP server
- ⬜ MCP tools
- ⬜ MCP resources
- ⬜ External integrations through MCP
- ⬜ Dynamic MCP tool discovery

## PHASE 6 — EVALUATION AND PRODUCTION

- ✅ Basic MLflow tracing and application-level trace integration
- ✅ Retrieval/RAG evaluation framework exists
- 🟡 RAG evaluation benchmark needs a controlled baseline, clearly named MMR and similarity runs, and consistent expected-source/expected-fact definitions.
- ⬜ Agent behavior/tool-use evaluation
- 🟡 Prompts are organized into source files, but prompt versioning and experiment-to-prompt linkage are not implemented.
- 🟡 MLflow traces may expose usage/latency metadata, but there is no project-level token/cost report or defined latency SLO/dashboard yet.
- 🟡 Some guardrails exist (tool allowlist, authorization middleware, HITL, grounded RAG instructions, and abstention). General input/output guardrails are not complete.
- ⬜ Rate limiting and per-user quotas
- 🟡 Exception handling and tool retry/error middleware exist; production hardening, timeouts, observability alerts, and integration tests remain.
- 🟡 Automated test coverage is limited: the repository primarily contains runnable probe scripts under **backend/app/scripts/**; add repeatable tests with assertions for critical behavior.

## NEXT STEPS — FOLLOW THIS ORDER

1. **Fix and validate MMR before starting hybrid RAG.** In **backend/app/ai/rag/service.py**, stop globally sorting merged candidates by similarity scores from different queries. Preserve a deterministic candidate order after deduplication, and keep the existing LLM reranker as the final relevance filter.
2. **Run a controlled retrieval comparison.** Use the same 12-case dataset, Qdrant collection, embedding model, reranker, and score threshold. Run once with **RAG_USE_MMR=false**, save the CSV, then run with **RAG_USE_MMR=true** and save the second CSV. Record both runs separately in MLflow.
3. **Review metrics and freeze the retrieval baseline.** Compare source recall, source precision, retrieval relevance, custom RAG quality, and negative-case abstention. Do not judge MMR by variety alone.
4. **Add automated tests.** Cover the MMR flag, empty retrieval, duplicate documents, candidate order, source metadata, and negative/abstention cases.
5. **Proceed to hybrid retrieval only after the baseline is stable.** Add it as a separate experiment, not in the same change as MMR.
6. **Then implement agentic RAG, search_knowledge, and a dedicated Knowledge Agent.**
7. **After the retrieval path is stable, integrate memory end to end:** create/verify migrations, connect summary memory to chat, implement persistent user-fact extraction, then semantic memory and memory policies.
8. **Continue with agent evaluation, MCP, and production hardening.** Address the hard-coded user identity before treating the application as production-ready.

## Experiment rule

Change one retrieval or memory behavior per experiment. Keep the dataset, configuration, MLflow run, and results CSV identifiable so that a measured difference can be attributed to the change.
