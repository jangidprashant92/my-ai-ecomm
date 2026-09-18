from app.models.product import Product
from sqlmodel import Session, select


class ProductRepository:
    """Persistence operations for product-related queries."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    def get_product(
        self,
        product_id: str,
    ) -> Product | None:
        """Retrieve a product by its ID."""

        statement = select(Product).where(
            Product.product_id == product_id,
        )

        return self.session.exec(statement).first()
