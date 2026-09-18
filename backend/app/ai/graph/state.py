from dataclasses import dataclass

from langgraph.graph import MessagesState


@dataclass(frozen=True, slots=True)
class GraphContext:
    """Request-scoped context available during graph execution."""

    user_id: str
    conversation_id: str


class ChatState(MessagesState):
    """Persistent state for a CommerceOps conversation."""

    intent: str | None
    intent_confidence: float | None
    intent_reason: str | None

    tool_count: int
    last_tool_name: str | None
