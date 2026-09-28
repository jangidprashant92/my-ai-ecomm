from collections.abc import Callable

from app.ai.tools.order_tools import create_order_tools
from app.ai.tools.product_tools import create_product_tools
from app.ai.tools.test_tools import test_write_operation
from sqlmodel import Session


def create_all_tools(
    session_factory: Callable[[], Session],
):
    """Create all application LangChain tools."""

    order_tools = create_order_tools(
        session_factory=session_factory,
    )

    product_tools = create_product_tools(
        session_factory=session_factory,
    )

    return [
        *order_tools,
        *product_tools,
        test_write_operation,
    ]


__all__ = [
    "create_all_tools",
    "create_order_tools",
    "create_product_tools",
    "test_write_operation",
]
