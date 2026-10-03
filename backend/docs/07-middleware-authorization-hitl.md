# 07 — Middleware, Authorization and HITL

Middleware protects model/tool execution.

Important responsibilities:

- tool limits/policy
- authorization
- retries/error handling
- Human-in-the-Loop

## HITL flow

```text
Agent
 ↓
middleware
 ↓
approval required
 ↓
GraphInterrupt
 ↓
SSE interrupt event
 ↓
human review
 ↓
Command(resume=...)
 ↓
graph continues
```

`GraphInterrupt` is expected control flow for HITL.

`backend/app/observability/mlflow_tracer.py` prevents expected `GraphInterrupt` events from being recorded as ordinary chain failures.

Study:

1. middleware
2. authorization
3. interrupt payload
4. `MessagesService.send_message()`
5. `MessagesService.resume_human_review()`
6. frontend review
7. MLflow tracing
