# 02 — System Architecture

The application has four major paths.

## Structured data

PostgreSQL stores customers, orders, products, sellers, order items, payments, reviews, conversations and messages.

## Unstructured knowledge

Markdown files under `backend/docs/documents/` are loaded, split, embedded and indexed in Qdrant.

```text
question
  ↓
query rewrite
  ↓
Qdrant retrieval
  ↓
LLM reranking
  ↓
minimal context
  ↓
grounded answer
```

## Agent/tool path

CommerceAgent selects tools for action-oriented requests.

## LangGraph

```text
START
  ↓
classify_intent
  ├── general_assistant
  ├── commerce_agent
  ├── database_workflow
  └── knowledge_assistant
```

## Chat request

`MessagesService`:

1. gets/creates conversation,
2. persists user message,
3. creates assistant placeholder,
4. runs LangGraph,
5. streams SSE tokens,
6. emits RAG sources,
7. handles HITL interrupts,
8. persists the final answer.

Main files:

- `backend/main.py`
- `backend/app/core/lifespan.py`
- `backend/app/ai/graph/builder.py`
- `backend/app/modules/messages/services.py`
- `backend/app/ai/rag/service.py`
