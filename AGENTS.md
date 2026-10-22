# CommerceOps AI — Agent Context

Read `.agent/skills/commerceops-ai/SKILL.md` before making changes to this repository.

Rules:
- Inspect current code and dependency versions before editing.
- PostgreSQL stores structured data; SQLite stores LangGraph checkpoints; Qdrant stores RAG vectors; MLflow stores traces/evaluations.
- Keep top-level `docs/` (engineering documentation) separate from `backend/docs/documents/` (RAG corpus).
- The Reranker v1 evaluation baseline is frozen. Do not overwrite it during experiments.
- Planned next task: implement LangChain/Qdrant built-in MMR before the existing LLM reranker, after inspecting the installed vector-store API and current retrieval abstractions.
- Preserve metadata, tracing, abstention, and existing reranking behavior.
- Give exact file paths, complete code, commands, tests, and explain each change.
