from datetime import datetime
from decimal import Decimal

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_payment import OrderPayment
from app.models.product import Product
from sqlmodel import Session, func, select


class AnalyticsRepository:
    """Persistence operations for analytical queries."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    def count_orders(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> int:
        """Count orders within an optional date range."""

        statement = select(func.count()).select_from(Order)

        if start_date is not None:
            statement = statement.where(
                Order.order_purchase_timestamp >= start_date,
            )

        if end_date is not None:
            statement = statement.where(
                Order.order_purchase_timestamp < end_date,
            )

        result = self.session.exec(statement).one()

        return int(result)

    def total_spending(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> Decimal:
        """Calculate total payment value within an optional date range."""

        statement = (
            select(
                func.coalesce(
                    func.sum(OrderPayment.payment_value),
                    0,
                )
            )
            .select_from(OrderPayment)
            .join(
                Order,
                Order.order_id == OrderPayment.order_id,
            )
        )

        if start_date is not None:
            statement = statement.where(
                Order.order_purchase_timestamp >= start_date,
            )

        if end_date is not None:
            statement = statement.where(
                Order.order_purchase_timestamp < end_date,
            )

        result = self.session.exec(statement).one()

        return Decimal(result)

    def top_products(
        self,
        limit: int = 10,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict]:
        """
        Return top products ranked by total item sales value.
        """

        statement = (
            select(
                Product.product_id,
                Product.product_category_name,
                func.count(OrderItem.order_item_id).label(
                    "items_sold",
                ),
                func.sum(OrderItem.price).label(
                    "sales_value",
                ),
            )
            .select_from(OrderItem)
            .join(
                Order,
                Order.order_id == OrderItem.order_id,
            )
            .join(
                Product,
                Product.product_id == OrderItem.product_id,
            )
        )

        if start_date is not None:
            statement = statement.where(
                Order.order_purchase_timestamp >= start_date,
            )

        if end_date is not None:
            statement = statement.where(
                Order.order_purchase_timestamp < end_date,
            )

        statement = (
            statement.group_by(
                Product.product_id,
                Product.product_category_name,
            )
            .order_by(
                func.sum(OrderItem.price).desc(),
            )
            .limit(limit)
        )

        rows = self.session.exec(statement).all()

        return [
            {
                "product_id": row.product_id,
                "category": row.product_category_name,
                "items_sold": int(row.items_sold),
                "sales_value": str(
                    Decimal(row.sales_value or 0),
                ),
            }
            for row in rows
        ]

    def sales_by_category(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict]:
        """Return sales grouped by product category."""

        statement = (
            select(
                Product.product_category_name,
                func.count(OrderItem.order_item_id).label(
                    "items_sold",
                ),
                func.sum(OrderItem.price).label(
                    "sales_value",
                ),
            )
            .select_from(OrderItem)
            .join(
                Order,
                Order.order_id == OrderItem.order_id,
            )
            .join(
                Product,
                Product.product_id == OrderItem.product_id,
            )
        )

        if start_date is not None:
            statement = statement.where(
                Order.order_purchase_timestamp >= start_date,
            )

        if end_date is not None:
            statement = statement.where(
                Order.order_purchase_timestamp < end_date,
            )

        statement = statement.group_by(
            Product.product_category_name,
        ).order_by(
            func.sum(OrderItem.price).desc(),
        )

        rows = self.session.exec(statement).all()

        return [
            {
                "category": row.product_category_name,
                "items_sold": int(row.items_sold),
                "sales_value": str(
                    Decimal(row.sales_value or 0),
                ),
            }
            for row in rows
        ]
