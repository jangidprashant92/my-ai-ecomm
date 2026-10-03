# 05 — LangGraph Foundation

State:

```text
backend/app/ai/graph/state.py
```

`ChatState` extends `MessagesState` and also stores intent, tool information, database plan/result, resolved dates and RAG sources.

`GraphContext` contains:

- user ID
- conversation ID

Graph builder:

```text
backend/app/ai/graph/builder.py
```

Flow:

```text
START
 ↓
classify_intent
 ↓
conditional routing
 ├── general_assistant
 ├── commerce_agent
 ├── database_planner
 │    ↓
 │  database_time_resolver
 │    ↓
 │  database_executor
 │    ↓
 │  database_answer
 └── knowledge_assistant
 ↓
END
```

For every node, learn four things:

1. What state does it read?
2. What does it calculate?
3. What state does it return?
4. What edge executes next?
