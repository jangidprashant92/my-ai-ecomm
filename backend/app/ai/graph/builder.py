from collections.abc import Sequence

from app.ai.graph.nodes import (
    create_assistant_node,
    create_intent_classifier_node,
    route_by_intent,
)
from app.ai.graph.state import ChatState, GraphContext
from app.ai.prompts.chat import (
    GENERAL_ASSISTANT_PROMPT,
    ORDER_ASSISTANT_PROMPT,
    PRODUCT_ASSISTANT_PROMPT,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition


def build_chat_graph(
    model: BaseChatModel,
    checkpointer: BaseCheckpointSaver,
    order_tools: Sequence[BaseTool],
    product_tools: Sequence[BaseTool],
):
    """Build and compile the CommerceOps root graph."""

    builder = StateGraph(
        ChatState,
        context_schema=GraphContext,
    )

    # --------------------------------------------------
    # CLASSIFIER
    # --------------------------------------------------

    builder.add_node(
        "classify_intent",
        create_intent_classifier_node(
            model=model,
        ),
    )

    # --------------------------------------------------
    # GENERAL ASSISTANT
    # --------------------------------------------------

    builder.add_node(
        "general_assistant",
        create_assistant_node(
            model=model,
            tools=None,
            system_prompt=GENERAL_ASSISTANT_PROMPT,
        ),
    )

    # --------------------------------------------------
    # ORDER ASSISTANT
    # --------------------------------------------------

    builder.add_node(
        "order_assistant",
        create_assistant_node(
            model=model,
            tools=order_tools,
            system_prompt=ORDER_ASSISTANT_PROMPT,
        ),
    )

    # --------------------------------------------------
    # PRODUCT ASSISTANT
    # --------------------------------------------------

    builder.add_node(
        "product_assistant",
        create_assistant_node(
            model=model,
            tools=product_tools,
            system_prompt=PRODUCT_ASSISTANT_PROMPT,
        ),
    )

    # --------------------------------------------------
    # TOOL NODES
    # --------------------------------------------------

    builder.add_node(
        "order_tools",
        ToolNode(
            list(order_tools),
        ),
    )

    builder.add_node(
        "product_tools",
        ToolNode(
            list(product_tools),
        ),
    )

    # --------------------------------------------------
    # START
    # --------------------------------------------------

    builder.add_edge(
        START,
        "classify_intent",
    )

    # --------------------------------------------------
    # INTENT ROUTING
    # --------------------------------------------------

    builder.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "general_assistant": "general_assistant",
            "order_assistant": "order_assistant",
            "product_assistant": "product_assistant",
        },
    )

    # --------------------------------------------------
    # GENERAL
    # --------------------------------------------------

    builder.add_edge(
        "general_assistant",
        END,
    )

    # --------------------------------------------------
    # ORDER TOOL LOOP
    # --------------------------------------------------

    builder.add_conditional_edges(
        "order_assistant",
        tools_condition,
        {
            "tools": "order_tools",
            "__end__": END,
        },
    )

    builder.add_edge(
        "order_tools",
        "order_assistant",
    )

    # --------------------------------------------------
    # PRODUCT TOOL LOOP
    # --------------------------------------------------

    builder.add_conditional_edges(
        "product_assistant",
        tools_condition,
        {
            "tools": "product_tools",
            "__end__": END,
        },
    )

    builder.add_edge(
        "product_tools",
        "product_assistant",
    )

    return builder.compile(
        checkpointer=checkpointer,
    )
