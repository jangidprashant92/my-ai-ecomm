from collections.abc import Callable
from typing import Any

from app.modules.products.repository import ProductRepository
from app.modules.products.service import ProductQueryService
from langchain_core.tools import StructuredTool
from sqlmodel import Session


class ProductTools:
    """LangChain tool adapters for product operations."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
    ) -> None:
        self.session_factory = session_factory

    def get_product(
        self,
        product_id: str,
    ) -> dict[str, Any]:
        """Retrieve product information using a product ID."""

        with self.session_factory() as session:
            repository = ProductRepository(
                session=session,
            )

            service = ProductQueryService(
                repository=repository,
            )

            return service.get_product(
                product_id=product_id,
            )


def create_product_tools(
    session_factory: Callable[[], Session],
) -> list[StructuredTool]:
    """Create LangChain tools for product operations."""

    product_tools = ProductTools(
        session_factory=session_factory,
    )

    return [
        StructuredTool.from_function(
            func=product_tools.get_product,
            name="get_product",
            description=(
                "Get product information using a product ID, "
                "including category, dimensions, weight, "
                "photo count, and other product attributes."
            ),
        ),
    ]
