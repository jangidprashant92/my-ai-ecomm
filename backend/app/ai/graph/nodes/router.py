from typing import Literal

from app.ai.graph.state import ChatState
from app.ai.schemas.router import Intent

RouteName = Literal[
    "general_assistant",
    "commerce_agent",
    "database_workflow",
    "knowledge_assistant",
]


def route_by_intent(
    state: ChatState,
) -> RouteName:
    """Route the graph to the workflow matching the classified intent."""

    intent = state.get("intent")

    if intent in {
        Intent.ORDER.value,
        Intent.PRODUCT.value,
    }:
        return "commerce_agent"

    if intent == Intent.DATABASE.value:
        return "database_workflow"

    if intent == Intent.KNOWLEDGE.value:
        return "knowledge_assistant"

    return "general_assistant"
