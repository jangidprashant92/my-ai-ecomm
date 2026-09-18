from collections.abc import Sequence
from typing import Any

from app.ai.graph.state import ChatState
from langchain.messages import SystemMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool


class AssistantNode:
    """Executes an LLM with an optional set of tools."""

    def __init__(
        self,
        model: BaseChatModel,
        tools: Sequence[BaseTool] | None,
        system_prompt: str,
    ) -> None:
        self.system_prompt = system_prompt

        if tools:
            self.model = model.bind_tools(
                list(tools),
            )
        else:
            self.model = model

    async def run(
        self,
        state: ChatState,
    ) -> dict[str, Any]:
        messages = [
            SystemMessage(
                content=self.system_prompt,
            ),
            *state["messages"],
        ]

        response = await self.model.ainvoke(
            messages,
        )

        tool_calls = getattr(
            response,
            "tool_calls",
            [],
        )

        return {
            "messages": [response],
            "tool_count": len(tool_calls),
            "last_tool_name": (tool_calls[0]["name"] if tool_calls else None),
        }


def create_assistant_node(
    model: BaseChatModel,
    tools: Sequence[BaseTool] | None,
    system_prompt: str,
):
    """
    Create a LangGraph-compatible node.

    The class owns the dependency and behavior while this
    function provides the callable interface expected by LangGraph.
    """

    node = AssistantNode(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
    )

    async def assistant_node(
        state: ChatState,
    ) -> dict[str, Any]:
        return await node.run(state)

    return assistant_node
