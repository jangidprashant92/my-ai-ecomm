from collections.abc import Sequence

from app.ai.middleware import CommerceToolPolicyMiddleware
from app.ai.middleware.authorization import CommerceAuthorizationMiddleware
from langchain.agents import create_agent
from langchain.agents.middleware import (
    HumanInTheLoopMiddleware,
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

You can use tools for:

- order status
- products belonging to an order
- product information
- requesting a refund for an order

Rules:

1. Use tools for order-specific or product-specific facts.
2. Never invent an order ID.
3. Never invent a product ID.
4. If an order ID is required but the user has not provided one,
   ask the user for the order ID.
5. If a product ID is required but the user has not provided one,
   ask the user for the product ID.
6. For a refund request, do not invent the amount or reason.
7. Never claim that a refund was executed unless the refund tool
   actually confirms execution.
8. Keep the final answer concise.
"""


class CommerceAgent:
    """Agent responsible for order, product, and refund operations."""

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
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "request_refund": {
                        "allowed_decisions": [
                            "approve",
                            "reject",
                        ],
                        "description": (
                            "A refund request requires human approval before execution."
                        ),
                    },
                },
            ),
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

        self.agent = create_agent(
            model=model,
            tools=list(tools),
            system_prompt=COMMERCE_AGENT_PROMPT,
            middleware=middleware,
            name="commerce_agent",
            # checkpointer=None means:
            # inherit parent graph checkpointer when used
            # as a subgraph.
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
