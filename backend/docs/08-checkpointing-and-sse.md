# 08 — Checkpointing and SSE

## LangGraph checkpointing

`backend/app/core/lifespan.py` creates an `AsyncSqliteSaver`.

Configured by:

```text
LANGGRAPH_CHECKPOINT_DB
```

The default project setting is a SQLite file under `data/`.

This SQLite database is for LangGraph checkpoints, not Olist/application data.

The conversation ID is used as LangGraph `thread_id`.

## SSE

`backend/app/modules/messages/services.py` emits:

- `message_start`
- `token`
- `sources`
- `interrupt`
- `complete`
- `error`

Conceptually:

```text
message_start
  ↓
token
  ↓
token
  ↓
sources
  ↓
complete
```

HITL can produce:

```text
interrupt
  ↓
human review
  ↓
resume
  ↓
token
  ↓
complete
```

Internal query-rewrite streams, tool-call chunks and tool messages are filtered from user-visible output.
