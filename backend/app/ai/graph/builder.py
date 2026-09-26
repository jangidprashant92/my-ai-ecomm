from collections.abc import Callable, Sequence

from app.ai.graph.nodes import (
    create_assistant_node,
    create_database_answer_node,
    create_database_executor_node,
    create_database_planner_node,
    create_database_time_resolver_node,
    create_intent_classifier_node,
    route_by_intent,
)
from app.ai.graph.nodes.rag_assistant_node import create_rag_node
from app.ai.graph.state import ChatState, GraphContext
from app.ai.prompts.chat import (
    GENERAL_ASSISTANT_PROMPT,
    ORDER_ASSISTANT_PROMPT,
    PRODUCT_ASSISTANT_PROMPT,
)
from app.ai.rag.service import RagService
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from sqlmodel import Session


def build_chat_graph(
    model: BaseChatModel,
    checkpointer: BaseCheckpointSaver,
    order_tools: Sequence[BaseTool],
    product_tools: Sequence[BaseTool],
    session_factory: Callable[[], Session],
    rag_service: RagService,
):
    """Build and compile the CommerceOps root graph."""

    builder = StateGraph(
        ChatState,
        context_schema=GraphContext,
    )

    # ==================================================
    # CLASSIFIER
    # ==================================================

    builder.add_node(
        "classify_intent",
        create_intent_classifier_node(
            model=model,
        ),
    )

    # ==================================================
    # GENERAL ASSISTANT
    # ==================================================

    builder.add_node(
        "general_assistant",
        create_assistant_node(
            model=model,
            tools=None,
            system_prompt=GENERAL_ASSISTANT_PROMPT,
        ),
    )

    # ==================================================
    # ORDER ASSISTANT
    # ==================================================

    builder.add_node(
        "order_assistant",
        create_assistant_node(
            model=model,
            tools=order_tools,
            system_prompt=ORDER_ASSISTANT_PROMPT,
        ),
    )

    # ==================================================
    # PRODUCT ASSISTANT
    # ==================================================

    builder.add_node(
        "product_assistant",
        create_assistant_node(
            model=model,
            tools=product_tools,
            system_prompt=PRODUCT_ASSISTANT_PROMPT,
        ),
    )

    # ==================================================
    # DATABASE WORKFLOW
    # ==================================================

    builder.add_node(
        "database_planner",
        create_database_planner_node(
            model=model,
        ),
    )

    builder.add_node(
        "database_time_resolver",
        create_database_time_resolver_node(),
    )

    builder.add_node(
        "database_executor",
        create_database_executor_node(
            session_factory=session_factory,
        ),
    )

    builder.add_node(
        "database_answer",
        create_database_answer_node(
            model=model,
        ),
    )

    # ==================================================
    # Rag WORKFLOW
    # ==================================================

    builder.add_node(
        "knowledge_assistant",
        create_rag_node(
            rag_service=rag_service,
        ),
    )

    # ==================================================
    # TOOL NODES
    # ==================================================

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

    # ==================================================
    # START
    # ==================================================

    builder.add_edge(
        START,
        "classify_intent",
    )

    # ==================================================
    # INTENT ROUTING
    # ==================================================

    builder.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "general_assistant": "general_assistant",
            "order_assistant": "order_assistant",
            "product_assistant": "product_assistant",
            "database_workflow": "database_planner",
            "knowledge_assistant": "knowledge_assistant",
        },
    )

    # ==================================================
    # GENERAL
    # ==================================================

    builder.add_edge(
        "general_assistant",
        END,
    )

    # ==================================================
    # DATABASE
    #
    # planner
    #    ↓
    # temporal resolver
    #    ↓
    # conditional
    #    ├── clarification
    #    └── executor
    # ==================================================

    builder.add_edge(
        "database_planner",
        "database_time_resolver",
    )

    builder.add_edge(
        "database_time_resolver",
        "database_executor",
    )

    builder.add_edge(
        "database_executor",
        "database_answer",
    )

    builder.add_edge(
        "database_answer",
        END,
    )

    builder.add_edge(
        "knowledge_assistant",
        END,
    )

    # ==================================================
    # ORDER TOOL LOOP
    # ==================================================

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

    # ==================================================
    # PRODUCT TOOL LOOP
    # ==================================================

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
