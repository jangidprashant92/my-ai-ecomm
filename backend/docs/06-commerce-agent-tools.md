# 06 — Commerce Agent and Tools

The CommerceAgent is created during application startup.

Tools are created through:

```python
create_all_tools(session_factory=create_session)
```

The agent decides:

- whether to use a tool,
- which tool,
- arguments,
- how to interpret the result.

Tools should contain deterministic business logic.

## Database workflow vs agent

Database workflow:

```text
planner → time resolver → executor → answer
```

Commerce agent:

```text
request → agent → tool → result → agent response
```

Use the first for predictable structured analytics and the second for flexible action-oriented tasks.

For every tool document:

- input schema
- authorization
- queries
- side effects
- output
- failures
- read-only vs mutating
