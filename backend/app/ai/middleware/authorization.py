from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage
from langgraph.prebuilt.tool_node import ToolCallRequest

logger = logging.getLogger(__name__)


class CommerceAuthorizationMiddleware(AgentMiddleware):
    """Business authorization guardrail for CommerceAgent."""

    READ_ONLY_TOOLS = frozenset(
        {
            "get_order_status",
            "get_order_products",
            "get_product",
        }
    )

    HITL_REQUIRED_TOOLS = frozenset(
        {
            "request_refund",
        }
    )

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[
            [ToolCallRequest],
            Awaitable[Any],
        ],
    ):
        tool_name = request.tool_call["name"]
        tool_call_id = request.tool_call["id"]

        if tool_name in self.READ_ONLY_TOOLS:
            logger.info(
                "Authorized read-only tool: %s",
                tool_name,
            )

            return await handler(request)

        if tool_name in self.HITL_REQUIRED_TOOLS:
            logger.info(
                "Tool requires human approval: %s",
                tool_name,
            )

            return await handler(request)

        logger.warning(
            "Blocked unauthorized tool: %s",
            tool_name,
        )

        return ToolMessage(
            content=(
                f"The operation '{tool_name}' is not authorized "
                "for the CommerceOps agent."
            ),
            tool_call_id=tool_call_id,
        )
