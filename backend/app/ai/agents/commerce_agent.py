from collections.abc import Sequence
from typing import Any

from app.ai.graph.state import ChatState
from app.ai.middleware import CommerceToolPolicyMiddleware
from app.ai.middleware.authorization import CommerceAuthorizationMiddleware
from langchain.agents import create_agent
from langchain.agents.middleware import (
    ModelCallLimitMiddleware,
    ToolCallLimitMiddleware,
    ToolErrorMiddleware,
    ToolRetryMiddleware,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.prebuilt.tool_node import ToolCallRequest
from sqlalchemy.exc import OperationalError

COMMERCE_AGENT_PROMPT = """
You are the CommerceOps order and product assistant.

You can use tools to retrieve:
- order status
- products belonging to an order
- product information

Temporary testing rule:
- When the user asks to "run the test write operation",
  call the `test_write_operation` tool.

Rules:

1. Use tools for order-specific or product-specific facts.
2. Never invent an order ID.
3. Never invent a product ID.
4. If an order ID is required but the user has not provided one,
   ask the user for the order ID.
5. If a product ID is required but the user has not provided one,
   ask the user for the product ID.
6. Do not claim that an action was performed unless a tool confirms it.
7. Keep the final answer concise.
"""


class CommerceAgent:
    """Agent responsible for order and product tool interactions."""

    def __init__(
        self,
        model: BaseChatModel,
        tools: Sequence[BaseTool],
    ) -> None:

        middleware = [
            ModelCallLimitMiddleware(
                run_limit=5,
                exit_behavior="end",
            ),
            ToolCallLimitMiddleware(
                run_limit=5,
                exit_behavior="end",
            ),
            CommerceToolPolicyMiddleware(),
            CommerceAuthorizationMiddleware(),
            ToolErrorMiddleware(
                aon_error=self._handle_tool_error,
            ),
            ToolRetryMiddleware(
                max_retries=2,
                on_failure="error",
                retry_on=(
                    ConnectionError,
                    TimeoutError,
                    OperationalError,
                ),
                initial_delay=0.1,
                backoff_factor=1.0,
                max_delay=1.0,
                jitter=False,
            ),
        ]

        agent_tools = [
            *tools,
        ]

        self.agent = create_agent(
            model=model,
            tools=agent_tools,
            system_prompt=COMMERCE_AGENT_PROMPT,
            middleware=middleware,
            name="commerce_tools_agent",
        )

    @staticmethod
    async def _handle_tool_error(
        exc: Exception,
        request: ToolCallRequest,
    ) -> str | None:
        tool_name = request.tool_call["name"]

        print(
            "[ToolErrorMiddleware]",
            tool_name,
            type(exc).__name__,
        )

        if isinstance(exc, ValueError):
            return (
                f"The tool '{tool_name}' rejected the request. "
                "Please check the input and try again."
            )

        return (
            f"The tool '{tool_name}' could not complete the request. Please try again."
        )

    async def run(
        self,
        state: ChatState,
    ) -> dict[str, Any]:

        result = await self.agent.ainvoke(
            {
                "messages": state["messages"],
            }  # type: ignore[arg-type]
        )

        messages = result["messages"]

        if not messages:
            raise RuntimeError("Commerce agent returned no messages.")

        return {
            "messages": [
                messages[-1],
            ],
        }


def create_commerce_agent_node(
    model: BaseChatModel,
    tools: Sequence[BaseTool],
):
    agent = CommerceAgent(
        model=model,
        tools=tools,
    )

    async def commerce_agent_node(
        state: ChatState,
    ) -> dict[str, Any]:

        return await agent.run(state)

    return commerce_agent_node
