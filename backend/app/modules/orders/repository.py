from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from sqlmodel import Session, select


class OrderRepository:
    """Persistence operations for order-related queries."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    def get_order(
        self,
        order_id: str,
    ) -> Order | None:
        return self.session.exec(
            select(Order).where(
                Order.order_id == order_id,
            )
        ).first()

    def get_order_products(
        self,
        order_id: str,
    ) -> list[tuple[OrderItem, Product]]:
        statement = (
            select(OrderItem, Product)
            .join(
                Product,
                Product.product_id == OrderItem.product_id,  # type: ignore
            )
            .where(
                OrderItem.order_id == order_id,
            )
        )

        return list(self.session.exec(statement).all())
