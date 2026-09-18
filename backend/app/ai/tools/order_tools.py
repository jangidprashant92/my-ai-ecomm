from collections.abc import Callable

from app.modules.orders.repository import OrderRepository
from app.modules.orders.service import OrderQueryService
from langchain_core.tools import StructuredTool
from sqlmodel import Session


class OrderTools:
    """LangChain tool adapters for order-related operations."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
    ) -> None:
        self.session_factory = session_factory

    def get_order_status(
        self,
        order_id: str,
    ) -> dict:
        """Retrieve status and delivery information for an order."""

        with self.session_factory() as session:
            repository = OrderRepository(
                session=session,
            )

            service = OrderQueryService(
                repository=repository,
            )

            return service.get_order_status(
                order_id=order_id,
            )

    def get_order_products(
        self,
        order_id: str,
    ) -> dict:
        """Retrieve the products belonging to an order."""

        with self.session_factory() as session:
            repository = OrderRepository(
                session=session,
            )

            service = OrderQueryService(
                repository=repository,
            )

            return service.get_order_products(
                order_id=order_id,
            )


def create_order_tools(
    session_factory: Callable[[], Session],
) -> list[StructuredTool]:
    """Create LangChain tools for order operations."""

    order_tools = OrderTools(
        session_factory=session_factory,
    )

    return [
        StructuredTool.from_function(
            func=order_tools.get_order_status,
            name="get_order_status",
            description=(
                "Get the current status, purchase date, "
                "delivery date, and other status information "
                "for an e-commerce order using its order ID."
            ),
        ),
        StructuredTool.from_function(
            func=order_tools.get_order_products,
            name="get_order_products",
            description=(
                "Get all products belonging to an e-commerce "
                "order using the order ID. Use this when the "
                "user asks for product information based on "
                "an order ID."
            ),
        ),
    ]
