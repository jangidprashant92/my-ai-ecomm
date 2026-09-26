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

    @staticmethod
    def _validate_product_id(
        product_id: str,
    ) -> str:
        value = product_id.strip()

        if not value:
            raise ValueError("A valid product ID is required.")

        invalid_values = {
            "product_id",
            "your_product_id",
            "unknown",
            "none",
            "null",
        }

        if value.lower() in invalid_values:
            raise ValueError("A real product ID is required.")

        return value

    def get_product(
        self,
        product_id: str,
    ) -> dict[str, Any]:
        product_id = self._validate_product_id(
            product_id,
        )

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
