# 16 — Frontend Chat

The frontend is a Vite React application using React, React Router, TanStack Query, Assistant UI, Tailwind/shadcn-related packages and Zustand.

## Intended conversation flow

```text
/chat
 ↓
first message
 ↓
conversation created
 ↓
/chat/<conversation_id>
 ↓
messages
 ↓
new message
```

## Backend contract

The message service persists:

1. user message
2. assistant placeholder
3. final assistant message

It streams SSE events.

Important event types:

- message_start
- token
- sources
- interrupt
- complete
- error

## RAG source UI

Sources are emitted independently from answer tokens.

This lets the frontend render:

```text
answer
+
sources
```

as separate UI concerns.

## Debugging

Backend:

```text
backend/app/modules/messages/services.py
```

Frontend: find the SSE/event consumer and verify every `ChatEventType` is handled.

If a token or source is missing, inspect the backend event first.
