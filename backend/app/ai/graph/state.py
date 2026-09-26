from dataclasses import dataclass
from datetime import date

from langgraph.graph import MessagesState


@dataclass(frozen=True, slots=True)
class GraphContext:
    """Request-scoped context available during graph execution."""

    user_id: str
    conversation_id: str


class ChatState(MessagesState):
    """Persistent state for the CommerceOps conversation."""

    intent: str | None
    intent_confidence: float | None
    intent_reason: str | None

    tool_count: int
    last_tool_name: str | None

    database_plan: dict | None
    database_result: dict | None

    database_time_resolved: bool
    database_start_date: date | None
    database_end_date: date | None

    rag_sources: list[dict] | None
