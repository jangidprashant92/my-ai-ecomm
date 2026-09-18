from app.ai.graph.nodes import create_chat_node
from app.ai.graph.state import ChatState
from app.ai.tools import ALL_TOOLS
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode


def route_after_assistant(
    state: ChatState,
) -> str:

    last_message = state["messages"][-1]

    tool_calls = getattr(
        last_message,
        "tool_calls",
        [],
    )

    print(
        "Tool calls:",
        tool_calls,
    )

    if tool_calls:
        return "tools"

    return END


def build_chat_graph(
    model: BaseChatModel,
    checkpointer: BaseCheckpointSaver,
):

    builder = StateGraph(ChatState)

    builder.add_node(
        "assistant",
        create_chat_node(
            model=model,
            tools=ALL_TOOLS,
        ),
    )

    builder.add_node(
        "tools",
        ToolNode(ALL_TOOLS),
    )

    builder.add_edge(
        START,
        "assistant",
    )

    builder.add_conditional_edges(
        "assistant",
        route_after_assistant,
        {
            "tools": "tools",
            END: END,
        },
    )

    builder.add_edge(
        "tools",
        "assistant",
    )

    return builder.compile(
        checkpointer=checkpointer,
    )
