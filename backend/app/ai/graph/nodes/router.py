from typing import Literal

from app.ai.graph.state import ChatState
from app.ai.schemas.router import Intent

RouteName = Literal[
    "general_assistant",
    "order_assistant",
    "product_assistant",
]


def route_by_intent(
    state: ChatState,
) -> RouteName:
    """Route the graph to the workflow matching the classified intent."""

    intent = state.get("intent")

    if intent == Intent.ORDER.value:
        return "order_assistant"

    if intent == Intent.PRODUCT.value:
        return "product_assistant"

    return "general_assistant"
