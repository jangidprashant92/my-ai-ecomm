import re
from collections.abc import Awaitable, Callable
from typing import Any, ClassVar

from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.messages import ToolMessage
from langgraph.prebuilt.tool_node import ToolCallRequest


class CommerceToolPolicyMiddleware(AgentMiddleware):
    """
    Validates CommerceAgent tool calls before execution.

    Responsibilities:
    - Allow only explicitly approved tools.
    - Validate required identifiers.
    - Reject placeholder IDs.
    - Reject malformed IDs.
    """

    ALLOWED_TOOLS = frozenset(
        {
            "get_order_status",
            "get_order_products",
            "get_product",
            "test_write_operation",
            "flaky_test_tool",
        }
    )

    REQUIRED_ID_FIELDS: ClassVar[dict[str, str]] = {
        "get_order_status": "order_id",
        "get_order_products": "order_id",
        "get_product": "product_id",
    }

    PLACEHOLDER_VALUES = frozenset(
        {
            "",
            "order_id",
            "product_id",
            "your_order_id",
            "your_product_id",
            "unknown",
            "none",
            "null",
        }
    )

    ID_PATTERN = re.compile(
        r"^[0-9a-fA-F]{32}$",
    )

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[
            [ToolCallRequest],
            Awaitable[Any],
        ],
    ):
        tool_call = request.tool_call

        tool_name = tool_call["name"]
        tool_args = tool_call.get("args") or {}
        tool_call_id = tool_call["id"]

        # --------------------------------------------------
        # 1. Tool allowlist
        # --------------------------------------------------

        if tool_name not in self.ALLOWED_TOOLS:
            return ToolMessage(
                content=(
                    f"Tool '{tool_name}' is not allowed for the CommerceOps agent."
                ),
                tool_call_id=tool_call_id,
            )

        # --------------------------------------------------
        # 2. Required identifier
        # --------------------------------------------------

        required_field = self.REQUIRED_ID_FIELDS.get(
            tool_name,
        )

        if required_field is None:
            return await handler(request)

        identifier = tool_args.get(
            required_field,
        )

        if not isinstance(identifier, str):
            return ToolMessage(
                content=(f"A valid {required_field} is required for {tool_name}."),
                tool_call_id=tool_call_id,
            )

        identifier = identifier.strip()

        # ----------------------------------------
        # 4. Placeholder values
        # ----------------------------------------

        if identifier.lower() in self.PLACEHOLDER_VALUES:
            return ToolMessage(
                content=(
                    f"A real {required_field} is required. "
                    "Do not use placeholder values."
                ),
                tool_call_id=tool_call_id,
            )

        # ----------------------------------------
        # 5. ID format
        # ----------------------------------------

        if not self.ID_PATTERN.fullmatch(identifier):
            return ToolMessage(
                content=(
                    f"Invalid {required_field}. Expected a 32-character hexadecimal ID."
                ),
                tool_call_id=tool_call_id,
            )

        # ----------------------------------------
        # 6. Approved → execute tool
        # ----------------------------------------

        return await handler(request)
